"""Critic agent (plan_phase2 section 7.2): fresh-context review of the round's best result.

The critic's working folder holds an evidence/ copy of the best job's plots and metrics.json; with
--restricted its Read tool cannot reach anything else. It sees the planner's claims, not its rationale.
"""

from __future__ import annotations

import shutil

from .llm import LLMError
from .roles import LoopContext, call_dir, record_call, template
from .schemas import CriticVerdict
from .state import LoopState, RoundRecord
from .summaries import critic_context, evidence_files, load_metrics


def review(ctx: LoopContext, state: LoopState, cur: RoundRecord) -> tuple[CriticVerdict, str]:
    system, t_hash = template(ctx, "critic")
    call_id, cdir = call_dir(ctx, state.run_id, cur.round, "critic")
    job_dir = ctx.cfg.path("results_dir") / cur.best_job_id
    ev = cdir / "evidence"
    ev.mkdir(parents=True, exist_ok=True)
    names = []
    for f in evidence_files(job_dir):
        shutil.copy2(f, ev / f.name)
        names.append(f"evidence/{f.name}")
    if (job_dir / "metrics.json").is_file():
        shutil.copy2(job_dir / "metrics.json", ev / "metrics.json")
        names.append("evidence/metrics.json")
    study = (f"- optimizer study {cur.study_id}: {cur.n_solves} solves; the best job is {cur.best_job_id}"
             f" ({'feasible' if (cur.metrics or {}).get('feasible') else 'no feasible run: best valid run shown'})")
    prompt = critic_context(ctx.cfg, state, load_metrics(ctx.cfg, cur.best_job_id), study, names)
    try:
        rec = ctx.llm.call("critic", system, prompt, CriticVerdict, cdir)
    except LLMError as e:
        record_call(ctx, call_id, state.run_id, cur.round, "critic", None, t_hash, error=str(e), cdir=cdir,
                    model=ctx.acfg.role("critic").model)
        raise
    record_call(ctx, call_id, state.run_id, cur.round, "critic", rec, t_hash)
    return rec.output, call_id
