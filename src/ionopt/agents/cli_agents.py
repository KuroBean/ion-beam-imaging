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


def _ctx(cfg: Config, a) -> "LoopContext":
    from ..backends import make_backend
    from .config import load_agents_config
    from .llm import ClaudeCLIClient
    from .roles import LoopContext

    acfg = load_agents_config(cfg.root_dir / "config")
    if getattr(a, "fake_llm", None):
        from .llm_fake import FakeLLM
        llm = FakeLLM.from_dir(a.fake_llm)
    else:
        llm = ClaudeCLIClient(acfg)
    return LoopContext(cfg=cfg, acfg=acfg, llm=llm, backend=make_backend(cfg),
                       runs_dir=cfg.path("results_dir") / "runs", prompts_dir=cfg.root_dir / "prompts",
                       log=lambda s: print(s, flush=True))


def _close(ctx: "LoopContext") -> None:
    if hasattr(ctx.backend, "close"):
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
            st = lr.start(new_state(ctx, run_id, a.method, a.case, a.budget, a.rounds))
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
    p.add_argument("--fake-llm", type=Path, default=None,
                   help="folder of scripted responses <role>_<n>.json instead of Claude (testing)")


def args_agent_resume(p) -> None:
    p.add_argument("run_id")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--approve", action="store_true", help="approve the pending model edit")
    g.add_argument("--reject", default=None, metavar="REASON", help="reject the pending model edit")
    g.add_argument("--answer", default=None, metavar="TEXT", help="answer the planner's escalation")
    g.add_argument("--stop", action="store_true", help="stop the run at the escalation")
    p.add_argument("--fake-llm", type=Path, default=None)


def args_trace(p) -> None:
    p.add_argument("run_id")
