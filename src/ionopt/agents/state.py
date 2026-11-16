"""LoopState: the one shared state of an agent run (plan_phase2 section 6).

LangGraph checkpoints it after every node (SQLite), so a run can be resumed and inspected. Agents
never see it directly: agents/summaries.py builds their prompts from it.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .schemas import CriticVerdict, EditRequest, EditResult, PlannerProposal

Method = Literal["agent", "A1", "A2"]


class _St(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Budget(_St):
    solves_total: int
    solves_used: int = 0
    round_cap: int
    rounds_used: int = 0

    @property
    def solves_left(self) -> int:
        return max(0, self.solves_total - self.solves_used)


class ValidationResult(_St):
    status: Literal["ok", "needs_edit", "invalid", "escalate", "stop"]
    reasons: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class Variant(_St):
    variant_id: str
    parent: str
    edit_id: str
    script_path: str
    new_parameters: list[dict] = Field(default_factory=list)


class RoundRecord(_St):
    round: int
    proposal: PlannerProposal | None = None
    validation: ValidationResult | None = None
    study_id: str | None = None
    n_solves: int = 0
    best_job_id: str | None = None
    metrics: dict = Field(default_factory=dict)          # summaries.metrics_summary of the best job
    critic: CriticVerdict | None = None
    counted: bool = True                                 # False when the critic rejected the result
    planner_call: str | None = None                      # call folder (relative to the run folder)
    critic_call: str | None = None
    note: str | None = None


class BestSoFar(_St):
    job_id: str
    round: int
    score: float
    eta: float | None = None
    valid: bool = True
    feasible: bool = True
    critic_accepted: bool | None = None                  # None in A1 (no critic)
    configuration: dict = Field(default_factory=dict)


class Pending(_St):
    proposal: PlannerProposal | None = None
    validation: ValidationResult | None = None
    invalid_streak: int = 0
    edit_request: EditRequest | None = None
    edit_result: EditResult | None = None
    edit_id: str | None = None
    approval: Literal["none", "waiting", "approved", "rejected"] = "none"
    approval_reason: str | None = None
    feedback: list[str] = Field(default_factory=list)    # validator / author messages for the next planner call


class LoopState(_St):
    run_id: str
    method: Method = "agent"
    case_id: str = "nominal"
    seed: int = 0
    models: dict[str, str] = Field(default_factory=dict)
    budget: Budget
    spec_hash: str = ""
    constraints_hash: str = ""
    agents_hash: str = ""
    assumptions: list[str] = Field(default_factory=list)
    goal: str | None = None                              # optional author direction for the planner (--goal)
    model_variants: list[Variant] = Field(default_factory=list)
    history: list[RoundRecord] = Field(default_factory=list)
    best: BestSoFar | None = None
    pending: Pending = Field(default_factory=Pending)
    current: RoundRecord | None = None                   # the round between optimize and update_state
    no_improve_rounds: int = 0
    editor_failures: int = 0
    stop_reason: str | None = None
    paused: str | None = None                            # why the loop waits for the author

    def variant_ids(self) -> set[str]:
        return {"base"} | {v.variant_id for v in self.model_variants}
