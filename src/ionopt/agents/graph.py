"""The agent loop as a LangGraph state machine (plan_phase2 section 5).

    load_context -> planner -> validator
    validator --invalid (<= validator_retries)--> planner
    validator --needs_edit--> editor -> author_approval --approved--> optimize
                                        author_approval --rejected--> planner
    validator --ok--> optimize -> critic -> update_state -> stop_check --continue--> planner
    validator --escalate--> escalate (pause for the author) --> planner
    validator --stop--> finalize ; stop_check --stop--> finalize -> END

Code, not an LLM, picks every transition, counts the solve budget and checks the stop conditions.
The state is checkpointed to SQLite after every node (results/runs/<run_id>/checkpoints.sqlite):
a crashed or paused run continues with resume_loop. The optimizer study of a round is resumable on
its own (Optuna storage), and its solves are counted from the study, so a resumed round is not
double-counted. A1 skips the critic; A2 has no editor (the validator rejects edit requests).
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

from ..config import ConfigError
from ..optimize import optimize
from ..utils import now_iso
from .critic import review
from .llm import LLMError
from .planner import propose
from .roles import LoopContext
from .schemas import EditResult
from .state import BestSoFar, Budget, LoopState, Method, Pending, RoundRecord, Variant
from .summaries import load_metrics, metrics_summary
from .validator import bounds_tuple, to_configuration_def, validate
from ..variants import approve_variant

ASSUMPTIONS = [
    "2D axisymmetric model trusted for search; 3D used only to validate finalists once compute allows "
    "(plan_phase2 section 2; small known 2D/3D inconsistency, KNOWN_ISSUES #23)",
    "3D promotion at finalize skipped: no 3D compute on this machine (author 2026-11-14)",
]


# --------------------------------------------------------------------------- run setup


def _hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


def new_state(ctx: LoopContext, run_id: str, method: Method = "agent", case_id: str = "nominal",
              solve_budget: int | None = None, round_cap: int | None = None, goal: str | None = None) -> LoopState:
    cfg, acfg = ctx.cfg, ctx.acfg
    assumptions = list(ASSUMPTIONS)
    goal = (goal or "").strip() or None
    if goal:
        assumptions.append(f"author goal given to the planner (steered run, not a blind evaluation): {goal}")
    r = cfg.spec.requirements
    if r.impact_threshold_eV_per_charge is None and r.impact_threshold_mps is None:
        raise ConfigError("spec.requirements.impact_threshold_* is TBD: the checker cannot score runs. Set it in "
                          "config/spec.yaml or run with --overrides config/dev_overrides.yaml (placeholder)")
    if cfg.overrides:
        assumptions.append("config overrides (placeholders, not author decisions): " + ", ".join(cfg.overrides))
    return LoopState(
        run_id=run_id, method=method, case_id=case_id, seed=cfg.optimizer.seed,
        models={k: v.model for k, v in acfg.roles.items()},
        budget=Budget(solves_total=solve_budget or acfg.loop.solve_budget, round_cap=round_cap or acfg.loop.round_cap),
        spec_hash=cfg.spec_hash(), constraints_hash=_hash(cfg.resolved()["constraints"]), agents_hash=acfg.hash(),
        assumptions=assumptions, goal=goal, backend=cfg.backend.backend)


# --------------------------------------------------------------------------- nodes


def build_graph(ctx: LoopContext, checkpointer=None):
    cfg, acfg = ctx.cfg, ctx.acfg
    lp = acfg.loop

    def load_context(s: LoopState) -> dict:
        ctx.run_dir(s.run_id).mkdir(parents=True, exist_ok=True)
        with ctx.db() as rl:
            rl.start_agent_run(s.run_id, s.method, s.case_id, s.seed, s.models, s.spec_hash, s.constraints_hash,
                               s.agents_hash, cfg.config_hash(), s.assumptions)
        ctx.log(f"[{s.run_id}] start: method {s.method}, budget {s.budget.solves_total} solves, "
                f"{s.budget.round_cap} rounds")
        return {}

    def planner(s: LoopState) -> dict:
        try:
            p, call_id = propose(ctx, s)
        except LLMError as e:
            return {"stop_reason": f"planner_error: {e}"}
        ctx.log(f"[{s.run_id}] round {s.budget.rounds_used + 1} planner: {p.action} ({p.diagnosis})")
        pend = s.pending.model_copy(update={"proposal": p, "validation": None, "feedback": []})
        cur = RoundRecord(round=s.budget.rounds_used + 1, proposal=p, planner_call=call_id)
        return {"pending": pend, "current": cur}

    def validator(s: LoopState) -> dict:
        v = validate(s.pending.proposal, s, cfg, acfg)
        upd: dict = {}
        streak = s.pending.invalid_streak + 1 if v.status == "invalid" else 0
        feedback = [f"validator: {r}" for r in v.reasons] if v.status == "invalid" else []
        upd["pending"] = s.pending.model_copy(update={"validation": v, "invalid_streak": streak, "feedback": feedback})
        upd["current"] = s.current.model_copy(update={"validation": v}) if s.current else None
        if v.status == "invalid":
            ctx.log(f"[{s.run_id}] validator: invalid ({streak}): " + "; ".join(v.reasons))
            if streak > lp.validator_retries:
                upd["stop_reason"] = "invalid_proposals"
        elif v.status == "stop":
            upd["stop_reason"] = "planner_stop"
        return upd

    def route_validator(s: LoopState) -> str:
        if s.stop_reason:
            return "finalize"
        return {"invalid": "planner", "ok": "optimize", "needs_edit": "editor", "escalate": "escalate",
                "stop": "finalize"}[s.pending.validation.status]

    def editor(s: LoopState) -> dict:
        req = s.pending.proposal.edit_request
        round_ = s.budget.rounds_used + 1
        k = sum(1 for _ in (ctx.run_dir(s.run_id) / "edits").glob(f"r{round_:02d}_e*")) \
            if (ctx.run_dir(s.run_id) / "edits").is_dir() else 0
        edit_id = f"{s.run_id}-r{round_:02d}-e{k}"
        sandbox = ctx.run_dir(s.run_id) / "edits" / f"r{round_:02d}_e{k}"
        sandbox.mkdir(parents=True, exist_ok=True)
        if ctx.editor is None:
            res = EditResult(ok=False, variant_id="", script_path="", diff_summary="",
                             notes="the editor agent is not available yet (Phase 2 task 8)")
        else:
            try:
                res = ctx.editor(req, s, ctx, sandbox)
            except Exception as e:                                   # noqa: BLE001
                res = EditResult(ok=False, variant_id="", script_path="", diff_summary="", notes=f"editor error: {e}")
        (sandbox / "edit_result.json").write_text(res.model_dump_json(indent=1), encoding="utf-8")
        budget = s.budget.model_copy(update={"solves_used": s.budget.solves_used + res.n_solves})
        if res.ok:
            pend = s.pending.model_copy(update={"edit_request": req, "edit_result": res, "edit_id": edit_id,
                                                "approval": "waiting"})
            return {"pending": pend, "budget": budget}
        fails = s.editor_failures + 1
        upd = {"editor_failures": fails, "budget": budget,
               "pending": s.pending.model_copy(update={"feedback": [f"edit {edit_id} failed: {res.notes}"]})}
        if fails >= lp.editor_failure_cap:
            upd["stop_reason"] = "editor_failures"
        return upd

    def route_editor(s: LoopState) -> str:
        if s.stop_reason:
            return "finalize"
        return "author_approval" if s.pending.approval == "waiting" else "planner"

    def author_approval(s: LoopState) -> dict:
        res = s.pending.edit_result
        ans = interrupt({"type": "edit_approval", "edit_id": s.pending.edit_id,
                         "sandbox": str(ctx.run_dir(s.run_id) / "edits"), "edit_result": res.model_dump(mode="json")})
        ans = ans or {}
        if ans.get("approved"):
            var = Variant(variant_id=res.variant_id, parent=s.pending.edit_request.parent_variant,
                          edit_id=s.pending.edit_id, script_path=res.script_path,
                          new_parameters=[p.model_dump() for p in res.new_parameters])
            approve_variant(cfg, res.variant_id)
            p = s.pending.proposal
            c = p.configuration
            req = s.pending.edit_request
            wiring = {**c.wiring, **{n: req.supply for n in res.new_parts if req.supply and req.supply != "GND"}}
            settings = {**c.variant_settings, **{n: 1.0 for n in res.new_switches}}   # the requested parts exist
            p = p.model_copy(update={"configuration": c.model_copy(update={
                "variant_id": res.variant_id, "wiring": wiring, "variant_settings": settings})})
            return {"model_variants": s.model_variants + [var], "editor_failures": 0,
                    "pending": s.pending.model_copy(update={"approval": "approved", "proposal": p}),
                    "current": s.current.model_copy(update={"proposal": p})}
        reason = ans.get("reason") or "no reason given"
        return {"pending": s.pending.model_copy(update={
            "approval": "rejected", "approval_reason": reason,
            "feedback": [f"the author rejected edit {s.pending.edit_id}: {reason}"]})}

    def route_approval(s: LoopState) -> str:
        return "optimize" if s.pending.approval == "approved" else "planner"

    def escalate(s: LoopState) -> dict:
        p = s.pending.proposal
        ans = interrupt({"type": "escalation", "question": p.escalation, "diagnosis_evidence": p.diagnosis_evidence})
        ans = ans or {}
        if ans.get("stop"):
            return {"stop_reason": "author_stop"}
        return {"pending": s.pending.model_copy(update={
            "feedback": [f"the author answered your escalation: {ans.get('answer') or '(no answer)'}"]})}

    def route_escalate(s: LoopState) -> str:
        return "finalize" if s.stop_reason else "planner"

    def optimize_node(s: LoopState) -> dict:
        p, cur = s.pending.proposal, s.current
        study_id = f"{s.run_id}-r{cur.round:02d}"
        variant = p.configuration.variant_id
        if s.backend and cfg.backend.backend != s.backend:
            raise RuntimeError(f"run {s.run_id} started on backend {s.backend!r} but this process uses "
                               f"{cfg.backend.backend!r}: resume with the run's own config (no solves made)")
        if variant != "base" and not getattr(ctx.backend, "supports_variants", False):
            note = f"variant {variant} cannot be solved: the backend has no model-variant support yet"
            return {"current": cur.model_copy(update={"note": note, "counted": False}),
                    "pending": s.pending.model_copy(update={"feedback": [note]})}
        conf = to_configuration_def(p.configuration, study_id, description=f"agent run {s.run_id} round {cur.round}")
        budget = min(p.solve_budget, s.budget.solves_left)
        ctx.log(f"[{s.run_id}] round {cur.round} optimize: study {study_id}, {budget} solves")
        try:
            res = optimize(cfg, study_id, budget=budget, backend=ctx.backend, study_id=study_id, conf=conf,
                           bounds=bounds_tuple(p.bounds),
                           tags={"run_id": s.run_id, "round": str(cur.round), "purpose": "agent"})
        except Exception as e:                                       # noqa: BLE001
            note = f"optimizer failed: {e}"
            return {"current": cur.model_copy(update={"note": note, "counted": False}),
                    "pending": s.pending.model_copy(update={"feedback": [note]})}
        best_job = res.best_job_id or _best_valid_job(ctx, study_id)
        m = metrics_summary(load_metrics(cfg, best_job))
        b = s.budget.model_copy(update={"solves_used": s.budget.solves_used + res.n_trials})
        ctx.log(f"[{s.run_id}] round {cur.round}: {res.n_trials} solves, {res.n_feasible} feasible, best "
                f"{res.best_score if res.best_score is not None else '-'}")
        return {"budget": b, "current": cur.model_copy(update={
            "study_id": study_id, "n_solves": res.n_trials, "best_job_id": best_job, "metrics": m})}

    def route_optimize(s: LoopState) -> str:
        if s.method == "A1" or not s.current or not s.current.best_job_id:
            return "update_state"
        return "critic"

    def critic(s: LoopState) -> dict:
        cur = s.current
        try:
            v, call_id = review(ctx, s, cur)
        except LLMError as e:
            return {"current": cur.model_copy(update={"note": f"critic error: {e}"})}
        ctx.log(f"[{s.run_id}] round {cur.round} critic: {v.verdict}")
        return {"current": cur.model_copy(update={"critic": v, "critic_call": call_id,
                                                  "counted": cur.counted and v.verdict != "reject"})}

    def update_state(s: LoopState) -> dict:
        cur = s.current
        m = cur.metrics or {}
        upd: dict = {"history": s.history + [cur], "current": None,
                     "budget": s.budget.model_copy(update={"rounds_used": s.budget.rounds_used + 1}),
                     "pending": Pending(feedback=list(s.pending.feedback) if cur.note else [])}
        cand = cur.counted and m.get("valid") and m.get("feasible") and m.get("score") is not None
        improved = bool(cand) and (s.best is None or m["score"] < s.best.score - lp.improvement_tol_deg)
        if improved:
            upd["best"] = BestSoFar(job_id=cur.best_job_id, round=cur.round, score=m["score"], eta=m.get("eta"),
                                    valid=True, feasible=True,
                                    critic_accepted=None if cur.critic is None else cur.critic.verdict != "reject",
                                    configuration=cur.proposal.configuration.model_dump() if cur.proposal else {})
            upd["no_improve_rounds"] = 0
        else:
            upd["no_improve_rounds"] = s.no_improve_rounds + 1
        with ctx.db() as rl:
            rl.record_round(s.run_id, cur.model_dump(mode="json"))
        return upd

    def stop_check(s: LoopState) -> dict:
        if s.budget.solves_left <= 0:
            return {"stop_reason": "budget"}
        if s.budget.rounds_used >= s.budget.round_cap:
            return {"stop_reason": "round_cap"}
        if s.best is not None and s.no_improve_rounds >= lp.no_improvement_rounds:
            return {"stop_reason": "no_improvement"}
        return {}

    def route_stop(s: LoopState) -> str:
        return "finalize" if s.stop_reason else "planner"

    def finalize(s: LoopState) -> dict:
        reason = s.stop_reason or "unknown"
        best = s.best
        success = bool(best and best.feasible and best.critic_accepted is not False)
        summary = {"run_id": s.run_id, "method": s.method, "case_id": s.case_id, "stop_reason": reason,
                   "success": success, "rounds": s.budget.rounds_used, "solves_used": s.budget.solves_used,
                   "best": best.model_dump() if best else None, "assumptions": s.assumptions,
                   "finished_at": now_iso()}
        (ctx.run_dir(s.run_id) / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
        with ctx.db() as rl:
            rl.finish_agent_run(s.run_id, reason, best.job_id if best else None, best.score if best else None,
                                s.budget.solves_used)
        ctx.log(f"[{s.run_id}] stop: {reason}; best {best.score if best else '-'} ({'success' if success else 'no success'})")
        return {"stop_reason": reason}

    g = StateGraph(LoopState)
    for name, fn in [("load_context", load_context), ("planner", planner), ("validator", validator),
                     ("editor", editor), ("author_approval", author_approval), ("escalate", escalate),
                     ("optimize", optimize_node), ("critic", critic), ("update_state", update_state),
                     ("stop_check", stop_check), ("finalize", finalize)]:
        g.add_node(name, fn)
    g.add_edge(START, "load_context")
    g.add_edge("load_context", "planner")
    g.add_conditional_edges("planner", lambda s: "finalize" if s.stop_reason else "validator",
                            ["finalize", "validator"])
    g.add_conditional_edges("validator", route_validator, ["planner", "optimize", "editor", "escalate", "finalize"])
    g.add_conditional_edges("editor", route_editor, ["author_approval", "planner", "finalize"])
    g.add_conditional_edges("author_approval", route_approval, ["optimize", "planner"])
    g.add_conditional_edges("escalate", route_escalate, ["planner", "finalize"])
    g.add_conditional_edges("optimize", route_optimize, ["critic", "update_state"])
    g.add_edge("critic", "update_state")
    g.add_edge("update_state", "stop_check")
    g.add_conditional_edges("stop_check", route_stop, ["planner", "finalize"])
    g.add_edge("finalize", END)
    return g.compile(checkpointer=checkpointer)


def _best_valid_job(ctx: LoopContext, study_id: str) -> str | None:
    """Best valid (possibly infeasible) job of a study, for the critic and the planner's context."""
    with ctx.db() as rl:
        rows = [r for r in rl.study_results(study_id, ctx.cfg.spec_hash()) if r["valid"] and r["score"] is not None]
    return min(rows, key=lambda r: r["score"])["job_id"] if rows else None


# --------------------------------------------------------------------------- running


class LoopRun:
    """A compiled graph bound to one run's checkpoint file."""

    def __init__(self, ctx: LoopContext, run_id: str):
        self.ctx, self.run_id = ctx, run_id
        d = ctx.run_dir(run_id)
        d.mkdir(parents=True, exist_ok=True)
        self.con = sqlite3.connect(str(d / "checkpoints.sqlite"), check_same_thread=False)
        self.graph = build_graph(ctx, SqliteSaver(self.con))
        self.config = {"configurable": {"thread_id": run_id}, "recursion_limit": 2000}

    def close(self) -> None:
        self.con.close()

    def __enter__(self) -> "LoopRun":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def start(self, state: LoopState) -> "LoopStatus":
        self.graph.invoke(state, self.config)
        return self.status()

    def resume(self, answer: dict | None = None) -> "LoopStatus":
        """Continue a paused run (answer = the author's reply) or a crashed one (answer = None)."""
        if self.status().interrupt is not None:
            self.graph.invoke(Command(resume=answer or {}), self.config)
        else:
            self.graph.invoke(None, self.config)
        return self.status()

    def status(self) -> "LoopStatus":
        snap = self.graph.get_state(self.config)
        values = snap.values
        state = LoopState.model_validate(values) if values else None
        intr = None
        for t in snap.tasks or ():
            for i in getattr(t, "interrupts", ()) or ():
                intr = i.value
        return LoopStatus(state=state, interrupt=intr, done=not snap.next)


class LoopStatus:
    def __init__(self, state: LoopState | None, interrupt: dict | None, done: bool):
        self.state, self.interrupt, self.done = state, interrupt, done

    def __repr__(self) -> str:
        s = self.state
        return (f"LoopStatus(done={self.done}, stop={s.stop_reason if s else None}, "
                f"rounds={s.budget.rounds_used if s else 0}, interrupt={bool(self.interrupt)})")


def run_dir_exists(ctx: LoopContext, run_id: str) -> bool:
    return (ctx.run_dir(run_id) / "checkpoints.sqlite").is_file()


def checkpoint_path(ctx: LoopContext, run_id: str) -> Path:
    return ctx.run_dir(run_id) / "checkpoints.sqlite"
