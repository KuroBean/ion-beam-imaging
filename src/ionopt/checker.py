"""Checker: per-ion derived table, spot statistics, mapping/resolution, validity (plan 9.6).

Inputs: a result folder (raw exports) and the CURRENT spec. Outputs: ions_derived.csv
and metrics.json. Thresholds and tolerances only affect this module, so `recheck`
can re-derive every verdict without rerunning a simulation.

Units in outputs: mm, eV, us, deg (stated in every column/key name).
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from . import units
from .config import Config, ConfigError, TBDError
from .electrodes import expected_potentials
from .results import load_job, read_bundle
from .schemas import FATES, FILES, REQUIRED_RAW, JobSpec, Metrics
from .utils import clean, read_json, write_json

SURFACE = {"mcp_active": "sel_mcp_face", "mcp_outside": "sel_mcp_face", "mesh_frame": "sel_mesh_frame",
           "wall": "sel_walls", "in_flight": "", "missing": ""}


# --------------------------------------------------------------------------- helpers


def weighted_quantile(x: np.ndarray, w: np.ndarray, q: float) -> float:
    """Smallest x such that the weight of values <= x is at least q of the total."""
    if len(x) == 0 or w.sum() <= 0:
        return math.nan
    o = np.argsort(x)
    cum = np.cumsum(w[o]) / w.sum()
    return float(x[o][min(np.searchsorted(cum, q - 1e-12), len(x) - 1)])


def _wmean(x, w):
    s = w.sum()
    return float(np.sum(w * x) / s) if s > 0 else math.nan


def _wstd(x, w):
    s = w.sum()
    if s <= 0:
        return math.nan
    m = np.sum(w * x) / s
    return float(np.sqrt(np.sum(w * (x - m) ** 2) / s))


def _nn(v):
    """float or None (for JSON)."""
    return None if v is None or (isinstance(v, float) and not math.isfinite(v)) else float(v)


# --------------------------------------------------------------------------- step 1


def threshold_check(cfg: Config, launch_mass_Da: float, charge: int, ke_eV: np.ndarray) -> np.ndarray:
    """True where the impact energy/speed meets the requirement (plan 9.6, section 11)."""
    req = cfg.spec.requirements
    if req.impact_threshold_eV_per_charge is not None:
        return ke_eV / abs(charge) >= req.impact_threshold_eV_per_charge
    if req.impact_threshold_mps is not None:
        m = (req.threshold_species_mass_Da or launch_mass_Da) * units.DALTON
        # same KE per charge for every species on the same path; speed of the threshold species
        return units.ke_eV_to_speed(np.maximum(ke_eV, 0), m) >= req.impact_threshold_mps
    raise TBDError("spec.requirements.impact_threshold_eV_per_charge")


def derive_ions(launch: pd.DataFrame, final: pd.DataFrame, geom: dict, job: JobSpec, cfg: Config) -> pd.DataFrame:
    """Per-ion derived table (ions_derived.csv)."""
    tol = cfg.require("spec.tolerances.fate_position_tol_um") * units.UM
    q = job.launch.charge
    d = launch[["ion_id", "theta_deg", "phi_deg", "KE0_eV", "weight", "w_E", "w_phi"]].merge(
        final.drop_duplicates("ion_id"), on="ion_id", how="left")
    n = len(d)
    x, y, z = d["x_m"].to_numpy(), d["y_m"].to_numpy(), d["z_m"].to_numpy()
    r = np.hypot(x, y)
    speed = np.sqrt(d["vx_mps"] ** 2 + d["vy_mps"] ** 2 + d["vz_mps"] ** 2).to_numpy()
    t = d["t_s"].to_numpy()

    fate = np.full(n, "wall", dtype=object)
    surface = np.full(n, "sel_walls", dtype=object)
    missing = np.isnan(z)
    t_end = geom.get("t_end_s")
    in_flight = ~missing & (t_end is not None) & (t >= (t_end or 0) * (1 - 1e-9)) & (speed > 0)

    on_mcp_plane = np.abs(z - geom["z_mcp_m"]) <= tol
    fz = geom["mesh_frame_z_m"]
    fr = geom["mesh_frame_r_m"]
    at_frame = (z >= fz[0] - tol) & (z <= fz[1] + tol) & (r >= fr[0] - tol) & \
               ((r <= fr[1] + tol) if fr[1] is not None else True)
    at_el = np.zeros(n, dtype=bool)
    el_sel = np.full(n, "", dtype=object)
    for e in geom.get("electrodes", []):
        if None in (e.get("thickness_m"), e.get("r_in_m"), e.get("r_out_m")):
            continue
        h = e["thickness_m"] / 2
        hit = (np.abs(z - e["z_m"]) <= h + tol) & (r >= e["r_in_m"] - tol) & (r <= e["r_out_m"] + tol) & ~at_el
        at_el |= hit
        el_sel[hit] = e["selection"]

    # order matters: earlier rules win
    rules = [
        (missing, "missing"),
        (in_flight, "in_flight"),
        (on_mcp_plane & (r <= geom["r_mcp_active_m"]), "mcp_active"),
        (on_mcp_plane, "mcp_outside"),
        (at_frame, "mesh_frame"),
        (at_el, "electrode"),
    ]
    done = np.zeros(n, dtype=bool)
    for mask, name in rules:
        sel = mask & ~done
        fate[sel] = name
        surface[sel] = el_sel[sel] if name == "electrode" else SURFACE[name]
        done |= sel

    on_mcp = np.isin(fate, ["mcp_active", "mcp_outside"])
    ke = d["KE_eV"].to_numpy()
    expected = d["KE0_eV"].to_numpy() + q * (d["V_start_V"].to_numpy() - d["V_end_V"].to_numpy())
    err_rel = (ke - expected) / np.maximum(np.abs(expected), d["KE0_eV"].to_numpy())
    with np.errstate(invalid="ignore"):
        angle = np.degrees(np.arccos(np.clip(d["vz_mps"].to_numpy() / speed, -1, 1)))
    above = np.zeros(n, dtype=bool)
    above[~missing] = threshold_check(cfg, job.launch.mass_Da, q, ke[~missing])

    return pd.DataFrame({
        "ion_id": d["ion_id"], "theta_deg": d["theta_deg"], "phi_deg": d["phi_deg"], "KE0_eV": d["KE0_eV"],
        "weight": d["weight"], "w_group": d["w_E"] * d["w_phi"],
        "fate": fate, "surface": surface,
        "x_land_mm": np.where(on_mcp, x / units.MM, np.nan),
        "y_land_mm": np.where(on_mcp, y / units.MM, np.nan),
        "r_land_mm": np.where(on_mcp, r / units.MM, np.nan),
        "on_mcp_active": fate == "mcp_active",
        "impact_KE_eV": ke, "impact_speed_mps": speed,
        "impact_angle_deg": np.where(on_mcp, angle, np.nan),
        "above_threshold": above,
        "tof_us": t / units.US,
        "energy_error_rel": err_rel,
        "energy_error_eV": ke - expected,
    })


# --------------------------------------------------------------------------- step 2


def spot_statistics(dv: pd.DataFrame, fidelity: str, cfg: Config) -> dict[str, float | None]:
    a = dv[dv["fate"] == "mcp_active"]
    w = a["weight"].to_numpy()
    r_act = cfg.spec.detector.mcp_active_diameter_mm / 2
    keys = ["landed_weight", "centroid_x_mm", "centroid_y_mm", "centroid_offset_mm", "rms_centroid_mm",
            "rms_axis_mm", "r50_mm", "r90_mm", "r_max_mm", "fill_fraction", "impact_KE_mean_eV",
            "impact_KE_min_eV", "frac_above_threshold", "impact_angle_mean_deg", "impact_angle_max_deg",
            "tof_mean_us", "tof_std_us"]
    out: dict[str, float | None] = {k: None for k in keys}
    out["n_landed"] = int(len(a))
    out["landed_weight"] = float(w.sum())
    if len(a) == 0 or w.sum() <= 0:
        return out
    x, y, r = a["x_land_mm"].to_numpy(), a["y_land_mm"].to_numpy(), a["r_land_mm"].to_numpy()
    if fidelity == "3d":
        cx, cy = _wmean(x, w), _wmean(y, w)
        rms_c = math.sqrt(_wmean((x - cx) ** 2 + (y - cy) ** 2, w))
    else:  # 2D: x is the radial coordinate; centroid is on the axis by symmetry
        cx = cy = 0.0
        rms_c = math.sqrt(_wmean(r ** 2, w))
    r90 = weighted_quantile(r, w, 0.9)
    out.update({
        "centroid_x_mm": cx, "centroid_y_mm": cy, "centroid_offset_mm": math.hypot(cx, cy),
        "rms_centroid_mm": rms_c, "rms_axis_mm": math.sqrt(_wmean(r ** 2, w)),
        "r50_mm": weighted_quantile(r, w, 0.5), "r90_mm": r90, "r_max_mm": float(r.max()),
        "fill_fraction": r90 / r_act,
        "impact_KE_mean_eV": _wmean(a["impact_KE_eV"].to_numpy(), w),
        "impact_KE_min_eV": float(a["impact_KE_eV"].min()),
        "frac_above_threshold": _wmean(a["above_threshold"].to_numpy().astype(float), w),
        "impact_angle_mean_deg": _wmean(a["impact_angle_deg"].to_numpy(), w),
        "impact_angle_max_deg": float(a["impact_angle_deg"].max()),
        "tof_mean_us": _wmean(a["tof_us"].to_numpy(), w),
        "tof_std_us": _wstd(a["tof_us"].to_numpy(), w),
    })
    return {k: _nn(v) if k != "n_landed" else v for k, v in out.items()}


# --------------------------------------------------------------------------- step 3


def mapping(dv: pd.DataFrame, cfg: Config) -> dict[str, Any]:
    """r(theta), sigma_E(theta), dr/dtheta, dtheta(theta), evaluation range, monotonicity, score."""
    sigma_mcp = cfg.require("spec.detector.sigma_mcp_um") * units.UM
    mono_tol = cfg.require("spec.tolerances.monotonic_tol_um") * units.UM
    frac_min = cfg.spec.tolerances.eval_range_landed_frac
    an = cfg.spec.analysis

    th_deg, r_m, s_m, landed = [], [], [], []
    for th, g in dv.groupby(dv["theta_deg"].round(9), sort=True):
        wg = g["w_group"].to_numpy()
        if wg.sum() <= 0:
            wg = np.ones(len(g))
        act = g["fate"].to_numpy() == "mcp_active"
        th_deg.append(float(th))
        landed.append(float(wg[act].sum() / wg.sum()))
        r = g["r_land_mm"].to_numpy()[act] * units.MM
        r_m.append(_wmean(r, wg[act]) if act.any() else math.nan)
        s_m.append(_wstd(r, wg[act]) if act.any() else math.nan)
    th_deg, r_m, s_m, landed = map(np.array, (th_deg, r_m, s_m, landed))

    n_eval = 0
    while n_eval < len(th_deg) and landed[n_eval] >= frac_min - 1e-12:
        n_eval += 1
    th = np.radians(th_deg[:n_eval])
    re, se = r_m[:n_eval], s_m[:n_eval]

    drdth = np.full(len(th_deg), np.nan)
    dth = np.full(len(th_deg), np.nan)
    score = None
    monotonic = False
    flags: list[str] = []
    min_pts = 4 if an.drdtheta_method == "spline" else 2
    if n_eval >= min_pts:
        if an.drdtheta_method == "central":
            deriv = np.gradient(re, th)
        else:
            from scipy.interpolate import UnivariateSpline
            deriv = UnivariateSpline(th, re, k=3, s=an.spline_smoothing or 0).derivative()(th)
        sig_tot = np.sqrt(se ** 2 + sigma_mcp ** 2)
        with np.errstate(divide="ignore"):
            d = np.where(np.abs(deriv) > 0, sig_tot / np.abs(deriv), np.inf)
        drdth[:n_eval] = deriv
        dth[:n_eval] = np.degrees(d)
        score = float(np.max(dth[:n_eval]))
        monotonic = bool(np.all(np.diff(re) > -mono_tol))
        if not monotonic:
            flags.append("r(theta) is not monotonic over the evaluation range")
        if not math.isfinite(score):
            flags.append("dr/dtheta is zero somewhere in the evaluation range")
    else:
        flags.append(f"evaluation range has {n_eval} theta points (need {min_pts}): too few ions land")

    return {
        "theta_deg": th_deg.tolist(),
        "r_mm": [_nn(v / units.MM) for v in r_m],
        "sigma_E_mm": [_nn(v / units.MM) for v in s_m],
        "landed_frac": landed.tolist(),
        "drdtheta_mm_per_deg": [_nn(v / units.MM * units.DEG) for v in drdth],
        "dtheta_deg": [_nn(v) for v in dth],
        "sigma_mcp_mm": sigma_mcp / units.MM,
        "n_eval": int(n_eval),
        "eval_theta_max_deg": float(th_deg[n_eval - 1]) if n_eval else None,
        "monotonic": monotonic,
        "score_dtheta_deg": _nn(score) if score is not None else None,
        "flags": flags,
    }


# --------------------------------------------------------------------------- driver


def _invalid(job_id: str, cfg: Config, flags: list[str], **validity: bool) -> Metrics:
    return Metrics(job_id=job_id, spec_hash=cfg.spec_hash(), valid=False, feasible=False, flags=flags,
                   validity=validity)


def check(result_dir: Path | str, cfg: Config, write: bool = True) -> Metrics:
    """Run the checker on one result folder with the current spec."""
    d = Path(result_dir)
    bundle = read_bundle(d)
    try:
        job = load_job(d)
    except (OSError, ValueError) as e:
        m = _invalid(d.name, cfg, [f"cannot read job.json: {e}"], files_present=False)
        return _finish(d, m, None, write)
    if bundle.status != "success":
        return _finish(d, _invalid(job.job_id, cfg, [f"run {bundle.status}: {bundle.error}"], run_succeeded=False),
                       None, write)
    missing_files = [k for k in REQUIRED_RAW if k not in bundle.files]
    if any(k in missing_files for k in ("ions_launch", "ions_final", "geometry")):
        return _finish(d, _invalid(job.job_id, cfg, [f"required files missing: {missing_files}"],
                                   files_present=False), None, write)

    launch = pd.read_csv(d / FILES["ions_launch"])
    final = pd.read_csv(d / FILES["ions_final"])
    geom = read_json(d / FILES["geometry"])
    dv = derive_ions(launch, final, geom, job, cfg)
    spot = spot_statistics(dv, job.fidelity, cfg)
    mp = mapping(dv, cfg)

    # ---- step 4: requirements and validity
    req, tol = cfg.spec.requirements, cfg.spec.tolerances
    open_frac = cfg.require("spec.detector.mesh_open_fraction")
    eta_min = cfg.require("spec.requirements.eta_min")
    e_tol = cfg.require("spec.tolerances.energy_conservation_rel")
    v_tol = cfg.require("spec.tolerances.potential_match_V")
    w = dv["weight"].to_numpy()
    act = dv["fate"].to_numpy() == "mcp_active"
    w_all = w.sum()
    eta = open_frac * w[act].sum() / w_all if w_all > 0 else 0.0
    frac_fast = float(w[act & dv["above_threshold"].to_numpy()].sum() / w[act].sum()) if w[act].sum() > 0 else 0.0

    flags = list(mp.pop("flags"))
    validity: dict[str, bool] = {}
    validity["files_present"] = not missing_files
    if missing_files:
        flags.append(f"required files missing: {missing_files}")
    n_missing = int((dv["fate"] == "missing").sum())
    extra_ids = set(final["ion_id"]) - set(launch["ion_id"])
    dup = int(final["ion_id"].duplicated().sum())
    validity["fate_counts_complete"] = n_missing == 0 and not extra_ids and dup == 0
    if not validity["fate_counts_complete"]:
        flags.append(f"ion bookkeeping: {n_missing} launched ions missing from ions_final, "
                     f"{len(extra_ids)} unknown ids, {dup} duplicates")
    # an ion passes if its error is within the relative OR the absolute tolerance (low-energy ions that
    # end on electrodes have tiny expected energies, so a relative limit alone is too strict there)
    e_abs = tol.energy_conservation_abs_eV
    err = np.abs(dv["energy_error_rel"].to_numpy())
    err_eV = np.abs(dv["energy_error_eV"].to_numpy())
    ok = np.isfinite(err)
    err, err_eV = err[ok], err_eV[ok]
    max_err = float(err.max()) if len(err) else 0.0
    bad = (err > e_tol) & (err_eV > e_abs)
    validity["energy_conserved"] = not bad.any()
    if bad.any():
        flags.append(f"energy conservation error: {int(bad.sum())} ions exceed {e_tol} (relative) and {e_abs} eV "
                     f"(worst {err[bad].max():.3g} relative, {err_eV[bad].max():.3g} eV)")
    validity["potentials_match"], pflag = _potentials_ok(d, bundle, job, cfg, v_tol)
    if pflag:
        flags.append(pflag)
    n_flight = int((dv["fate"] == "in_flight").sum())
    validity["no_in_flight"] = n_flight == 0
    if n_flight:
        flags.append(f"{n_flight} ions still in flight at t_end")
    valid = all(validity.values())

    # ---- feasibility
    opt_results = {}
    for key, limit in req.optional_constraints.items():
        stat = key[4:]
        pool = {**spot, "eta": eta, "frac_fast": frac_fast}
        if stat not in pool:
            raise ConfigError(f"spec.requirements.optional_constraints.{key}: unknown statistic '{stat}' "
                              f"(known: {sorted(pool)})")
        v = pool[stat]
        ok = v is not None and (v >= limit if key.startswith("min_") else v <= limit)
        opt_results[key] = ok
        if not ok:
            flags.append(f"optional constraint {key} = {limit} not met ({stat} = {v})")
    score = mp["score_dtheta_deg"]
    feas = {
        "evaluable": score is not None and math.isfinite(score),
        "monotonic": mp["monotonic"],
        "eta_ok": eta >= eta_min,
        "fast_ok": frac_fast >= req.frac_fast_min,
        **{f"opt_{k}": v for k, v in opt_results.items()},
    }
    if not feas["eta_ok"]:
        flags.append(f"collection efficiency {eta:.3g} < eta_min {eta_min}")
    if not feas["fast_ok"]:
        flags.append(f"fast fraction {frac_fast:.3g} < frac_fast_min {req.frac_fast_min}")
    feasible = valid and all(feas.values())

    fates = {f: float(w[dv["fate"].to_numpy() == f].sum() / w_all) for f in FATES}
    counts = {f: int((dv["fate"] == f).sum()) for f in FATES}
    if n_missing:
        counts["missing"] = n_missing
    m = Metrics.model_validate(clean(dict(
        job_id=job.job_id, spec_hash=cfg.spec_hash(), valid=valid, feasible=feasible, score=score,
        flags=flags, validity=validity, fates=fates, fate_counts=counts, spot=spot, mapping=mp,
        requirements={"eta": eta, "eta_min": eta_min, "mesh_open_fraction": open_frac, "frac_fast": frac_fast,
                      "frac_fast_min": req.frac_fast_min, "max_energy_error_rel": max_err, **feas},
        n_launched=int(len(launch)), fidelity=job.fidelity,
    )))
    return _finish(d, m, dv, write)


def _potentials_ok(d: Path, bundle, job: JobSpec, cfg: Config, v_tol: float) -> tuple[bool, str | None]:
    if "electrode_potentials" not in bundle.files:
        return False, "electrode_potentials.csv missing"
    ep = pd.read_csv(d / FILES["electrode_potentials"])
    got = dict(zip(ep["selection"], ep["V_mean_V"]))
    bad = []
    for sel, v in expected_potentials(job, cfg).items():
        if sel not in got:
            bad.append(f"{sel} not exported")
        elif abs(got[sel] - v) > v_tol:
            bad.append(f"{sel}: {got[sel]:g} V vs assigned {v:g} V")
    return (not bad), (f"electrode potentials mismatch: {bad}" if bad else None)


def _finish(d: Path, m: Metrics, dv: pd.DataFrame | None, write: bool) -> Metrics:
    if write:
        if dv is not None:
            dv.to_csv(d / FILES["ions_derived"], index=False)
        write_json(d / FILES["metrics"], m.model_dump())
    return m


# --------------------------------------------------------------------------- recheck / convergence


def recheck(results_dir: Path | str, cfg: Config, job_ids: list[str] | None = None) -> list[Metrics]:
    """Recompute metrics for stored runs with the current spec (no simulation)."""
    root = Path(results_dir)
    dirs = [root / j for j in job_ids] if job_ids else sorted(p for p in root.iterdir()
                                                              if (p / FILES["job"]).is_file())
    return [check(p, cfg) for p in dirs]


def convergence_check(normal: Metrics, conv: Metrics, cfg: Config) -> dict[str, Any]:
    """Compare a normal run with its convergence rerun (2x ions, fine mesh)."""
    tol = cfg.require("spec.tolerances.convergence_rel")

    def rel(a, b):
        if a is None or b is None:
            return math.inf
        return abs(b - a) / max(abs(a), 1e-300)

    d_score = rel(normal.score, conv.score)
    d_eta = rel(normal.requirements.get("eta"), conv.requirements.get("eta"))
    return {"passed": d_score <= tol and d_eta <= tol, "rel_change_dtheta": _nn(d_score),
            "rel_change_eta": _nn(d_eta), "tolerance": tol}
