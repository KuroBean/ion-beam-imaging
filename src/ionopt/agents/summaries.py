"""Deterministic prompt context (plan_phase2 section 6): agents never read the raw state.

Every function here is pure given (cfg, state, run log contents), so identical inputs give identical
prompts. Numbers are rounded to what a decision needs; tables are plain markdown.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .. import units
from ..config import Config
from ..optimize import SearchSpace
from ..runlog import RunLog
from ..variants import list_variants, load_variant
from .config import AgentsConfig
from .state import LoopState
from .validator import presence_supported, to_configuration_def


def _r(v: Any, nd: int = 3) -> Any:
    if isinstance(v, float):
        return float(f"{v:.{nd}g}")
    return v


def _fmt(v: Any, nd: int = 3) -> str:
    if v is None:
        return "-"
    if isinstance(v, bool):
        return "yes" if v else "no"
    if isinstance(v, float):
        return f"{v:.{nd}g}"
    return str(v)


# --------------------------------------------------------------------------- metrics


def load_metrics(cfg: Config, job_id: str | None) -> dict | None:
    if not job_id:
        return None
    f = cfg.path("results_dir") / job_id / "metrics.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else None


def metrics_summary(m: dict | None, n_rows: int = 8) -> dict:
    """Compact metrics of one job: validity, requirements, fates, spot, coarse r(theta) table."""
    if not m:
        return {}
    req, spot, mp = m.get("requirements") or {}, m.get("spot") or {}, m.get("mapping") or {}
    out = {"job_id": m.get("job_id"), "valid": m.get("valid"), "feasible": m.get("feasible"),
           "score": _r(m.get("score")), "flags": (m.get("flags") or [])[:6],
           "eta": _r(req.get("eta")), "eta_min": req.get("eta_min"), "frac_fast": _r(req.get("frac_fast")),
           "monotonic": req.get("monotonic"), "evaluable": req.get("evaluable"),
           "fates": {k: _r(v, 2) for k, v in (m.get("fates") or {}).items() if v},
           "spot": {k: _r(spot.get(k)) for k in ("r50_mm", "r90_mm", "r_max_mm", "fill_fraction", "rms_axis_mm",
                                                  "centroid_offset_mm", "impact_KE_mean_eV", "tof_mean_us")
                    if spot.get(k) is not None},
           "eval_theta_max_deg": _r(mp.get("eval_theta_max_deg")), "n_eval": mp.get("n_eval")}
    th, r, dth, lf = (mp.get(k) or [] for k in ("theta_deg", "r_mm", "dtheta_deg", "landed_frac"))
    if th:
        step = max(1, len(th) // n_rows)
        out["r_theta"] = [{"theta_deg": _r(th[i]), "r_mm": _r(r[i]) if i < len(r) else None,
                           "dtheta_deg": _r(dth[i]) if i < len(dth) else None,
                           "landed_frac": _r(lf[i], 2) if i < len(lf) else None}
                          for i in range(0, len(th), step)]
    return out


def metrics_block(s: dict) -> str:
    if not s:
        return "(no evaluable result)"
    lines = [f"- job {s.get('job_id')}: valid {_fmt(s.get('valid'))}, feasible {_fmt(s.get('feasible'))}, "
             f"score (worst dtheta) {_fmt(s.get('score'))} deg",
             f"- eta {_fmt(s.get('eta'))} (min {_fmt(s.get('eta_min'))}), fast fraction {_fmt(s.get('frac_fast'))}, "
             f"monotonic r(theta) {_fmt(s.get('monotonic'))}, evaluable {_fmt(s.get('evaluable'))}, "
             f"evaluated up to {_fmt(s.get('eval_theta_max_deg'))} deg ({_fmt(s.get('n_eval'))} angles)"]
    if s.get("flags"):
        lines.append("- checker flags: " + "; ".join(s["flags"]))
    if s.get("fates"):
        lines.append("- ion fates (weight fraction): " + ", ".join(f"{k} {v}" for k, v in s["fates"].items()))
    if s.get("spot"):
        lines.append("- spot: " + ", ".join(f"{k} {v}" for k, v in s["spot"].items()))
    if s.get("r_theta"):
        lines.append("- r(theta): " + "; ".join(f"{x['theta_deg']} deg -> r {_fmt(x['r_mm'])} mm, dtheta "
                                                f"{_fmt(x['dtheta_deg'])}, landed {_fmt(x['landed_frac'])}"
                                                for x in s["r_theta"]))
    return "\n".join(lines)


# --------------------------------------------------------------------------- spec / design space


def _meniscus_line(cfg: Config) -> str:
    """What theta means in the meniscus picture, with an example angle map (planner and critic misread
    the clipped angles as launch angles otherwise)."""
    L, R, D = cfg.spec.launch, cfg.spec.requirements, cfg.spec.detector
    text = (f"- emission angles: theta in every metric, r(theta) and weight is the angle at the meniscus. The "
            f"emitter field bends the {L.E0_eV:g} eV ions toward the axis before the model launch point, so launch "
            f"angles are several times smaller. Weights are Gaussian(HWHM {L.hwhm_deg:g} deg) x sin(theta): about "
            f"half of the emission lies above the HWHM. Because a narrower accepted cone gives a larger dr/dtheta "
            f"on the fixed MCP, the best designs tend to clip angles until eta just meets eta_min "
            f"({R.eta_min:g} with mesh transmission {D.mesh_open_fraction:g}).")
    dv = cfg.optimizer.fixed_extraction_V
    if dv is None:
        return text
    try:
        import numpy as np

        from ..launch import meniscus_angle_map, preacceleration
        gap = 20e-3                                   # nominal lens_gap for the example; the map changes slowly with it
        amap = meniscus_angle_map(L, preacceleration(L, dv, 0.0, gap))
        th = np.radians([10.0, 20.0, 30.0, 50.0])
        out = np.degrees(amap(th, L.E0_eV))
        ex = ", ".join(f"{a:g} -> {b:.1f}" for a, b in zip([10, 20, 30, 50], out))
        return text + f" Example at the fixed {dv:g} V extraction and lens_gap 20 mm (meniscus -> launch, deg): {ex}."
    except Exception:                                  # the example is a hint only; never break the prompt
        return text


def spec_block(cfg: Config) -> str:
    L, D, R = cfg.spec.launch, cfg.spec.detector, cfg.spec.requirements
    if R.impact_threshold_eV_per_charge is not None:
        thr = f"impact energy >= {R.impact_threshold_eV_per_charge:g} eV per charge"
    elif R.impact_threshold_mps is not None:
        m = R.threshold_species_mass_Da or L.mass_Da
        ev = 0.5 * m * units.DALTON * R.impact_threshold_mps ** 2 / units.E_CHARGE
        thr = (f"impact speed of a {m:g} Da ion >= {R.impact_threshold_mps:.3g} m/s, i.e. >= {ev / 1000:.3g} keV per "
               f"charge gained between the tip and the MCP front")
    else:
        thr = None
    return "\n".join([
        f"- ions: mass {L.mass_Da} Da, charge {L.charge:+d}, E0 {L.E0_eV} eV, energy spread {L.dE_eV} eV, "
        f"emission HWHM {L.hwhm_deg} deg at the {L.emission_angle_at}, pre-acceleration "
        f"{'on' if L.preaccel else 'off'}",
        *([_meniscus_line(cfg)] if L.preaccel and L.emission_angle_at == "meniscus" else []),
        f"- goal: minimize the worst angular resolution dtheta (deg) over the evaluated emission angles, "
        f"so the MCP spot maps emission angle to radius as finely as possible",
        f"- feasible requires: collection efficiency eta >= {R.eta_min} (MCP active area x mesh "
        f"transmission {D.mesh_open_fraction}), monotonic r(theta), fast fraction >= {R.frac_fast_min} "
        f"({thr if thr is not None else 'impact threshold not set: always passes'})",
        f"- detector: MCP diameter {D.mcp_active_diameter_mm} mm, resolution sigma {D.sigma_mcp_um} um"])


def design_space_block(cfg: Config, state: LoopState) -> str:
    cs = cfg.constraints
    lv = cs.supplies.low_voltage
    lines = ["Chamber setups (positions in mm from the tip apex; [a, a] = fixed):"]
    for k, c in sorted(cs.chamber_setups.items()):
        rng = (c.z_mcp_mm, c.mesh_gap_mm, c.lens_gap_mm)
        if any(r is None or None in r for r in rng):
            lines.append(f"- cfg {k} ({c.name}): NOT USABLE (position ranges not set)")
        else:
            lines.append(f"- cfg {k} ({c.name}): z_mcp {c.z_mcp_mm}, mesh_gap {c.mesh_gap_mm}, "
                         f"lens_gap {c.lens_gap_mm}")
    lines.append(f"Supplies: {len(lv.channels)} low-voltage channels {lv.channels}, range {lv.range_V} V. Each of "
                 f"{lv.connectable} is wired to one channel or GND; electrodes on one channel share its voltage. "
                 f"HV ports have fixed roles {cs.supplies.high_voltage.roles}; MCP front {cs.supplies.mcp_front_V} V, "
                 f"mesh {cs.supplies.mesh_V} V.")
    el = cs.electrodes
    stack = ", ".join(f"e{k} front {s.front_mm} mm" for k, s in enumerate(el.stack, start=1))
    defl = ", ".join(f"{d.name} front {d.front_mm} mm (cfg {d.cfgs})" for d in el.deflectors)
    lines.append(f"Lens stack: {el.count} plates (e1 = extractor, aperture radius {el.stack[0].r_in_mm} mm), placed "
                 f"by lens_gap (tip apex to the e1 front face); as built, front faces from e1: {stack}. "
                 f"Deflector pairs (grounded): {defl}.")
    if presence_supported(cfg):
        lines.append(f"Part switches: configuration.removed may leave out {el.removable}; configuration.moved lets the "
                     f"optimizer tune the axial position of {el.movable} (variable <plate>_offset_mm, front face from "
                     f"the e1 front face), keeping at least {el.min_gap_mm} mm between facing surfaces of neighbours"
                     + (f" and ending before {el.max_offset_mm} mm" if el.max_offset_mm else "") +
                     ". As built, every plate already sits at that minimum gap, so a plate can only move into room "
                     "made by removing a neighbour (or, without deflectors, the last plate can move back toward the "
                     "mesh).")
    else:
        lines.append("Part switches: NOT available (keep every part as built).")
    rules = []
    if cfg.optimizer.no_mirror:
        rules.append("no ion mirrors: every lens channel and the mesh stay below the tip potential (positive ions) "
                     "and the tip stays above ground")
    if cfg.spec.launch.preaccel:
        rules.append(f"extraction: the tip-e1 field accelerates the ions by >= {cfg.optimizer.min_extraction_V} V")
    if cfg.optimizer.fixed_extraction_V is not None:
        sign = 1 if cfg.spec.launch.charge > 0 else -1
        rules.append(f"fixed extraction (author): e1 follows the tip at V_tip - V_e1 = "
                     f"{sign * cfg.optimizer.fixed_extraction_V:g} V, so e1's channel is not a variable: do not "
                     "bound it, bound the tip channel instead")
    if rules:
        lines.append("Optimizer rules (always enforced): " + "; ".join(rules) + ".")
    hv = cs.supplies.high_voltage.roles
    port = {role: k for k, role in hv.items()}
    lines.append(f"Optimizer variables (the names bounds use): each LV channel used by the wiring (V), "
                 f"{port.get('mcp_front')} (MCP front, V), {port.get('mesh')} (mesh, V), lens_gap_mm, mesh_gap_mm, "
                 f"z_mcp_mm and <plate>_offset_mm of moved plates (mm). A position fixed by its range ([a, a]) is not a variable. Omitted variables keep "
                 f"their full usable range.")
    lines.append("Model variants (configuration.variant_id; 2D models the editor built and the author approved):")
    lines += variants_lines(cfg, state)
    if state.method == "A2":
        lines.append("Geometry edits are DISABLED in this run: use the existing switches only.")
    return "\n".join(lines)


def variants_lines(cfg: Config, state: LoopState) -> list[str]:
    seen = {m.variant_id: m for m in list_variants(cfg)}
    for v in state.model_variants:
        if v.variant_id not in seen:
            m = load_variant(cfg, v.variant_id)
            if m is not None:
                seen[v.variant_id] = m
    out = ["- base: the as-built model"]
    for m in seen.values():
        bits = [f"from {m.parent} with {m.inventory_items}"]
        if m.variables():
            bits.append("variables " + ", ".join(f"{x.name}_mm [{x.range[0]:g}, {x.range[1]:g}] (as built "
                                                 f"{x.as_built:g})" for x in m.variables()))
        if m.switches():
            bits.append("switches (variant_settings) " + ", ".join(f"{x.name} (as built {x.as_built:g})"
                                                                  for x in m.switches()))
        if m.parts:
            bits.append("new conductors, wired like plates when present: " + ", ".join(
                p.name + (f" (needs {p.present_when}=1)" if p.present_when else "") for p in m.parts))
        if m.removed_base:
            bits.append(f"removed: {m.removed_base}")
        if m.mesh_open_fraction is not None:
            bits.append(f"mesh transmission {m.mesh_open_fraction:g}")
        out.append(f"- {m.variant_id}: " + "; ".join(bits) + (f". {m.description}" if m.description else ""))
    return out


def inventory_block(cfg: Config) -> str:
    """Hypothetical parts the editor can build into a 2D variant (config/inventory.yaml)."""
    if not cfg.inventory.items:
        return "(empty: no geometry edits possible)"
    out = []
    for i in cfg.inventory.items:
        bits = [f"{i.kind}" + (f", replaces {i.replaces}" if i.replaces else "")]
        if i.parameters:
            bits.append("sweepable " + ", ".join(f"{k} [{v.range[0]:g}, {v.range[1]:g}]"
                                                 + (f" (as built {v.as_built:g})" if v.as_built is not None else "")
                                                 for k, v in i.parameters.items()))
        if i.transmission is not None:
            bits.append(f"transmission {i.transmission:g}")
        if i.connectable:
            bits.append("may be wired to an LV channel")
        out.append(f"- {i.id} ({'; '.join(bits)}): {' '.join(i.description.split())}")
    return "\n".join(out)


def variables_block(cfg: Config, c) -> str:
    """Optimizer variables and usable ranges of one configuration (for bounds)."""
    conf = to_configuration_def(c, "summary")
    try:
        rng = SearchSpace.from_config(cfg, conf).variable_ranges()
    except Exception as e:                                  # noqa: BLE001  (shown to the planner as is)
        return f"(configuration cannot be optimized: {e})"
    return ", ".join(f"{k} [{_fmt(lo, 4)}, {_fmt(hi, 4)}]" for k, (lo, hi) in rng.items())


# --------------------------------------------------------------------------- history


def config_str(c: dict | None) -> str:
    if not c:
        return "-"
    w = ",".join(f"{k}:{v}" for k, v in sorted(c.get("wiring", {}).items()) if v != "GND") or "all GND"
    extra = (f" removed {c['removed']}" if c.get("removed") else "") + \
            (f" moved {c['moved']}" if c.get("moved") else "") + \
            (f" variant {c['variant_id']}" if c.get("variant_id", "base") != "base" else "")
    return f"cfg {c.get('cfg')} [{w}]{extra}"


def history_block(state: LoopState) -> str:
    if not state.history:
        return "(no rounds yet)"
    rows = ["| round | action | diagnosis | configuration | bounds | solves | score | eta | feasible | critic |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for h in state.history:
        p = h.proposal
        b = ", ".join(f"{k} [{_fmt(v.lo, 4)}, {_fmt(v.hi, 4)}]" for k, v in (p.bounds if p else {}).items()) or "full"
        crit = (h.critic.verdict if h.critic else "-") + ("" if h.counted else " (excluded)")
        m = h.metrics or {}
        rows.append(f"| {h.round} | {p.action if p else '-'} | {p.diagnosis if p else '-'} | "
                    f"{config_str(p.configuration.model_dump() if p and p.configuration else None)} | {b} | "
                    f"{h.n_solves} | {_fmt(m.get('score'))} | {_fmt(m.get('eta'))} | {_fmt(m.get('feasible'))} | "
                    f"{crit} |")
    return "\n".join(rows)


def best_block(state: LoopState) -> str:
    b = state.best
    if not b:
        return "(no valid, feasible result accepted yet)"
    return (f"round {b.round}, job {b.job_id}: score {_fmt(b.score)} deg, eta {_fmt(b.eta)}, "
            f"{config_str(b.configuration)}")


def _study_rows(rl: RunLog, study_id: str, spec_hash: str) -> tuple[list[dict], bool]:
    """Valid runs of a study with metrics for the current spec; else the latest metrics of each job
    (second value False: scored under an older spec)."""
    rows = [r for r in rl.study_results(study_id, spec_hash) if r["valid"]]
    if rows:
        return rows, True
    rows = rl._rows(
        "SELECT j.job_id, m.valid, m.feasible, m.score, m.eta FROM jobs j JOIN metrics m ON m.job_id=j.job_id "
        "WHERE j.study_id=? AND m.rowid=(SELECT m2.rowid FROM metrics m2 WHERE m2.job_id=j.job_id "
        "ORDER BY m2.created_at DESC, m2.rowid DESC LIMIT 1)", (study_id,))
    rows = [r for r in rows if r["valid"]]
    rows.sort(key=lambda r: (not r["feasible"], r["score"] if r["score"] is not None else 1e9))
    return rows, False


def b0_block(cfg: Config) -> str:
    """Baseline B0 (the reference the agent must beat): the latest study of each b0_configs entry."""
    db = cfg.path("db_path")
    if not db.is_file():
        return "(no B0 results in the run log)"
    ids = {c.config_id: c for c in cfg.b0_configs.configurations}
    rows, settings, old_spec = [], [], False
    with RunLog(db) as rl:
        latest: dict[str, dict] = {}
        for s in rl._rows("SELECT * FROM studies ORDER BY started_at"):
            if s["config_id"] in ids:
                latest[s["config_id"]] = s
        for cid, s in latest.items():
            res, current = _study_rows(rl, s["study_id"], cfg.spec_hash())
            if not res:
                continue
            old_spec |= not current
            n_feas = sum(1 for r in res if r["feasible"])
            if n_feas:
                best = res[0]
                score, eta = _fmt(best["score"]), _fmt(best["eta"])
            else:       # an infeasible run's score is meaningless (tiny when almost no ions land)
                score, eta = "none feasible", f"max {_fmt(max((r['eta'] or 0.0) for r in res))}"
            rows.append(f"| {s['study_id']}{'' if current else ' *'} | {config_str(ids[cid].model_dump())} | "
                        f"{len(res)} | {n_feas} | {score} | {eta} |")
            pick = res[0] if n_feas else max(res, key=lambda r: r["eta"] or 0.0)
            settings.append(f"- {cid} ({'best feasible' if n_feas else 'highest-eta'} run {pick['job_id'][:8]}): "
                            + _settings_str(cfg, ids[cid], rl, pick["job_id"]))
    if not rows:
        return "(no B0 results in the run log)"
    head = ["| study | configuration | valid runs | feasible runs | best feasible score (deg) | its eta |",
            "|---|---|---|---|---|---|"]
    note = ["", "* scored under an earlier spec version (thresholds may differ); treat as indicative"] if old_spec else []
    tail = ["", "Settings of each study's best run, value [usable range] (V, mm):"] + settings if settings else []
    return "\n".join(head + rows + note + tail)


def _settings_str(cfg: Config, conf, rl: RunLog, job_id: str) -> str:
    """'LV1 164.6 [1, 300], ..., lens_gap_mm 37.77 [10, 53]' for a stored job (fixed positions left out)."""
    row = rl._rows("SELECT config_json FROM jobs WHERE job_id=?", (job_id,))
    if not row:
        return "(settings not in the run log)"
    j = json.loads(row[0]["config_json"])
    vals = {**j.get("channels", {}), **{f"{k}_mm": v / units.MM for k, v in j.get("positions", {}).items()}}
    try:
        rng = SearchSpace.from_config(cfg, conf).variable_ranges()
    except Exception:                                       # noqa: BLE001
        rng = {}
    out = []
    for k, v in vals.items():
        lo, hi = rng.get(k, (None, None))
        if lo is not None and lo == hi:
            continue
        out.append(f"{k} {_fmt(v, 4)}" + (f" [{_fmt(lo, 4)}, {_fmt(hi, 4)}]" if lo is not None else ""))
    return ", ".join(out)


# --------------------------------------------------------------------------- prompts


def planner_context(cfg: Config, acfg: AgentsConfig, state: LoopState, last_metrics: dict | None) -> str:
    b, lp = state.budget, acfg.loop
    last = state.history[-1] if state.history else None
    lo_b, hi_b = min(lp.study_budget_min, b.solves_left), min(lp.study_budget_max, b.solves_left)
    parts = [
        "# Specification\n" + spec_block(cfg),
        "# Design space\n" + design_space_block(cfg, state),
        "# Baseline B0 (fixed hand-made configurations, same optimizer)\n" + b0_block(cfg),
        "# Inventory (hypothetical parts we could order; action edit_then_optimize builds them into a 2D model "
        "variant, the author approves it)\n" + inventory_block(cfg),
        "# Rounds so far\n" + history_block(state),
        "# Best so far\n" + best_block(state),
        f"# Budget\n- solves used {b.solves_used} of {b.solves_total} ({b.solves_left} left); round "
        f"{b.rounds_used + 1} of {b.round_cap}\n- solve_budget for this round: {lo_b} to {hi_b}\n"
        f"- each bound must span at least {lp.min_bound_fraction:.0%} of the variable's usable range\n"
        f"- the loop stops after {lp.no_improvement_rounds} rounds without improving the best score by more "
        f"than {lp.improvement_tol_deg} deg",
    ]
    if state.goal:
        parts.insert(0, "# Author's goal for this run\n" + state.goal + "\n(A direction to explore, not a new "
                     "requirement: the specification still decides what counts as better. Report honestly if the "
                     "results argue against it, and stop pursuing it when they do.)")
    if last is not None:
        parts.append("# Last round's best result\n" + metrics_block(last_metrics or last.metrics))
        if last.critic:
            c = last.critic
            checks = "; ".join(f"{x.claim_id}: {x.status} ({x.evidence})" for x in c.claim_checks)
            parts.append(f"# Critic verdict on the last round: {c.verdict}\n- reasons: {c.reasons}\n"
                         f"- claim checks: {checks or '-'}\n- failure modes: {'; '.join(c.observed_failure_modes) or '-'}"
                         f"\n- suggestions: {'; '.join(c.suggestions) or '-'}")
        if last.proposal and last.proposal.configuration:
            parts.append("# Optimizer variables of the last configuration (usable ranges)\n"
                         + variables_block(cfg, last.proposal.configuration))
    if state.pending.feedback:
        parts.append("# Feedback on your previous proposal (fix this)\n" +
                     "\n".join(f"- {f}" for f in state.pending.feedback))
    return "\n\n".join(parts)


def critic_context(cfg: Config, state: LoopState, metrics: dict | None, study_line: str,
                   evidence_files: list[str]) -> str:
    p = state.pending.proposal
    claims = "\n".join(f"- {c.id}: {c.statement} (evidence: {c.evidence_needed})" for c in (p.claims if p else [])) \
        or "(no claims)"
    files = "\n".join(f"- {f}" for f in evidence_files) or "(none)"
    return "\n\n".join([
        "# Specification\n" + spec_block(cfg),
        "# What was run\n" + (f"- {config_str(p.configuration.model_dump())}\n" if p and p.configuration else "")
        + study_line,
        "# Checker output for the best job\n" + metrics_block(metrics_summary(metrics)),
        "# Full metrics.json\n```json\n" + json.dumps(metrics_summary(metrics, n_rows=26), indent=0) + "\n```",
        "# Planner claims to check\n" + claims,
        "# Evidence files you can Read (plots of the best job)\n" + files,
    ])


def evidence_files(job_dir: Path) -> list[Path]:
    plots = job_dir / "plots"
    return sorted(plots.glob("*.png")) if plots.is_dir() else []
