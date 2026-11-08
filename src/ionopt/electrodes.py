"""Supply-channel wiring: validation and expansion into model parameters (plan 7.2, 7.3).

The optimizer tunes supply *channels*; the wiring map assigns the tip and each used
electrode to an LV channel or GND, which makes the four-supply limit impossible to
violate. HV ports have fixed roles (constraints.supplies.high_voltage.roles).

Validation returns warnings for checks that cannot run because a limit is still TBD;
hard violations raise :class:`JobValidationError` listing every problem.
"""
from __future__ import annotations

from typing import Any

from . import units
from .config import Config, range_known
from .schemas import JobSpec

GND = "GND"
EPS_M = 1e-12          # numerical slack for position comparisons (m)


class JobValidationError(ValueError):
    def __init__(self, problems: list[str]):
        self.problems = problems
        super().__init__("invalid job:\n  " + "\n  ".join(problems))


def _mm(x):
    return None if x is None else x * units.MM


# --------------------------------------------------------------------------- structure


def check_structure(cfg: Config, chamber: int, electrodes_used: list[int], wiring: dict[str, str]) -> list[str]:
    """Problems with a configuration's chamber setup, electrodes used and wiring map."""
    p: list[str] = []
    cs = cfg.constraints
    if chamber not in cs.chamber_setups:
        p.append(f"cfg {chamber} is not a chamber setup {sorted(cs.chamber_setups)}")
    n = cs.electrodes.count
    used = list(electrodes_used)
    if 1 not in used:
        p.append("E1 (extractor) must be used")
    bad = [k for k in used if not (isinstance(k, int) and 1 <= k <= n)]
    if bad:
        p.append(f"electrode numbers must be 1..{n}: {bad}")
    if len(set(used)) != len(used):
        p.append(f"electrodes_used has duplicates: {used}")
    if used != sorted(used):
        p.append(f"electrodes_used must be in increasing order: {used}")

    lv = cs.supplies.low_voltage
    hv_ports = set(cs.supplies.high_voltage.roles)
    need = {"tip"} | {f"e{k}" for k in used}
    missing = sorted(need - set(wiring))
    extra = sorted(set(wiring) - need)
    if missing:
        p.append(f"wiring is missing {missing} (tip and every used electrode need a channel or GND)")
    if extra:
        p.append(f"wiring assigns {extra}, which are not the tip or a used electrode")
    not_conn = sorted(set(wiring) - set(lv.connectable))
    if not_conn:
        p.append(f"not connectable to LV supplies: {not_conn}")
    allowed = set(lv.channels) | {GND}
    for node, ch in wiring.items():
        if ch in hv_ports:
            p.append(f"{node} -> {ch}: HV ports have fixed roles and cannot be wired to the tip or electrodes")
        elif ch not in allowed:
            p.append(f"{node} -> {ch}: must be one of {sorted(allowed)}")
    distinct = {ch for ch in wiring.values() if ch in lv.channels}
    if len(distinct) > len(lv.channels):
        p.append(f"uses {len(distinct)} LV channels; only {len(lv.channels)} exist")
    return p


def used_lv_channels(cfg: Config, wiring: dict[str, str]) -> list[str]:
    """LV channels referenced by a wiring map, in the order of constraints.supplies.low_voltage.channels."""
    return [c for c in cfg.constraints.supplies.low_voltage.channels if c in set(wiring.values())]


# --------------------------------------------------------------------------- potentials


def node_potentials(job: JobSpec, cfg: Config) -> dict[str, float]:
    """Potential (V) of the tip and each used electrode, from the wiring and channel voltages."""
    out = {}
    for node, ch in job.wiring.items():
        out[node] = 0.0 if ch == GND else float(job.channels[ch])
    return out


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
    problems = check_structure(cfg, job.cfg, job.electrodes_used, job.wiring)
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
    used = job.electrodes_used
    need = {"z_mcp", "mesh_gap"} | {f"z_e{k}" for k in used}
    missing = sorted(need - set(job.positions))
    extra = sorted(set(job.positions) - need)
    if missing:
        problems.append(f"positions missing {missing}")
    if extra:
        problems.append(f"positions given for {extra} (removed electrodes have no position)")
    if problems:
        raise JobValidationError(problems)

    ch = cfg.chamber(job.cfg)
    z_mcp, gap = job.positions["z_mcp"], job.positions["mesh_gap"]
    z_mesh = z_mcp - gap
    zs = [job.positions[f"z_e{k}"] for k in used]

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
    if cs.mesh.min_gap_to_mcp_mm is None:
        warnings.append("mesh_gap lower bound not checked: constraints.mesh.min_gap_to_mcp_mm is TBD")
    elif gap < cs.mesh.min_gap_to_mcp_mm * units.MM - EPS_M:
        problems.append(f"mesh_gap {gap / units.MM:g} mm < constraints.mesh.min_gap_to_mcp_mm "
                        f"{cs.mesh.min_gap_to_mcp_mm}")
    pos_check("z_e1", job.positions["z_e1"], cs.electrodes.e1_z_mm, "constraints.electrodes.e1_z_mm")
    for k, z in zip(used, zs):
        pos_check(f"z_e{k}", z, ch.electrode_z_mm, f"{key}.electrode_z_mm")

    t = _mm(cs.electrodes.thickness_mm)
    g = _mm(cs.electrodes.min_gap_mm)
    if t is None or g is None:
        warnings.append("electrode spacing not checked: constraints.electrodes.thickness_mm/min_gap_mm is TBD")
    half = (t or 0.0) / 2
    for (k1, z1), (k2, z2) in zip(zip(used, zs), zip(used[1:], zs[1:])):
        if z2 <= z1:
            problems.append(f"z_e{k2} must be larger than z_e{k1} (positions increase with k)")
        elif t is not None and g is not None and (z2 - z1 - t) < g - EPS_M:
            problems.append(f"gap between E{k1} and E{k2} is {(z2 - z1 - t) / units.MM:g} mm "
                            f"< min_gap_mm {cs.electrodes.min_gap_mm}")
    if zs and zs[-1] + half >= z_mesh - EPS_M:
        problems.append(f"last electrode E{used[-1]} reaches the mesh plane (z_mesh = {z_mesh / units.MM:g} mm)")
    if zs and zs[0] - half <= 0:
        problems.append("E1 overlaps the tip apex (z <= 0)")

    # ---- arcing limit between neighbours (tip, used electrodes, mesh)
    emax = cs.electrical.max_field_kV_per_mm
    if emax is None:
        warnings.append("field limit not checked: constraints.electrical.max_field_kV_per_mm is TBD")
    else:
        pots = node_potentials(job, cfg)
        chain = [("tip", 0.0, 0.0, pots["tip"])] + \
                [(f"e{k}", z - half, z + half, pots[f"e{k}"]) for k, z in zip(used, zs)] + \
                [("mesh", z_mesh, z_mesh, hv["mesh"])]
        for (n1, _, b1, v1), (n2, a2, _, v2) in zip(chain, chain[1:]):
            d_mm = (a2 - b1) / units.MM
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

    GND and unused electrodes are 0 V; unused electrodes get use_e<k> = False and no
    position. v_mcp_back / v_phosphor are included only when their offsets are set.
    """
    reg = cfg.registry()
    n = cfg.constraints.electrodes.count
    pots = node_potentials(job, cfg)
    hv = hv_potentials(job, cfg)
    p: dict[str, Any] = {
        "cfg": job.cfg,
        "z_mcp": job.positions["z_mcp"],
        "mesh_gap": job.positions["mesh_gap"],
        "v_tip": pots["tip"],
        "v_mesh": hv["mesh"],
        "v_mcp_front": hv["mcp_front"],
    }
    if hv["mcp_back"] is not None:
        p["v_mcp_back"] = hv["mcp_back"]
    if hv["phosphor"] is not None:
        p["v_phosphor"] = hv["phosphor"]
    for k in range(1, n + 1):
        on = k in job.electrodes_used
        p[f"use_e{k}"] = on
        p[f"v_e{k}"] = pots[f"e{k}"] if on else 0.0
        if on:
            p[f"z_e{k}"] = job.positions[f"z_e{k}"]
    unknown = sorted(set(p) - set(reg))
    if unknown:
        raise ValueError(f"expanded parameters not in the registry: {unknown}")
    return p


def expected_potentials(job: JobSpec, cfg: Config) -> dict[str, float]:
    """Assigned potential per named selection (plan section 8), for the checker."""
    pots = node_potentials(job, cfg)
    hv = hv_potentials(job, cfg)
    out = {"sel_tip": pots["tip"]}
    for k in job.electrodes_used:
        out[f"sel_e{k}"] = pots[f"e{k}"]
    out["sel_mesh_plane"] = hv["mesh"]
    out["sel_mesh_frame"] = hv["mesh"]
    out["sel_mcp_face"] = hv["mcp_front"]
    return out
