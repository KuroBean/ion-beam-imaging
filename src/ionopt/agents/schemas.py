"""Structured outputs of the agents (plan_phase2 section 7). These pydantic models are also the
JSON schemas handed to `claude -p --json-schema`, so field descriptions are part of the prompt.

Units: voltages in V, positions in mm. Bound keys are the optimizer variable names
(optimize.SearchSpace.raw_ranges): the LV channels used by the wiring (LV1..LV4), the MCP-front and
mesh HV ports (HV1, HV4), and lens_gap_mm, mesh_gap_mm, z_mcp_mm.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Diagnosis = Literal["parametric", "structural", "specification", "none"]
Action = Literal["optimize", "edit_then_optimize", "escalate_spec", "stop"]
ClaimStatus = Literal["supported", "contradicted", "untestable"]
Verdict = Literal["accept", "reject", "dispute"]


class _S(BaseModel):
    model_config = ConfigDict(extra="forbid")


# --------------------------------------------------------------------------- planner


class Bound(_S):
    lo: float
    hi: float

    @model_validator(mode="after")
    def _order(self):
        if self.lo > self.hi:
            raise ValueError(f"lo {self.lo} > hi {self.hi}")
        return self


class Configuration(_S):
    """Structure the optimizer cannot change (plan_v1 7.2 format)."""

    cfg: int = Field(description="chamber setup (1, 2 or 3)")
    wiring: dict[str, str] = Field(
        description="tip and e1..e9 -> LV1..LV4 or GND; any node not listed is grounded. Electrodes on the "
                    "same channel share one voltage.")
    removed: list[str] = Field(default_factory=list,
                               description="stack parts left out (plates e2..e9, deflectors d1, d2; see the design "
                                           "space for what is removable). A removed part cannot be wired.")
    moved: list[str] = Field(default_factory=list,
                             description="plates whose axial position the optimizer tunes (variable "
                                         "<plate>_offset_mm = front face from the e1 front face); the others stay "
                                         "as built. Needs room: the as-built plates are packed at the minimum gap.")
    variant_id: str = Field("base", description="model variant: 'base' or an approved editor variant id")

    def key(self) -> tuple:
        """Identity for duplicate detection: grounded entries do not matter."""
        w = tuple(sorted((k, v) for k, v in self.wiring.items() if v != "GND"))
        return (self.cfg, w, tuple(sorted(self.removed)), tuple(sorted(self.moved)), self.variant_id)


class Claim(_S):
    id: str = Field(description="short id, e.g. 'c1'")
    statement: str = Field(description="a testable prediction about this round's best result")
    evidence_needed: str = Field(description="which metric or plot would confirm or refute it")


class EditRequest(_S):
    """Geometry change that is not a switch in the model (plan_phase2 7.3). 2D only for now."""

    element: Literal["grounded_grid", "electrode", "move_fixed_part", "mesh_change", "other"]
    description: str = Field(description="what to add, remove or change, in words")
    z_mm: float | None = Field(None, description="axial position from the tip apex, mm (if applicable)")
    dimensions_mm: dict[str, float] = Field(default_factory=dict, description="e.g. r_in, r_out, thickness")
    supply: str | None = Field(None, description="LV1..LV4, GND or an HV port, if it is an electrode")
    reason: str
    parent_variant: str = "base"


class PlannerProposal(_S):
    diagnosis: Diagnosis = Field(
        description="why the last result falls short: parametric (better values inside the current structure "
                    "should fix it), structural (needs another configuration or geometry), specification "
                    "(the requirement or an assumption looks unreachable or wrong; the author must decide), "
                    "none (first round)")
    diagnosis_evidence: str = Field(description="metrics or critic findings that support the diagnosis")
    action: Action
    configuration: Configuration | None = Field(None, description="required for optimize / edit_then_optimize")
    bounds: dict[str, Bound] = Field(
        default_factory=dict,
        description="optional narrowing of optimizer variables (V, mm); unlisted variables keep their full range")
    solve_budget: int = Field(0, ge=0, description="solves for this round's optimizer study")
    edit_request: EditRequest | None = None
    claims: list[Claim] = Field(default_factory=list)
    repeat_reason: str | None = Field(None, description="required when repeating an earlier configuration "
                                                        "with heavily overlapping bounds")
    escalation: str | None = Field(None, description="for escalate_spec: the question for the author")
    rationale: str = Field(description="free text; logged, not shown to the critic")

    @model_validator(mode="after")
    def _consistent(self):
        if self.action in ("optimize", "edit_then_optimize"):
            if self.configuration is None:
                raise ValueError(f"action {self.action} needs a configuration")
            if self.solve_budget < 1:
                raise ValueError(f"action {self.action} needs solve_budget >= 1")
        if self.action == "edit_then_optimize" and self.edit_request is None:
            raise ValueError("action edit_then_optimize needs an edit_request")
        if self.action == "escalate_spec" and not self.escalation:
            raise ValueError("action escalate_spec needs the escalation question")
        ids = [c.id for c in self.claims]
        if len(ids) != len(set(ids)):
            raise ValueError("claim ids must be unique")
        return self


# --------------------------------------------------------------------------- critic


class ClaimCheck(_S):
    claim_id: str
    status: ClaimStatus = Field(description="untestable if the given evidence cannot decide it")
    evidence: str = Field(description="the metric value or plot that shows it")


class CriticVerdict(_S):
    verdict: Verdict = Field(
        description="accept: result stands. reject: it should not count (validity problem the checker missed, "
                    "suspicious result). dispute: valid, but a planner claim is contradicted or untested.")
    reasons: str
    claim_checks: list[ClaimCheck] = Field(default_factory=list)
    observed_failure_modes: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list, description="non-binding ideas for the planner")


# --------------------------------------------------------------------------- editor


class NewParameter(_S):
    name: str
    unit: str
    default: float
    lo: float
    hi: float


class EditResult(_S):
    ok: bool
    variant_id: str
    script_path: str = Field(description="edited copy of scripts/build_axisym.py, relative to the sandbox")
    diff_summary: str
    new_parameters: list[NewParameter] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict,
                                    description="build, selections, no_overlap, min_gap, field_limit, smoke_valid")
    smoke_job_id: str | None = None
    notes: str = ""
