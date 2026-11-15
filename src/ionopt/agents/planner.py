"""Planner agent (plan_phase2 section 7.1): next configuration, bounds and diagnosis."""

from __future__ import annotations

from .llm import LLMError
from .roles import LoopContext, call_dir, record_call, template
from .schemas import PlannerProposal
from .state import LoopState
from .summaries import load_metrics, planner_context


def planner_prompt(ctx: LoopContext, state: LoopState) -> str:
    last = state.history[-1] if state.history else None
    return planner_context(ctx.cfg, ctx.acfg, state, load_metrics(ctx.cfg, last.best_job_id) if last else None)


def propose(ctx: LoopContext, state: LoopState) -> tuple[PlannerProposal, str]:
    """One planner call; returns the proposal and its call id. Raises LLMError after the retries."""
    round_ = state.budget.rounds_used + 1
    system, t_hash = template(ctx, "planner")
    call_id, cdir = call_dir(ctx, state.run_id, round_, "planner")
    try:
        rec = ctx.llm.call("planner", system, planner_prompt(ctx, state), PlannerProposal, cdir)
    except LLMError as e:
        record_call(ctx, call_id, state.run_id, round_, "planner", None, t_hash, error=str(e), cdir=cdir,
                    model=ctx.acfg.role("planner").model)
        raise
    record_call(ctx, call_id, state.run_id, round_, "planner", rec, t_hash)
    return rec.output, call_id
