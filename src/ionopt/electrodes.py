"""Supply-channel wiring, fixed-stack geometry, validation and expansion into model parameters.

Hardware (plan 7.2, reworked for the real assembly, KNOWN_ISSUES #10): a FIXED stack of nine
plates E1..E9 (= L1..L9 in the models, E1 = extractor) plus two split deflectors, placed as one
unit by lens_gap (tip apex to the E1 front face). Every plate is always present.

The optimizer tunes supply *channels*; the wiring map assigns the tip and each electrode to an
LV channel or GND (nodes not listed are GND), which makes the four-supply limit impossible to
violate. HV ports have fixed roles (constraints.supplies.high_voltage.roles). Deflectors are
grounded in Phase 1 (constraints.electrodes.deflectors_grounded).

Validation returns warnings for checks that cannot run because a limit is still TBD;
hard violations raise :class:`JobValidationError` listing every problem.
"""
from __future__ import annotations

from typing import Any

from . import units
from .config import Config, TBDError, range_known
from .schemas import JobSpec

GND = "GND"
EPS_M = 1e-12          # numerical slack for position comparisons (m)
POSITIONS = ("lens_gap", "z_mcp", "mesh_gap")


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


def check_structure(cfg: Config, chamber: int, wiring: dict[str, str]) -> list[str]:
    """Problems with a configuration's chamber setup and wiring map."""
    p: list[str] = []
    cs = cfg.constraints
    if chamber not in cs.chamber_setups:
        p.append(f"cfg {chamber} is not a chamber setup {sorted(cs.chamber_setups)}")
    lv = cs.supplies.low_voltage
    hv_ports = set(cs.supplies.high_voltage.roles)
    not_conn = sorted(set(wiring) - set(lv.connectable))
    if not_conn:
        p.append(f"not connectable to LV supplies: {not_conn} (connectable: {lv.connectable})")
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


def stack_layout(cfg: Config, chamber: int, lens_gap_m: float) -> list[dict]:
    """Plates and deflectors of the fixed stack in plan coordinates (m), in beam order.

    Each entry: name, selection, kind (electrode | deflector), z_front_m, z_back_m (incl. lips),
    z_plate_back_m (plate only), r_in_m, r_out_m.
    """
    el = cfg.constraints.electrodes
    if not el.stack:
        raise TBDError("constraints.electrodes.stack")
    out = []
    for k, s in enumerate(el.stack, start=1):
        z0 = lens_gap_m + s.front_mm * units.MM
        out.append({"name": f"e{k}", "selection": f"sel_e{k}", "kind": "electrode", "z_front_m": z0,
                    "z_back_m": z0 + s.length_mm * units.MM,
                    "z_plate_back_m": z0 + (s.plate_mm or s.length_mm) * units.MM,
                    "r_in_m": s.r_in_mm * units.MM, "r_out_m": s.r_out_mm * units.MM})
    for d in el.deflectors:
        if chamber in d.cfgs:
            z0 = lens_gap_m + d.front_mm * units.MM
            out.append({"name": d.name, "selection": f"sel_{d.name}", "kind": "deflector", "z_front_m": z0,
                        "z_back_m": z0 + d.length_mm * units.MM, "z_plate_back_m": z0 + d.length_mm * units.MM,
                        "r_in_m": d.r_in_mm * units.MM, "r_out_m": d.r_out_mm * units.MM})
    return out


def geometry_electrodes(job: JobSpec, cfg: Config) -> list[dict]:
    """geometry.json 'electrodes' entries (checker contract: name, selection, z_m centre,
    thickness_m, r_in_m, r_out_m) as bounding boxes of each stack part."""
    return [{"name": e["name"], "selection": e["selection"], "kind": e["kind"],
             "z_m": 0.5 * (e["z_front_m"] + e["z_back_m"]), "thickness_m": e["z_back_m"] - e["z_front_m"],
             "r_in_m": e["r_in_m"], "r_out_m": e["r_out_m"]}
            for e in stack_layout(cfg, job.cfg, job.positions["lens_gap"])]


# --------------------------------------------------------------------------- potentials


def node_potentials(job: JobSpec, cfg: Config) -> dict[str, float]:
    """Potential (V) of the tip and every electrode e1..e9, from the wiring (unlisted = GND)."""
    out = {}
    for node in ["tip"] + electrode_names(cfg):
        ch = job.wiring.get(node, GND)
        out[node] = 0.0 if ch == GND else float(job.channels[ch])
    return out


def deflector_potentials(job: JobSpec, cfg: Config) -> dict[str, float]:
    """Potential of every deflector half present in the job's chamber setup."""
    if not cfg.constraints.electrodes.deflectors_grounded:
        raise NotImplementedError("deflector supplies are not modelled yet (deflectors_grounded must be true)")
    return {h: 0.0 for h in deflector_halves(cfg, job.cfg)}


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
    problems = check_structure(cfg, job.cfg, job.wiring)
    warnings: list[str] = []
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
    extra = sorted(set(job.positions) - set(POSITIONS))
    if missing:
        problems.append(f"positions missing {missing}")
    if extra:
        problems.append(f"unknown positions {extra} (the stack is fixed; only {list(POSITIONS)})")
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
    parts = stack_layout(cfg, job.cfg, lg)
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
    unknown = sorted(set(p) - set(reg))
    if unknown:
        raise ValueError(f"expanded parameters not in the registry: {unknown}")
    return p


def expected_potentials(job: JobSpec, cfg: Config) -> dict[str, float]:
    """Assigned potential per named selection (plan section 8 names), for the checker."""
    pots = node_potentials(job, cfg)
    hv = hv_potentials(job, cfg)
    out = {"sel_tip": model_tip_potential(job, cfg)}
    for name in electrode_names(cfg):
        out[f"sel_{name}"] = pots[name]
    defl = deflector_potentials(job, cfg)
    for d in cfg.constraints.electrodes.deflectors:
        if job.cfg in d.cfgs:
            # one value per deflector (2D models the pair as one ring at the mean of its halves)
            out[f"sel_{d.name}"] = 0.5 * (defl[d.name + "a"] + defl[d.name + "b"])
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


def model_tip_potential(job: JobSpec, cfg: Config) -> float:
    """Potential the MODEL tip is held at.

    Without pre-acceleration: the tip supply voltage. With it, V_tip - gain/q: the model needle
    then stands for the real emitter's equipotential at the emission distance s (where the
    pre-accelerated ions are launched), so total energy E0 + q V_tip is conserved along the path.
    """
    v = node_potentials(job, cfg)["tip"]
    gain = launch_preaccel(job, cfg)["preaccel_eV"]
    return v - gain / job.launch.charge
