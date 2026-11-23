"""Constraint validator for planner proposals (plan_phase2 section 8). Deterministic, no LLM.

Returns ok / needs_edit / invalid (with reasons that go back to the planner) / escalate / stop.
Reuses the Phase 1 checks: electrodes.check_structure for the wiring and
optimize.SearchSpace for ranges, the extraction and no-mirror rules and the stack fit, so a proposal
that passes here cannot fail when the optimizer builds its search space.
"""

from __future__ import annotations

from ..config import Config, ConfigError, ConfigurationDef
from ..electrodes import check_structure, layout_problems
from ..variants import list_variants, load_variant
from ..optimize import SearchSpace
from .config import AgentsConfig
from .schemas import Bound, Configuration, PlannerProposal
from .state import LoopState, ValidationResult

DUPLICATE_IOU = 0.8      # every variable's bounds overlap at least this much (intersection / union)
TOL = 1e-9


def presence_supported(cfg: Config) -> bool:
    """Part removal / moves are allowed by constraints.electrodes (removable / movable lists).
    The model must have the switches too (2D lens8_axisym_v3+); the worker refuses jobs otherwise."""
    el = cfg.constraints.electrodes
    return bool(el.removable or el.movable)


def to_configuration_def(c: Configuration, config_id: str, description: str = "") -> ConfigurationDef:
    return ConfigurationDef(config_id=config_id, description=description, cfg=c.cfg, wiring=dict(c.wiring),
                            removed=list(c.removed), moved=list(c.moved), variant_id=c.variant_id,
                            variant_settings=dict(c.variant_settings))


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
    known = state.variant_ids() | {m.variant_id for m in list_variants(cfg)}
    if c.variant_id not in known:
        p.append(f"variant_id '{c.variant_id}' is not an approved variant (known: {sorted(known)})")
        return p
    el = cfg.constraints.electrodes
    if "e1" in c.removed or "e1" in c.moved:
        p.append("e1 is the extractor and the stack reference: it cannot be removed or moved")
    if c.cfg in cfg.constraints.chamber_setups:
        p += [f"removed: {x}" for x in layout_problems(cfg, c.cfg, c.removed, {})]
    bad = sorted(set(c.moved) - set(el.movable))
    if bad:
        p.append(f"moved: {bad} are not movable (constraints.electrodes.movable: {el.movable})")
    both = sorted(set(c.moved) & set(c.removed))
    if both:
        p.append(f"{both} both removed and moved")
    p += check_structure(cfg, c.cfg, c.wiring, c.removed, c.variant_id, c.variant_settings)
    return p


def required_removals(variant_id: str, acfg: AgentsConfig, cfg: Config) -> list[str]:
    """loop.require_removed: the configuration's model (for an edit, its parent, which the new variant keeps)
    must have these base parts removed."""
    need = set(acfg.loop.require_removed)
    if not need:
        return []
    var = load_variant(cfg, variant_id)
    missing = sorted(need - set(var.removed_base if var else []))
    if not missing:
        return []
    ok = sorted(m.variant_id for m in list_variants(cfg) if need <= set(m.removed_base))
    return [f"variant_id {variant_id} still has {missing}; the author requires every configuration in this run to "
            f"run without them: use a variant that removes them ({ok or 'none approved yet'})"]


def validate(p: PlannerProposal, state: LoopState, cfg: Config, acfg: AgentsConfig) -> ValidationResult:
    if p.action == "stop":
        return ValidationResult(status="stop")
    if p.action == "escalate_spec":
        return ValidationResult(status="escalate")
    reasons: list[str] = []
    warnings: list[str] = []
    if p.action == "edit_then_optimize" and state.method == "A2":
        reasons.append("the editor is disabled in this run (A2): use the existing switches only")
    if p.action == "edit_then_optimize" and p.edit_request is not None:
        req = p.edit_request
        bad = [i for i in req.inventory_items if cfg.inventory.get(i) is None]
        if bad:
            reasons.append(f"edit_request: {bad} not in the inventory (config/inventory.yaml: "
                           f"{[i.id for i in cfg.inventory.items]})")
        if p.configuration is not None and p.configuration.variant_id != req.parent_variant:
            reasons.append(f"edit_request.parent_variant {req.parent_variant} must be the configuration's variant "
                           f"{p.configuration.variant_id} (the new variant replaces it after approval)")
        if req.supply not in (None, "GND") and req.supply not in cfg.constraints.supplies.low_voltage.channels:
            reasons.append(f"edit_request.supply {req.supply}: new conductors go on an LV channel or GND")
    c = p.configuration
    assert c is not None                                  # schema guarantees it for these actions
    reasons += check_configuration(c, state, cfg)
    reasons += required_removals(c.variant_id, acfg, cfg)
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
        return ValidationResult(status="needs_edit", warnings=warnings)
    return ValidationResult(status="ok", warnings=warnings)
