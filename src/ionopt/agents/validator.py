"""Constraint validator for planner proposals (plan_phase2 section 8). Deterministic, no LLM.

Returns ok / needs_edit / invalid (with reasons that go back to the planner) / escalate / stop.
Reuses the Phase 1 checks: electrodes.check_structure for the wiring and
optimize.SearchSpace for ranges, the extraction and no-mirror rules and the stack fit, so a proposal
that passes here cannot fail when the optimizer builds its search space.
"""

from __future__ import annotations

from ..config import Config, ConfigError, ConfigurationDef
from ..electrodes import GND, check_structure, electrode_names
from ..optimize import SearchSpace
from .config import AgentsConfig
from .schemas import Bound, Configuration, PlannerProposal
from .state import LoopState, ValidationResult

DUPLICATE_IOU = 0.8      # every variable's bounds overlap at least this much (intersection / union)
TOL = 1e-9


def presence_supported(cfg: Config) -> bool:
    """Per-electrode removal needs the 2D presence switches (Phase 2 task 7, not built yet)."""
    return False


def to_configuration_def(c: Configuration, config_id: str, description: str = "") -> ConfigurationDef:
    return ConfigurationDef(config_id=config_id, description=description, cfg=c.cfg, wiring=dict(c.wiring))


def bounds_tuple(bounds: dict[str, Bound]) -> dict[str, tuple[float, float]]:
    return {k: (b.lo, b.hi) for k, b in bounds.items()}


def _iou(a: tuple[float, float], b: tuple[float, float]) -> float:
    inter = min(a[1], b[1]) - max(a[0], b[0])
    union = max(a[1], b[1]) - min(a[0], b[0])
    if union <= TOL:
        return 1.0 if inter >= -TOL else 0.0
    return max(0.0, inter) / union


def bounds_overlap(full: dict[str, tuple[float, float]], a: dict[str, Bound], b: dict[str, Bound]) -> float:
    """Smallest per-variable IoU of two bound sets on the same configuration (unlisted = full range)."""
    out = 1.0
    for k, rng in full.items():
        ra = (a[k].lo, a[k].hi) if k in a else rng
        rb = (b[k].lo, b[k].hi) if k in b else rng
        out = min(out, _iou(ra, rb))
    return out


def check_configuration(c: Configuration, state: LoopState, cfg: Config) -> list[str]:
    p: list[str] = []
    if c.variant_id not in state.variant_ids():
        p.append(f"variant_id '{c.variant_id}' is not an approved variant (known: {sorted(state.variant_ids())})")
    names = set(electrode_names(cfg))
    bad = sorted(set(c.removed) - names)
    if bad:
        p.append(f"removed: unknown electrodes {bad} (electrodes: e1..e{len(names)})")
    if c.removed and not presence_supported(cfg):
        p.append("removed: per-electrode removal is not available in the model yet; keep every electrode")
    wired_removed = sorted(e for e in c.removed if c.wiring.get(e, GND) != GND)
    if wired_removed:
        p.append(f"removed electrodes cannot be wired to a supply: {wired_removed}")
    if "e1" in c.removed:
        p.append("e1 is the extractor and cannot be removed")
    p += check_structure(cfg, c.cfg, c.wiring)
    return p


def validate(p: PlannerProposal, state: LoopState, cfg: Config, acfg: AgentsConfig) -> ValidationResult:
    if p.action == "stop":
        return ValidationResult(status="stop")
    if p.action == "escalate_spec":
        return ValidationResult(status="escalate")
    reasons: list[str] = []
    warnings: list[str] = []
    if p.action == "edit_then_optimize" and state.method == "A2":
        reasons.append("the editor is disabled in this run (A2): use the existing switches only")
    c = p.configuration
    assert c is not None                                  # schema guarantees it for these actions
    reasons += check_configuration(c, state, cfg)
    if reasons:
        return ValidationResult(status="invalid", reasons=reasons)

    conf = to_configuration_def(c, f"{state.run_id}-validate")
    try:
        raw = SearchSpace.raw_ranges(cfg, conf)
        full = SearchSpace.from_config(cfg, conf).variable_ranges()
    except ConfigError as e:
        return ValidationResult(status="invalid", reasons=[f"configuration cannot be optimized: {e}"])

    frac = acfg.loop.min_bound_fraction
    for k, b in p.bounds.items():
        if k not in raw:
            reasons.append(f"bounds: '{k}' is not a variable of this configuration (variables: {sorted(raw)})")
            continue
        r_lo, r_hi = raw[k]
        if b.lo < r_lo - TOL or b.hi > r_hi + TOL:
            reasons.append(f"bounds: {k} = [{b.lo:g}, {b.hi:g}] is outside the allowed range [{r_lo:g}, {r_hi:g}]")
            continue
        f_lo, f_hi = full[k]
        w = f_hi - f_lo
        inter = min(b.hi, f_hi) - max(b.lo, f_lo)
        if inter < -TOL or (w > TOL and inter <= TOL):
            reasons.append(f"bounds: {k} = [{b.lo:g}, {b.hi:g}] is outside its usable range [{f_lo:g}, {f_hi:g}] "
                           f"(the extraction / no-ion-mirror rules exclude the rest)")
        elif w > TOL and inter < frac * w - TOL:
            reasons.append(f"bounds: {k} = [{b.lo:g}, {b.hi:g}] is narrower than {frac:.0%} of its usable range "
                           f"[{f_lo:g}, {f_hi:g}]; the optimizer picks values, the planner only sets regions")
    if not reasons and p.bounds:
        try:
            SearchSpace.from_config(cfg, conf, bounds_tuple(p.bounds))
        except ConfigError as e:
            reasons.append(f"bounds break a search-space rule: {e}")

    left = state.budget.solves_left
    lo_b, hi_b = min(acfg.loop.study_budget_min, left), min(acfg.loop.study_budget_max, left)
    if left <= 0:
        reasons.append("no solve budget left; choose stop")
    elif not lo_b <= p.solve_budget <= hi_b:
        reasons.append(f"solve_budget {p.solve_budget} must be within [{lo_b}, {hi_b}] "
                       f"({left} solves left in the run)")

    if p.action == "optimize":
        for rec in state.history:
            q = rec.proposal
            if q is None or q.configuration is None or rec.validation is None or rec.validation.status != "ok":
                continue
            if q.configuration.key() == c.key() and bounds_overlap(full, q.bounds, p.bounds) >= DUPLICATE_IOU:
                if p.repeat_reason:
                    warnings.append(f"repeats round {rec.round} (reason given: {p.repeat_reason})")
                else:
                    reasons.append(f"repeats round {rec.round}: same configuration and bounds overlapping by "
                                   f">= {DUPLICATE_IOU:.0%}; change them or give repeat_reason")
                break

    if reasons:
        return ValidationResult(status="invalid", reasons=reasons, warnings=warnings)
    if p.action == "edit_then_optimize":
        warnings.append("constraints.yaml has no inventory block yet: buildability is checked by the author only")
        return ValidationResult(status="needs_edit", warnings=warnings)
    return ValidationResult(status="ok", warnings=warnings)
