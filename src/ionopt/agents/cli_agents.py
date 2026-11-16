"""CLI commands of the agent loop: agent-run, agent-resume, trace (plan_phase2 section 11).

Argument parsers are cheap to import; LangGraph and the backends load only when a command runs.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

from ..config import Config
from ..runlog import RunLog

if TYPE_CHECKING:
    from .graph import LoopStatus
    from .roles import LoopContext


def _ctx(cfg: Config, a, backend: bool = True) -> "LoopContext":
    from ..backends import make_backend
    from .config import load_agents_config
    from .llm import ClaudeCLIClient
    from .roles import LoopContext

    loop = {"study_budget_max": a.round_max} if getattr(a, "round_max", None) else {}
    acfg = load_agents_config(cfg.root_dir / "config", overrides={"loop": loop} if loop else None)
    if getattr(a, "fake_llm", None):
        from .llm_fake import FakeLLM
        llm = FakeLLM.from_dir(a.fake_llm)
    else:
        llm = ClaudeCLIClient(acfg)
    from .editor import Editor
    return LoopContext(cfg=cfg, acfg=acfg, llm=llm, backend=make_backend(cfg) if backend else None, editor=Editor(),
                       runs_dir=cfg.path("results_dir") / "runs", prompts_dir=cfg.root_dir / "prompts",
                       log=lambda s: print(s, flush=True))


def _close(ctx: "LoopContext") -> None:
    if ctx.backend is not None and hasattr(ctx.backend, "close"):
        ctx.backend.close()


def _report(st: "LoopStatus", run_id: str) -> int:
    s = st.state
    if st.interrupt is not None:
        i = st.interrupt
        print(f"\nPAUSED: run {run_id} waits for the author ({i.get('type')}).")
        if i.get("type") == "edit_approval":
            r = i.get("edit_result", {})
            print(f"  edit {i.get('edit_id')}: variant {r.get('variant_id')}: {r.get('diff_summary')}")
            print(f"  checks: {r.get('checks')}; smoke job: {r.get('smoke_job_id')}; files: {i.get('sandbox')}")
            print(f"  approve: ionopt agent-resume {run_id} --approve")
            print(f"  reject:  ionopt agent-resume {run_id} --reject \"<reason>\"")
        else:
            print(f"  question: {i.get('question')}\n  evidence: {i.get('diagnosis_evidence')}")
            print(f"  answer: ionopt agent-resume {run_id} --answer \"<text>\"   (or --stop)")
        return 3
    if s is not None:
        best = f"{s.best.score:.4g} deg (job {s.best.job_id}, round {s.best.round})" if s.best else "none"
        print(f"\nrun {run_id}: stop {s.stop_reason}; {s.budget.rounds_used} rounds, "
              f"{s.budget.solves_used}/{s.budget.solves_total} solves; best {best}")
        print(f"trace: ionopt trace {run_id}")
    return 0


def cmd_agent_run(cfg: Config, a) -> int:
    from .graph import LoopRun, checkpoint_path, new_state

    run_id = a.run_id or f"{a.method.lower()}-{a.case}-{time.strftime('%Y%m%d-%H%M%S')}"
    ctx = _ctx(cfg, a)
    if checkpoint_path(ctx, run_id).is_file():
        print(f"run {run_id} exists: use ionopt agent-resume {run_id}", file=sys.stderr)
        return 2
    try:
        with LoopRun(ctx, run_id) as lr:
            st = lr.start(new_state(ctx, run_id, a.method, a.case, a.budget, a.rounds, a.goal))
    finally:
        _close(ctx)
    return _report(st, run_id)


def cmd_agent_resume(cfg: Config, a) -> int:
    from .graph import LoopRun, checkpoint_path

    ctx = _ctx(cfg, a)
    if not checkpoint_path(ctx, a.run_id).is_file():
        print(f"no run {a.run_id} under {ctx.runs_dir}", file=sys.stderr)
        return 2
    answer = None
    if a.approve:
        answer = {"approved": True}
    elif a.reject is not None:
        answer = {"approved": False, "reason": a.reject}
    elif a.answer is not None:
        answer = {"answer": a.answer}
    elif a.stop:
        answer = {"stop": True}
    try:
        with LoopRun(ctx, a.run_id) as lr:
            st = lr.status()
            if st.done:
                print(f"run {a.run_id} already finished ({st.state.stop_reason if st.state else '?'})")
                return 0
            if st.interrupt is not None and answer is None:
                return _report(st, a.run_id)
            st = lr.resume(answer)
    finally:
        _close(ctx)
    return _report(st, a.run_id)


def cmd_agent_plan(cfg: Config, a) -> int:
    """One planner call on the current run log (no solves, no loop): prompt, proposal, validator verdict."""
    from .graph import new_state
    from .llm import LLMError
    from .planner import planner_prompt, propose
    from .validator import validate

    run_id = a.run_id or f"plan-{time.strftime('%Y%m%d-%H%M%S')}"
    ctx = _ctx(cfg, a, backend=False)
    state = new_state(ctx, run_id, a.method, a.case, a.budget, a.rounds, a.goal)
    if a.prompt_only:
        out = ctx.run_dir(run_id) / "planner_prompt.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(planner_prompt(ctx, state), encoding="utf-8")
        print(f"written: {out}")
        return 0
    try:
        p, call_id = propose(ctx, state)
    except LLMError as e:
        print(f"planner failed: {e}", file=sys.stderr)
        return 1
    v = validate(p, state, cfg, ctx.acfg)
    print(json.dumps(p.model_dump(mode="json", exclude_none=True), indent=1))
    print(f"\nvalidator: {v.status}" + "".join(f"\n  - {r}" for r in v.reasons))
    print(f"call folder: {ctx.run_dir(run_id) / 'calls'} ({call_id})")
    return 0


def cmd_agent_edit(cfg: Config, a) -> int:
    """One editor call outside a loop: build inventory parts into a 2D variant (checked, not approved)."""
    from ..variants import approve_variant
    from .editor import Editor
    from .graph import new_state
    from .schemas import EditRequest

    if a.approve_variant:
        m = approve_variant(cfg, a.approve_variant)
        print(f"approved variant {m.variant_id} ({m.approved_at}): planners may now use it")
        return 0
    if not a.item or not a.description:
        print("give --item and --description (or --approve-variant ID)", file=sys.stderr)
        return 2
    run_id = a.run_id or f"edit-{time.strftime('%Y%m%d-%H%M%S')}"
    ctx = _ctx(cfg, a)
    state = new_state(ctx, run_id, "agent", "nominal", a.budget, None)
    sandbox = ctx.run_dir(run_id) / "edits" / "r01_e0"
    sandbox.mkdir(parents=True, exist_ok=True)
    req = EditRequest(inventory_items=a.item, description=a.description, reason=a.reason, supply=a.supply,
                      parent_variant=a.parent)
    try:
        res = (ctx.editor or Editor())(req, state, ctx, sandbox)
    finally:
        _close(ctx)
    (sandbox / "edit_result.json").write_text(res.model_dump_json(indent=1), encoding="utf-8")
    print(json.dumps(res.model_dump(mode="json"), indent=1))
    if res.ok:
        print(f"\nreview: {Path(res.script_path).parent / 'edit.diff'} and the smoke run {res.smoke_job_id}")
        print(f"approve: ionopt agent-edit --approve-variant {res.variant_id}")
    return 0 if res.ok else 1


def trace(cfg: Config, run_id: str) -> tuple[dict, str]:
    """A run's rounds, agent calls and metrics as JSON and markdown (for the lab report)."""
    with RunLog(cfg.path("db_path")) as rl:
        run, rounds, calls = rl.agent_run(run_id), rl.agent_rounds(run_id), rl.agent_calls(run_id)
    if run is None:
        raise SystemExit(f"no agent run {run_id} in the run log")
    data = {"run": run, "rounds": [{**r, "record": json.loads(r.pop("record_json"))} for r in rounds],
            "calls": [{k: v for k, v in c.items() if k not in ("raw_json",)} for c in calls]}
    cost = sum(c["cost_usd"] or 0 for c in calls)
    dur = sum(c["duration_s"] or 0 for c in calls)
    md = [f"# Agent run {run_id}", "",
          f"- method {run['method']}, case {run['case_id']}, seed {run['seed']}, models {run['models_json']}",
          f"- started {run['started_at']}, finished {run['finished_at'] or '-'}, stop: {run['stop_reason'] or '-'}",
          f"- solves {run['solves_used'] or 0}; best {run['best_score'] if run['best_score'] is not None else '-'} "
          f"deg (job {run['best_job_id'] or '-'})",
          f"- agent calls {len(calls)}, {dur:.0f} s, ~${cost:.3f} (CLI estimate)",
          f"- assumptions: {'; '.join(json.loads(run['assumptions_json'] or '[]'))}", "",
          "| round | action | diagnosis | validation | study | solves | score | eta | feasible | critic | counted |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in data["rounds"]:
        md.append(f"| {r['round']} | {r['action']} | {r['diagnosis']} | {r['validation_status']} | {r['study_id']} | "
                  f"{r['n_solves']} | {r['score'] if r['score'] is not None else '-'} | "
                  f"{r['eta'] if r['eta'] is not None else '-'} | {r['feasible']} | {r['critic_verdict'] or '-'} | "
                  f"{r['counted']} |")
    md += ["", "| call | role | model | retries | s | $ | error |", "|---|---|---|---|---|---|---|"]
    for c in calls:
        md.append(f"| {c['call_id']} | {c['role']} | {c['model']} | {c['retries']} | {c['duration_s'] or 0:.0f} | "
                  f"{c['cost_usd'] or 0:.4f} | {(c['error'] or '')[:80]} |")
    return data, "\n".join(md) + "\n"


def cmd_trace(cfg: Config, a) -> int:
    data, md = trace(cfg, a.run_id)
    out = cfg.path("results_dir") / "runs" / a.run_id
    out.mkdir(parents=True, exist_ok=True)
    (out / "trace.json").write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
    (out / "trace.md").write_text(md, encoding="utf-8")
    print(md)
    print(f"written: {out / 'trace.md'}, {out / 'trace.json'}")
    return 0


def args_agent_run(p) -> None:
    p.add_argument("--run-id", default=None, help="default <method>-<case>-<time>")
    p.add_argument("--method", choices=["agent", "A1", "A2"], default="agent",
                   help="agent = full loop; A1 = no critic; A2 = no editor")
    p.add_argument("--case", default="nominal", help="held-out case id (recorded; spec overrides via --set)")
    p.add_argument("--budget", type=int, default=None, help="total solves (default config/agents.yaml)")
    p.add_argument("--rounds", type=int, default=None, help="round cap (default config/agents.yaml)")
    p.add_argument("--round-max", type=int, default=None, metavar="N",
                   help="largest optimizer study per round (overrides loop.study_budget_max; give it again on resume)")
    p.add_argument("--goal", default=None, metavar="TEXT",
                   help="optional author direction shown to the planner every round (recorded as a run assumption)")
    p.add_argument("--fake-llm", type=Path, default=None,
                   help="folder of scripted responses <role>_<n>.json instead of Claude (testing)")


def args_agent_plan(p) -> None:
    args_agent_run(p)
    p.add_argument("--prompt-only", action="store_true", help="write the planner prompt, make no LLM call")


def args_agent_edit(p) -> None:
    p.add_argument("--item", action="append", default=[], help="inventory id (repeatable)")
    p.add_argument("--description", default=None, help="what to build and which dimensions to sweep")
    p.add_argument("--supply", default=None, help="LV channel or GND for new conductors")
    p.add_argument("--parent", default="base", help="parent model variant")
    p.add_argument("--reason", default="author trial")
    p.add_argument("--run-id", default=None)
    p.add_argument("--budget", type=int, default=None)
    p.add_argument("--approve-variant", default=None, metavar="ID", help="approve a checked variant and exit")
    p.add_argument("--fake-llm", type=Path, default=None)


def args_agent_resume(p) -> None:
    p.add_argument("run_id")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--approve", action="store_true", help="approve the pending model edit")
    g.add_argument("--reject", default=None, metavar="REASON", help="reject the pending model edit")
    g.add_argument("--answer", default=None, metavar="TEXT", help="answer the planner's escalation")
    g.add_argument("--stop", action="store_true", help="stop the run at the escalation")
    p.add_argument("--round-max", type=int, default=None, metavar="N", help="same as agent-run --round-max")
    p.add_argument("--fake-llm", type=Path, default=None)


def args_trace(p) -> None:
    p.add_argument("run_id")
