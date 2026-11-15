"""Supply-channel wiring, fixed-stack geometry, validation and expansion into model parameters.

Hardware (plan 7.2, reworked for the real assembly, KNOWN_ISSUES #10): a stack of nine plates
E1..E9 (= L1..L9 in the models, E1 = extractor) plus two split deflectors, placed by lens_gap (tip
apex to the E1 front face). As built, every part is present at its CAD position. A configuration
may leave out parts in constraints.electrodes.removable (JobSpec.removed) and the optimizer may move
plates in electrodes.movable (positions e<k>_offset = front face from the E1 front face), keeping
electrodes.min_gap_mm between the facing surfaces of neighbours (author 2026-11-15).

The optimizer tunes supply *channels*; the wiring map assigns the tip and each electrode to an
LV channel or GND (nodes not listed are GND), which makes the four-supply limit impossible to
violate. HV ports have fixed roles (constraints.supplies.high_voltage.roles). Deflectors are
grounded in Phase 1 (constraints.electrodes.deflectors_grounded).

Validation returns warnings for checks that cannot run because a limit is still TBD;
hard violations raise :class:`JobValidationError` listing every problem.
"""
from __future__ import annotations

import math
from typing import Any, Iterable

from . import units
from .config import Config, TBDError, range_known
from .schemas import JobSpec
from .variants import load_variant, present_parts, registry as variant_registry

GND = "GND"
EPS_M = 1e-12          # numerical slack for position comparisons (m)
POSITIONS = ("lens_gap", "z_mcp", "mesh_gap")
OFFSET = "_offset"     # positions key suffix of a moved plate: e3_offset (m, front face from the E1 front face)

# r-z shapes of the stack parts (scripts/build_axisym.py profile() and DEFLECTORS), as radial bands
# (r_lo, r_hi, front_dz, back_dz) in mm: where the solid starts and ends along z in each band,
# relative to the part's front face. Bands cover r 5..32.5 (aperture to outer radius).
PROFILES: dict[str, list[tuple[float, float, float, float]]] = {
    # 9 mm plate, front groove r 10..15 (5 deep), back lip r 12..13 (5 long)
    "lens": [(5, 10, 0, 9), (10, 12, 5, 9), (12, 13, 5, 14), (13, 15, 5, 9), (15, 32.5, 0, 9)],
    # 10 mm plate: front recess r < 15 (7 deep), 1 mm web, back recess r < 12, lip r 12..13 (to 15)
    "accel": [(5, 12, 7, 8), (12, 13, 7, 15), (13, 15, 7, 10), (15, 32.5, 0, 10)],
    # split-cylinder pair as one body: tube r 5..6.5 (12.77 long), plates from 0.77 to 12.0
    "deflector": [(5, 6.5, 0, 12.77), (6.5, 32.5, 0.77, 12.0)],
}


class JobValidationError(ValueError):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("invalid job:\n  " + "\n  ".join(problems))


def electrode_names(cfg: Config) -> list[str]:
    return [f"e{k}" for k in range(1, cfg.constraints.electrodes.count + 1)]


def deflector_halves(cfg: Config, chamber: int) -> list[str]:
    """Deflector half names present in a chamber setup (d1a, d1b, ...)."""
    return [f"{d.name}{h}" for d in cfg.constraints.electrodes.deflectors if chamber in d.cfgs for h in "ab"]


# --------------------------------------------------------------------------- structure


def check_structure(cfg: Config, chamber: int, wiring: dict[str, str], removed: Iterable[str] = (),
                    variant_id: str = "base", variant_settings: dict[str, float] | None = None) -> list[str]:
    """Problems with a configuration's chamber setup, wiring map, removed parts and variant."""
    p: list[str] = []
    try:
        var = load_variant(cfg, variant_id)
    except Exception as e:                                  # noqa: BLE001
        return [str(e)]
    settings = variant_settings or {}
    if var is not None:
        sw = {x.name for x in var.switches()}
        p += [f"variant {variant_id} has no switch '{k}' (switches: {sorted(sw)})" for k in settings if k not in sw]
        p += [f"variant switch {k} must be 0 or 1" for k, v in settings.items() if k in sw and v not in (0, 1)]
    elif settings:
        p.append("variant_settings given for the base model")
    extra_nodes = [x.name for x in present_parts(var, settings) if x.connectable]
    wired_removed = sorted(n for n in removed if wiring.get(n, GND) != GND)
    if wired_removed:
        p.append(f"removed parts cannot be wired: {wired_removed}")
    cs = cfg.constraints
    if chamber not in cs.chamber_setups:
        p.append(f"cfg {chamber} is not a chamber setup {sorted(cs.chamber_setups)}")
    lv = cs.supplies.low_voltage
    hv_ports = set(cs.supplies.high_voltage.roles)
    not_conn = sorted(set(wiring) - set(lv.connectable) - set(extra_nodes))
    if not_conn:
        p.append(f"not connectable to LV supplies: {not_conn} (connectable: {lv.connectable + extra_nodes})")
    allowed = set(lv.channels) | {GND}
    for node, ch in wiring.items():
        if ch in hv_ports:
            p.append(f"{node} -> {ch}: HV ports have fixed roles and cannot be wired to the tip or electrodes")
        elif ch not in allowed:
            p.append(f"{node} -> {ch}: must be one of {sorted(allowed)}")
    return p


def used_lv_channels(cfg: Config, wiring: dict[str, str]) -> list[str]:
    """LV channels referenced by a wiring map, in the order of constraints.supplies.low_voltage.channels."""
    return [c for c in cfg.constraints.supplies.low_voltage.channels if c in set(wiring.values())]


# --------------------------------------------------------------------------- geometry


def stack_layout(cfg: Config, chamber: int, lens_gap_m: float, removed: Iterable[str] = (),
                 offsets: dict[str, float] | None = None) -> list[dict]:
    """Present plates and deflectors in plan coordinates (m), in beam order.

    removed: parts left out; offsets: plate name -> front face from the E1 front face (m), others as built.
    Each entry: name, selection, kind (electrode | deflector), profile, z_front_m, z_back_m (incl. lips),
    z_plate_back_m (plate only), r_in_m, r_out_m.
    """
    el = cfg.constraints.electrodes
    if not el.stack:
        raise TBDError("constraints.electrodes.stack")
    removed, offsets = set(removed), offsets or {}
    out = []
    for k, s in enumerate(el.stack, start=1):
        name = f"e{k}"
        if name in removed:
            continue
        z0 = lens_gap_m + offsets.get(name, s.front_mm * units.MM)
        out.append({"name": name, "selection": f"sel_{name}", "kind": "electrode", "profile": s.profile,
                    "z_front_m": z0, "z_back_m": z0 + s.length_mm * units.MM,
                    "z_plate_back_m": z0 + (s.plate_mm or s.length_mm) * units.MM,
                    "r_in_m": s.r_in_mm * units.MM, "r_out_m": s.r_out_mm * units.MM})
    for d in el.deflectors:
        if chamber in d.cfgs and d.name not in removed:
            z0 = lens_gap_m + d.front_mm * units.MM
            out.append({"name": d.name, "selection": f"sel_{d.name}", "kind": "deflector", "profile": d.profile,
                        "z_front_m": z0, "z_back_m": z0 + d.length_mm * units.MM,
                        "z_plate_back_m": z0 + d.length_mm * units.MM,
                        "r_in_m": d.r_in_mm * units.MM, "r_out_m": d.r_out_mm * units.MM})
    return out


def job_offsets(job: JobSpec) -> dict[str, float]:
    """Moved plates of a job: name -> front face from the E1 front face (m)."""
    return {k[: -len(OFFSET)]: v for k, v in job.positions.items() if k.endswith(OFFSET)}


def job_layout(job: JobSpec, cfg: Config) -> list[dict]:
    return stack_layout(cfg, job.cfg, job.positions["lens_gap"], job.removed, job_offsets(job))


def nominal_offset(cfg: Config, plate: str) -> float:
    """As-built front face of a plate from the E1 front face (m)."""
    return cfg.constraints.electrodes.stack[int(plate[1:]) - 1].front_mm * units.MM


def face_shift(profile_a: str, profile_b: str) -> float:
    """Smallest gap (m) between part a's back surface and part b's front surface when b's front face is
    exactly at a's front face; the actual gap is this plus (b front - a front)."""
    best = math.inf
    for lo_a, hi_a, _, back_a in PROFILES[profile_a]:
        for lo_b, hi_b, front_b, _ in PROFILES[profile_b]:
            if min(hi_a, hi_b) - max(lo_a, lo_b) > 1e-9:          # radial bands overlap
                best = min(best, front_b - back_a)
    return best * units.MM


def part_gap(a: dict, b: dict) -> float:
    """Smallest axial gap (m) between neighbouring stack parts a (upstream) and b (stack_layout entries)."""
    return b["z_front_m"] - a["z_front_m"] + face_shift(a["profile"], b["profile"])


def layout_problems(cfg: Config, chamber: int, removed: Iterable[str], offsets: dict[str, float]) -> list[str]:
    """Removed / moved parts against constraints.electrodes: allowed lists, overlaps, max offset."""
    el = cfg.constraints.electrodes
    removed, p = list(removed), []
    exist = {f"e{k}" for k in range(1, el.count + 1)} | {d.name for d in el.deflectors if chamber in d.cfgs}
    not_allowed = sorted(set(removed) - set(el.removable))
    if not_allowed:
        p.append(f"cannot remove {not_allowed} (constraints.electrodes.removable: {el.removable})")
    absent = sorted(set(removed) - exist - set(not_allowed))
    if absent:
        p.append(f"cannot remove {absent}: not in the stack of cfg {chamber}")
    fixed = sorted(set(offsets) - set(el.movable))
    if fixed:
        p.append(f"cannot move {fixed} (constraints.electrodes.movable: {el.movable})")
    both = sorted(set(offsets) & set(removed))
    if both:
        p.append(f"{both} both removed and moved")
    if p or not offsets:
        return p
    parts = stack_layout(cfg, chamber, 0.0, removed, offsets)
    g = el.min_gap_mm * units.MM
    for a, b in zip(parts, parts[1:]):
        if (a["name"] in offsets or b["name"] in offsets) and part_gap(a, b) < g - 1e-9:
            p.append(f"{a['name']}-{b['name']} gap {part_gap(a, b) / units.MM:.3f} mm < electrodes.min_gap_mm "
                     f"{el.min_gap_mm} (moved: {sorted(offsets)})")
    if el.max_offset_mm is not None:
        for e in parts:
            if e["name"] in offsets and e["z_back_m"] > el.max_offset_mm * units.MM + 1e-9:
                p.append(f"{e['name']} reaches {e['z_back_m'] / units.MM:.3f} mm > electrodes.max_offset_mm "
                         f"{el.max_offset_mm}")
    return p


def geometry_electrodes(job: JobSpec, cfg: Config) -> list[dict]:
    """geometry.json 'electrodes' entries (checker contract: name, selection, z_m centre,
    thickness_m, r_in_m, r_out_m) as bounding boxes of each present stack part."""
    return [{"name": e["name"], "selection": e["selection"], "kind": e["kind"],
             "z_m": 0.5 * (e["z_front_m"] + e["z_back_m"]), "thickness_m": e["z_back_m"] - e["z_front_m"],
             "r_in_m": e["r_in_m"], "r_out_m": e["r_out_m"]}
            for e in job_layout(job, cfg)]


# --------------------------------------------------------------------------- potentials


def variant_nodes(job: JobSpec, cfg: Config) -> list[str]:
    """Wiring nodes added by the job's variant (present parts)."""
    return [x.name for x in present_parts(load_variant(cfg, job.variant_id), job.variant_settings)]


def node_potentials(job: JobSpec, cfg: Config) -> dict[str, float]:
    """Potential (V) of the tip, every electrode e1..e9 and the variant's parts, from the wiring (unlisted = GND)."""
    out = {}
    for node in ["tip"] + electrode_names(cfg) + variant_nodes(job, cfg):
        ch = job.wiring.get(node, GND)
        out[node] = 0.0 if ch == GND else float(job.channels[ch])
    return out


def deflector_potentials(job: JobSpec, cfg: Config) -> dict[str, float]:
    """Potential of every deflector half present in the job's chamber setup."""
    if not cfg.constraints.electrodes.deflectors_grounded:
        raise NotImplementedError("deflector supplies are not modelled yet (deflectors_grounded must be true)")
    return {h: 0.0 for h in deflector_halves(cfg, job.cfg)}


def mirror_warnings(job: JobSpec, cfg: Config) -> list[str]:
    """Electrodes, deflectors or the mesh beyond the tip potential (above it for q > 0). By energy conservation
    the ions only keep a positive kinetic energy below V_tip (+ E0/q), so such a part reflects them."""
    q = 1 if job.launch.charge > 0 else -1
    pots = node_potentials(job, cfg)
    v_tip = pots.pop("tip")
    try:
        pots.update(deflector_potentials(job, cfg))
    except NotImplementedError:
        pass
    pots["mesh"] = float(job.channels[cfg.constraints.supplies.hv_port("mesh")])
    bad = {k: v for k, v in pots.items() if q * (v - v_tip) > 1e-9}
    if not bad:
        return []
    side = "above" if q > 0 else "below"
    return [f"{', '.join(f'{k} {v:+.0f} V' for k, v in bad.items())} {side} the tip ({v_tip:+.0f} V): "
            f"ions keep only E0 there or are reflected"]


def hv_potentials(job: JobSpec, cfg: Config) -> dict[str, float | None]:
    """mcp_front, mesh (optimizer variables) and mcp_back, phosphor (from detector offsets, None if TBD)."""
    s = cfg.constraints.supplies
    front = float(job.channels[s.hv_port("mcp_front")])
    mesh = float(job.channels[s.hv_port("mesh")])
    back = None if s.mcp_back_offset_V is None else front + s.mcp_back_offset_V
    phos = None if back is None or s.phosphor_offset_V is None else back + s.phosphor_offset_V
    return {"mcp_front": front, "mesh": mesh, "mcp_back": back, "phosphor": phos}


def _in(v: float, rng: list | None) -> bool:
    return rng[0] - 1e-9 <= v <= rng[1] + 1e-9


# --------------------------------------------------------------------------- full job validation


def validate_job(job: JobSpec, cfg: Config) -> list[str]:
    """Validate a job against the registry, wiring rules and constraints.

    Returns warnings (checks skipped because a limit is TBD). Raises JobValidationError.
    """
    problems = check_structure(cfg, job.cfg, job.wiring, job.removed, job.variant_id, job.variant_settings)
    warnings: list[str] = []
    if problems:
        raise JobValidationError(problems)
    var = load_variant(cfg, job.variant_id)
    var_vars = {x.name: x for x in var.variables()} if var else {}
    if problems:
        raise JobValidationError(problems)
    cs = cfg.constraints
    s = cs.supplies
    lv = s.low_voltage

    # ---- channels
    lv_used = used_lv_channels(cfg, job.wiring)
    hv_front, hv_mesh = s.hv_port("mcp_front"), s.hv_port("mesh")
    known = set(lv.channels) | set(s.high_voltage.roles)
    for ch in job.channels:
        if ch not in known:
            problems.append(f"unknown channel '{ch}'")
    for ch in lv_used + [hv_front, hv_mesh]:
        if ch not in job.channels:
            problems.append(f"channel {ch} has no voltage")
    for ch in set(job.channels) & set(lv.channels) - set(lv_used):
        warnings.append(f"channel {ch} has a voltage but nothing is wired to it")
    for ch in (s.hv_port("mcp_back"), s.hv_port("phosphor")):
        if ch in job.channels:
            problems.append(f"channel {ch} is set from detector offsets, not by the job")
    if problems:
        raise JobValidationError(problems)

    def rng_check(name, v, rng, key):
        if range_known(rng):
            if not _in(v, rng):
                problems.append(f"{name} = {v:g} V outside {key} {rng}")
        else:
            warnings.append(f"{name} not range-checked: {key} is TBD")

    for ch in lv_used:
        rng_check(ch, job.channels[ch], lv.range_V, "constraints.supplies.low_voltage.range_V")
    hv = hv_potentials(job, cfg)
    rng_check(f"{hv_front} (MCP front)", hv["mcp_front"], s.mcp_front_V, "constraints.supplies.mcp_front_V")
    rng_check(f"{hv_mesh} (mesh)", hv["mesh"], s.mesh_V, "constraints.supplies.mesh_V")
    for role in ("mcp_front", "mesh", "mcp_back", "phosphor"):
        if hv[role] is not None:
            rng_check(f"{s.hv_port(role)} ({role})", hv[role], s.high_voltage.range_V,
                      "constraints.supplies.high_voltage.range_V")

    # ---- positions (metres)
    missing = sorted(set(POSITIONS) - set(job.positions))
    extra = sorted(k for k in set(job.positions) - set(POSITIONS) if not k.endswith(OFFSET) and k not in var_vars)
    for name, x in var_vars.items():
        if name not in job.positions:
            problems.append(f"variant parameter {name} has no value (positions)")
        elif not (x.range[0] * units.MM - EPS_M <= job.positions[name] <= x.range[1] * units.MM + EPS_M):
            problems.append(f"{name} = {job.positions[name] / units.MM:g} mm outside its inventory range {x.range}")
    if missing:
        problems.append(f"positions missing {missing}")
    if extra:
        problems.append(f"unknown positions {extra} (known: {list(POSITIONS)} and e<k>{OFFSET} for moved plates)")
    if problems:
        raise JobValidationError(problems)
    problems += layout_problems(cfg, job.cfg, job.removed, job_offsets(job))
    if problems:
        raise JobValidationError(problems)

    ch = cfg.chamber(job.cfg)
    z_mcp, gap, lg = job.positions["z_mcp"], job.positions["mesh_gap"], job.positions["lens_gap"]
    z_mesh = z_mcp - gap

    def pos_check(name, v, rng_mm, key):
        if range_known(rng_mm):
            lo, hi = rng_mm[0] * units.MM, rng_mm[1] * units.MM
            if not (lo - EPS_M <= v <= hi + EPS_M):
                problems.append(f"{name} = {v / units.MM:g} mm outside {key} {rng_mm}")
        else:
            warnings.append(f"{name} not range-checked: {key} is TBD")

    key = f"constraints.chamber_setups.{job.cfg}"
    pos_check("z_mcp", z_mcp, ch.z_mcp_mm, f"{key}.z_mcp_mm")
    pos_check("mesh_gap", gap, ch.mesh_gap_mm, f"{key}.mesh_gap_mm")
    pos_check("lens_gap", lg, ch.lens_gap_mm, f"{key}.lens_gap_mm")
    if cs.mesh.min_gap_to_mcp_mm is None:
        warnings.append("mesh_gap lower bound not checked: constraints.mesh.min_gap_to_mcp_mm is TBD")
    elif gap < cs.mesh.min_gap_to_mcp_mm * units.MM - EPS_M:
        problems.append(f"mesh_gap {gap / units.MM:g} mm < constraints.mesh.min_gap_to_mcp_mm "
                        f"{cs.mesh.min_gap_to_mcp_mm}")
    if lg <= 0:
        problems.append("lens_gap must be > 0 (E1 would touch the tip apex)")
    parts = job_layout(job, cfg)
    last = max(parts, key=lambda e: e["z_back_m"])
    if last["z_back_m"] >= z_mesh - EPS_M:
        problems.append(f"the lens stack ends at {last['z_back_m'] / units.MM:g} mm ({last['name']}), "
                        f"at or past the mesh plane ({z_mesh / units.MM:g} mm)")

    # ---- arcing limit between neighbours (tip, plates, deflectors, mesh)
    emax = cs.electrical.max_field_kV_per_mm
    if emax is None:
        warnings.append("field limit not checked: constraints.electrical.max_field_kV_per_mm is TBD")
    else:
        pots = {**node_potentials(job, cfg), **{d: v for d, v in deflector_potentials(job, cfg).items()}}
        clr = cs.electrodes.clearance_mm
        chain = [("tip", 0.0, pots["tip"])]
        for e in parts:
            v = pots[e["name"]] if e["kind"] == "electrode" else max(
                (pots[h] for h in (e["name"] + "a", e["name"] + "b")), key=abs)
            chain.append((e["name"], e["z_front_m"], v))
        chain.append(("mesh", z_mesh, hv["mesh"]))
        for i, ((n1, z1, v1), (n2, z2, v2)) in enumerate(zip(chain, chain[1:])):
            if n1 == "tip":
                d_mm = (z2 - z1) / units.MM
            elif n2 == "mesh":
                d_mm = (z2 - parts[i - 1]["z_back_m"]) / units.MM
            else:
                axial = (parts[i]["z_front_m"] - parts[i - 1]["z_back_m"]) / units.MM
                if axial > 0:            # parts do not nest: the axial gap is the distance
                    d_mm = axial
                elif clr is None:
                    warnings.append(f"field {n1}-{n2} not checked: constraints.electrodes.clearance_mm is TBD")
                    continue
                else:                    # nested lip/groove: CAD clearance
                    d_mm = clr
            if d_mm > 0:
                e = abs(v2 - v1) / 1000 / d_mm
                if e > emax:
                    problems.append(f"field between {n1} and {n2} is {e:.3g} kV/mm > max_field_kV_per_mm {emax}")
    if problems:
        raise JobValidationError(problems)
    return warnings


# --------------------------------------------------------------------------- expansion


def expand(job: JobSpec, cfg: Config) -> dict[str, Any]:
    """Model parameters (registry names, SI values) for a validated job.

    Unlisted electrodes and GND are 0 V. Deflector halves are 0 V (Phase 1); halves that do
    not exist in the job's chamber setup are set to 0 V too, so stale values never leak.
    v_mcp_back / v_phosphor are included only when their offsets are set. Ion species and
    tracing time come from the job's launch section.
    """
    reg = cfg.registry()
    pots = node_potentials(job, cfg)
    hv = hv_potentials(job, cfg)
    la = job.launch
    if la.t_end_us is None:
        raise TBDError("spec.launch.t_end_us")
    t_end = la.t_end_us * units.US
    p: dict[str, Any] = {
        "cfg": job.cfg,
        "z_mcp": job.positions["z_mcp"],
        "mesh_gap": job.positions["mesh_gap"],
        "lens_gap": job.positions["lens_gap"],
        "v_tip": model_tip_potential(job, cfg),
        "v_mesh": hv["mesh"],
        "v_mcp_front": hv["mcp_front"],
        "ion_mass": la.mass_Da * units.DALTON,
        "ion_charge": int(la.charge),
        "t_end": t_end,
        "dt_out": t_end / cfg.backend.worker.output_steps,
    }
    if hv["mcp_back"] is not None:
        p["v_mcp_back"] = hv["mcp_back"]
    if hv["phosphor"] is not None:
        p["v_phosphor"] = hv["phosphor"]
    for name in electrode_names(cfg):
        p[f"v_{name}"] = pots[name]
    defl = deflector_potentials(job, cfg)
    for d in cfg.constraints.electrodes.deflectors:
        for h in "ab":
            p[f"v_{d.name}{h}"] = defl.get(f"{d.name}{h}", 0.0)
    p.update(layout_params(job, cfg))
    var = load_variant(cfg, job.variant_id)
    if var is not None:
        reg = {**reg, **variant_registry(var)}
        for x in var.parameters:
            p[x.name] = job.positions[x.name] if x.role == "variable" else int(job.variant_settings.get(x.name, x.as_built))
        for part in var.parts:
            p[f"v_{part.name}"] = pots.get(part.name, 0.0)
    unknown = sorted(set(p) - set(reg))
    if unknown:
        raise ValueError(f"expanded parameters not in the registry: {unknown}")
    return p


def layout_params(job: JobSpec, cfg: Config) -> dict[str, Any]:
    """on_<part> (1 present, 0 removed) and dz_e<k> (shift from the as-built position, m) for every part.

    As built (all 1, all 0) these equal the registry defaults, so models without the switches still run
    such jobs (the worker skips a missing parameter only at its default value).
    """
    removed, off = set(job.removed), job_offsets(job)
    p: dict[str, Any] = {}
    for name in electrode_names(cfg):
        p[f"on_{name}"] = 0 if name in removed else 1
        p[f"dz_{name}"] = off[name] - nominal_offset(cfg, name) if name in off else 0.0
    for d in cfg.constraints.electrodes.deflectors:
        p[f"on_{d.name}"] = 0 if d.name in removed else 1
    return p


def expected_potentials(job: JobSpec, cfg: Config) -> dict[str, float]:
    """Assigned potential per named selection (plan section 8 names), for the checker."""
    pots = node_potentials(job, cfg)
    hv = hv_potentials(job, cfg)
    out = {"sel_tip": model_tip_potential(job, cfg)}
    removed = set(job.removed)
    for name in electrode_names(cfg):
        if name not in removed:
            out[f"sel_{name}"] = pots[name]
    var = load_variant(cfg, job.variant_id)
    for part in present_parts(var, job.variant_settings):
        out[f"sel_{part.name}"] = pots.get(part.name, 0.0)
    defl = deflector_potentials(job, cfg)
    for d in cfg.constraints.electrodes.deflectors:
        if job.cfg in d.cfgs and d.name not in removed:
            # one value per deflector (2D models the pair as one ring at the mean of its halves)
            out[f"sel_{d.name}"] = 0.5 * (defl[d.name + "a"] + defl[d.name + "b"])
    if not (var and "screen_mesh" in var.removed_base):
        out["sel_mesh_plane"] = hv["mesh"]
        out["sel_mesh_frame"] = hv["mesh"]
    out["sel_mcp_face"] = hv["mcp_front"]
    return out


def launch_preaccel(job: JobSpec, cfg: Config) -> dict:
    """Pre-acceleration for this job (launch.preacceleration): tip vs extractor E1, gap = lens_gap.

    Returns {'preaccel_eV': 0.0} when job.launch.preaccel is off.
    """
    if not job.launch.preaccel:
        return {"preaccel_eV": 0.0}
    from .launch import preacceleration  # noqa: PLC0415
    pots = node_potentials(job, cfg)
    return preacceleration(job.launch, pots["tip"], pots["e1"], job.positions["lens_gap"])


def job_launch(job: JobSpec, cfg: Config):
    """Launch table for a job and its pre-acceleration record (meta['preacceleration']).

    With spec.launch.emission_angle_at = 'meniscus' the record also holds the angle map
    (theta at the meniscus -> theta at the launch point, in degrees, for each meniscus energy).
    """
    from .launch import make_launch, meniscus_angle_map  # noqa: PLC0415
    pre = launch_preaccel(job, cfg)
    amap = meniscus_angle_map(job.launch, pre) if job.launch.preaccel else None
    ions = make_launch(job.launch, job.fidelity, job.ion_level, preaccel_eV=pre["preaccel_eV"], angle_map=amap)
    if amap is not None:
        pre = {**pre, "emission_angle_at": "meniscus", "angle_map_deg": {
            f"{e - pre['preaccel_eV']:.6g} eV": {f"{t:g}": round(float(tl), 4) for t, tl in g[["theta_deg", "theta_launch_deg"]]
                                                .drop_duplicates().itertuples(index=False)}
            for e, g in ions.groupby("KE0_eV")}}
    return ions, pre


def model_tip_potential(job: JobSpec, cfg: Config) -> float:
    """Potential the MODEL tip is held at.

    Without pre-acceleration: the tip supply voltage. With it, V_tip - gain/q: the model needle
    then stands for the real emitter's equipotential at the emission distance s (where the
    pre-accelerated ions are launched), so total energy E0 + q V_tip is conserved along the path.
    """
    v = node_potentials(job, cfg)["tip"]
    gain = launch_preaccel(job, cfg)["preaccel_eV"]
    return v - gain / job.launch.charge
