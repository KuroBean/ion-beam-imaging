"""Calibrate the launch angular spread so the beam reaching the extractor (L1) has a target spread.

Target (phenomenological emission model): just in front of L1 the beam's polar-angle distribution is
Gaussian-like, dI/dOmega ~ exp(-theta^2/2 sigma^2), with a given HWHM (e.g. 20 deg = 40 deg FWHM).
The math lives in src/ionopt/emission.py (tested); this script drives COMSOL. Models are never saved,
except by `apply3d`, which writes a NEW file.

Subcommands (run in this order):

  map2d    2D model, in memory: launch a fan of rays at theta0 = 0..theta0_max (fixed kinetic energy
           E_ion, on the axis at the tip), trace them, record the angle where each ray crosses the
           plane z = (L1 front) - plane_offset. Writes logs/emission_map2d_<tag>.npz/.json.
           --set NAME=VALUE changes model parameters first (e.g. L1_v=-60[V]) for sensitivity maps.
  fit      Reweight a map for every candidate launch spread (the parameter sweep), for two families:
             beam   COMSOL Particle Beam, Gaussian transverse slopes, std sigma_s   (3D pbeam1)
             omega  launch.py grid, Gaussian dI/dOmega with launch HWHM, cut at theta_max
           Writes logs/emission_fit.json and logs/emission_fit.png (+ sensitivity plot for >1 map).
  check3d  3D model, in memory: set pbeam1.xmp, trace, measure the launch slope spread (t = 0) and
           the angle distribution at the same plane; compare with the target and the 2D prediction.
  apply3d  3D model: add parameter pbeam_xmp, point pbeam1.xmp at it, re-run the particle study,
           save as a new file (refuses to overwrite).

Usage (.venv\\Scripts\\python.exe scripts\\calibrate_emission.py ...):
  map2d --plane-offset-mm 0.5 [--tag ref] [--set L1_v=-60[V]]
  fit --target-hwhm-deg 20 logs/emission_map2d_ref.npz [more maps for sensitivity]
  check3d --xmp 0.5 --plane-offset-mm 0.5 --t-end-us 20 [--map2d logs/emission_map2d_ref.npz --target-hwhm-deg 20]
  apply3d --xmp X --out lens8newMCP_ks_v6_beam.mph
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from introspect_models import setup_mph, tags  # noqa: E402
from ionopt import emission as em  # noqa: E402
from ionopt.config import load_config  # noqa: E402
from ionopt.launch import write_release_file  # noqa: E402

LOGS = ROOT / "logs"
E_CHARGE = 1.602176634e-19
DALTON = 1.66053906660e-27

# plot styling (dataviz reference palette, light mode)
C_TEXT, C_TEXT2, C_GRID = "#0b0b0b", "#52514e", "#e4e3df"
C_SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]


# --------------------------------------------------------------------------- COMSOL helpers


def start(cfg, key):
    mph = setup_mph(cfg.paths.comsol_root)
    client = mph.start()
    t = time.time()
    path = cfg.path(f"models.{key}")
    model = client.load(str(path))
    print(f"loaded {path.name} in {time.time() - t:.0f} s", flush=True)
    return client, model, path


def particle_all(j, sol, exprs):
    """[len(exprs), particle, time] at all output times."""
    ds = j.result().dataset()
    if "part_cal" in tags(ds):
        ds.remove("part_cal")
    ds.create("part_cal", "Particle").set("solution", sol)
    ev = j.result().numerical().create("pev_cal", "Particle")
    ev.set("data", "part_cal")
    ev.set("innerinput", "all")
    ev.set("evaluate", "all")
    out = []
    for e in exprs:
        ev.set("expr", e)
        out.append(np.array([np.array(row) for row in ev.getReal()]))
    j.result().numerical().remove("pev_cal")
    ds.remove("part_cal")
    return np.array(out)


def set_params(j, items):
    for kv in items or []:
        name, val = kv.split("=", 1)
        if name not in [str(n) for n in j.param().varnames()]:
            sys.exit(f"unknown model parameter {name}")
        j.param().set(name, val)
        print(f"set {name} = {val}", flush=True)


def run(j, std):
    t = time.time()
    j.study(std).run()
    print(f"{std} ran in {time.time() - t:.0f} s", flush=True)


def z_plane_mm(j, offset_mm):
    """Measurement plane in model z (mm): L1 front face (tip_z + lens_gap) minus offset."""
    return (float(j.param().evaluate("tip_z")) + float(j.param().evaluate("lens_gap"))) * 1e3 - offset_mm


# --------------------------------------------------------------------------- map2d


def cmd_map2d(a, cfg):
    client, model, path = start(cfg, "2d")
    j = model.java
    set_params(j, a.set)
    j.param().set("t_end", f"{a.t_end_us}[us]")
    j.param().set("dt_out", f"{a.dt_out_us}[us]")
    P = lambda n: float(j.param().evaluate(n))  # noqa: E731  SI
    tip_z, E, m = P("tip_z"), P("E_ion"), P("m_ion")
    v0 = math.sqrt(2 * E / m)
    axis_off = cfg.get("spec.launch.axis_offset_nm") * 1e-9
    off_um = cfg.get("spec.launch.launch_offset_um")
    z0 = off_um * 1e-6 if off_um is not None else axis_off     # launch point in front of the apex
    th0 = np.radians(np.linspace(0.0, a.theta0_max_deg, a.n_rays))
    df = pd.DataFrame({"ion_id": np.arange(a.n_rays), "x_m": 0.0, "y_m": 0.0, "z_m": z0,
                       "vx_mps": v0 * np.sin(th0), "vy_mps": 0.0, "vz_mps": v0 * np.cos(th0)})
    rel_file = LOGS / f"emission_release2d_{a.tag}.txt"
    write_release_file(df, rel_file, "2d", z_shift_m=tip_z, axis_offset_m=axis_off)
    rel = j.component("comp1").physics("cpt").feature("relf1")
    assert str(rel.getType()) == "ReleaseFromDataFile"
    rel.set("Filename", str(rel_file))
    rel.importData()
    print(f"{a.n_rays} rays, theta0 0..{a.theta0_max_deg} deg, E_ion {E / E_CHARGE:g} eV, "
          f"m_ion {m / DALTON:.1f} Da, v0 {v0:.1f} m/s, launch {z0 * 1e9:g} nm in front of the apex", flush=True)
    run(j, "std1")
    run(j, "std2")
    t, qr, qz, vr, vz = particle_all(j, "sol2", ["t", "qr", "qz", "cpt.vr", "cpt.vz"])
    zp = z_plane_mm(j, a.plane_offset_mm)
    vr_c, vz_c, r_c, t_c = em.plane_crossing(qz, vr, vz, qr, t, z_plane=zp)
    th_ext = np.arctan2(vr_c, vz_c)
    ke_c = 0.5 * m * (vr_c**2 + vz_c**2) / E_CHARGE
    n_ok = int(np.isfinite(th_ext).sum())
    print(f"plane z = {zp:.3f} mm: {n_ok}/{a.n_rays} rays crossed; last crossing at {np.nanmax(t_c) * 1e6:.2f} us; "
          f"theta_ext 0..{np.degrees(np.nanmax(th_ext)):.2f} deg; KE at plane {np.nanmin(ke_c):.1f}..{np.nanmax(ke_c):.1f} eV",
          flush=True)
    if n_ok < a.n_rays:
        print(f"WARNING: {a.n_rays - n_ok} rays did not reach the plane (t_end too short or hit something)")
    meta = {"model": path.name, "set": a.set or [], "plane_offset_mm": a.plane_offset_mm, "z_plane_mm": zp,
            "tip_z_mm": tip_z * 1e3, "lens_gap_mm": P("lens_gap") * 1e3, "E_ion_eV": E / E_CHARGE,
            "m_ion_Da": m / DALTON, "v0_mps": v0, "launch_z0_nm": z0 * 1e9, "n_rays": a.n_rays,
            "n_crossed": n_ok, "t_end_us": a.t_end_us, "dt_out_us": a.dt_out_us,
            "L1_v": P("L1_v"), "tag": a.tag}
    out = LOGS / f"emission_map2d_{a.tag}"
    np.savez(out.with_suffix(".npz"), theta0=th0, theta_ext=th_ext, r_cross_mm=r_c, t_cross_s=t_c, ke_cross_eV=ke_c,
             meta=json.dumps(meta))
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"wrote {out.with_suffix('.npz')}")
    client.remove(model)


# --------------------------------------------------------------------------- fit


def load_map(p):
    d = np.load(p)
    return em.AngleMap(d["theta0"], d["theta_ext"]), json.loads(str(d["meta"])), d


def transverse_velocity_rms(sigma_s, v0, n=400000, seed=1):
    """Per-axis rms transverse velocity of a Particle Beam with slope std sigma_s and speed v0."""
    rng = np.random.default_rng(seed)
    sx, sy = rng.normal(0, sigma_s, n), rng.normal(0, sigma_s, n)
    vz = v0 / np.sqrt(1 + sx**2 + sy**2)
    return float(np.sqrt(np.mean((sx * vz) ** 2)))


def dIdOmega(cdf, theta, bin_deg=1.0):
    """Binned dI/dOmega (normalized so that the integral over the hemisphere is 1)."""
    edges = np.radians(np.arange(0, 90 + bin_deg, bin_deg))
    F = np.interp(edges, theta, cdf)
    dens = np.diff(F) / (2 * np.pi * (np.cos(edges[:-1]) - np.cos(edges[1:])))
    return np.degrees(0.5 * (edges[1:] + edges[:-1])), dens


def style(ax, title, xlabel, ylabel):
    ax.set_title(title, loc="left", fontsize=10, color=C_TEXT)
    ax.set_xlabel(xlabel, color=C_TEXT2, fontsize=9)
    ax.set_ylabel(ylabel, color=C_TEXT2, fontsize=9)
    ax.grid(True, color=C_GRID, lw=0.6)
    ax.tick_params(colors=C_TEXT2, labelsize=8)
    for s in ax.spines.values():
        s.set_color(C_GRID)


def cmd_fit(a, cfg):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    th = em.eval_grid()
    s_t = em.hwhm_to_sigma(math.radians(a.target_hwhm_deg))
    tgt = em.target_cdf(th, s_t)
    theta_max = math.radians(cfg.get("spec.launch.theta_max_deg"))
    beam_pars = np.logspace(-3, math.log10(30), 900)
    omega_hwhm = np.radians(np.arange(0.5, 360.0, 0.25))
    omega_pars = np.array([em.hwhm_to_sigma(h) for h in omega_hwhm])
    results = {"target_hwhm_deg": a.target_hwhm_deg, "theta_max_deg_spec": math.degrees(theta_max), "maps": []}

    maps = [load_map(p) for p in a.maps]
    sweeps = []
    for fname, (m, meta, d) in zip(a.maps, maps):
        r_beam = em.sweep(m, "beam", beam_pars, s_t, th)
        r_cut = em.sweep(m, "omega", omega_pars, s_t, th, theta_max)
        r_unc = em.sweep(m, "omega", omega_pars, s_t, th, em.HALF_PI)
        sweeps.append((r_beam, r_cut, r_unc))
        v0 = meta["v0_mps"]
        na_v0 = math.sqrt(2 * meta["E_ion_eV"] * E_CHARGE / (cfg.get("spec.launch.mass_Da") * DALTON))
        ent = {"file": Path(fname).name, "meta": meta,
               "map_max_theta_ext_deg": float(np.degrees(np.max(m.theta_ext))),
               "beam": {"sigma_s": r_beam["best"], "cdf_rms": r_beam["best_rms"], "ks": r_beam["best_ks"],
                        "extractor_equiv_hwhm_deg": math.degrees(r_beam["best_equiv_hwhm"]),
                        "extractor_median_deg": math.degrees(r_beam["best_median"]),
                        "launch_prob_beyond_map": r_beam["best_lost"], "at_sweep_edge": r_beam["at_edge"],
                        "vperp_rms_per_axis_mps_model_mass": transverse_velocity_rms(r_beam["best"], v0),
                        "vperp_rms_per_axis_mps_spec_mass": transverse_velocity_rms(r_beam["best"], na_v0)},
               "omega_cut": {"launch_hwhm_deg": math.degrees(em.sigma_to_hwhm(r_cut["best"])),
                             "theta_max_deg": math.degrees(theta_max), "cdf_rms": r_cut["best_rms"],
                             "ks": r_cut["best_ks"], "extractor_equiv_hwhm_deg": math.degrees(r_cut["best_equiv_hwhm"]),
                             "at_sweep_edge": r_cut["at_edge"]},
               "omega_uncut": {"launch_hwhm_deg": math.degrees(em.sigma_to_hwhm(r_unc["best"])),
                               "theta_max_deg": 90.0, "cdf_rms": r_unc["best_rms"], "ks": r_unc["best_ks"],
                               "extractor_equiv_hwhm_deg": math.degrees(r_unc["best_equiv_hwhm"]),
                               "launch_prob_beyond_map": r_unc["best_lost"], "at_sweep_edge": r_unc["at_edge"]}}
        results["maps"].append(ent)
    # sensitivity: the reference map's best beam setting, evaluated on every map
    ref_sig = sweeps[0][0]["best"]
    for ent, (m, meta, d) in zip(results["maps"], maps):
        c, _ = em.extractor_cdf(m, "beam", ref_sig, th)
        ent["with_reference_sigma_s"] = {"sigma_s": ref_sig, "extractor_equiv_hwhm_deg": math.degrees(em.equivalent_hwhm(c, th)),
                                         "cdf_rms": em.cdf_rms(c, tgt), "ks": em.cdf_ks(c, tgt)}
    out = LOGS / "emission_fit"
    out.with_suffix(".json").write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(json.dumps(results, indent=1))

    # ---- figure 1: fit on the reference map
    (m, meta, d), (r_beam, r_cut, r_unc) = maps[0], sweeps[0]
    fig, ax = plt.subplots(2, 3, figsize=(15, 8.5), facecolor="#fcfcfb")
    lbl_b = f"Particle Beam, slope std {r_beam['best']:.3f}"
    lbl_o = f"launch.py, launch HWHM {math.degrees(em.sigma_to_hwhm(r_cut['best'])):.1f} deg (cut {math.degrees(theta_max):.0f} deg)"
    lbl_t = f"target, HWHM {a.target_hwhm_deg:g} deg"
    x = ax[0, 0]
    x.plot(np.degrees(m.theta0), np.degrees(m.theta_ext), color=C_SERIES[0], lw=2)
    x.plot([0, 90], [0, 90], color=C_TEXT2, lw=1, ls=":")
    x.text(60, 62, "no change", color=C_TEXT2, fontsize=8)
    style(x, f"a  Angle at the plane vs launch angle (2D, {meta['tag']})", "launch angle theta0 (deg)",
          "angle at plane theta_ext (deg)")
    x = ax[0, 1]
    x.plot(np.degrees(th), tgt, color=C_TEXT2, lw=2, ls="--", label=lbl_t)
    x.plot(np.degrees(th), r_beam["best_cdf"], color=C_SERIES[0], lw=2, label=lbl_b)
    x.plot(np.degrees(th), r_cut["best_cdf"], color=C_SERIES[1], lw=2, label=lbl_o)
    style(x, "b  Fraction of ions within angle theta at the plane", "theta (deg)", "cumulative fraction")
    x.legend(fontsize=7.5, frameon=False, loc="lower right")
    x = ax[0, 2]
    for cdf, col, ls, lb in ((tgt, C_TEXT2, "--", lbl_t), (r_beam["best_cdf"], C_SERIES[0], "-", lbl_b),
                             (r_cut["best_cdf"], C_SERIES[1], "-", lbl_o)):
        xb, yb = dIdOmega(cdf, th)
        x.plot(xb, yb, color=col, lw=2, ls=ls, label=lb)
    x.axvline(a.target_hwhm_deg, color=C_GRID, lw=1)
    style(x, "c  Angular intensity dI/dOmega at the plane", "theta (deg)", "dI/dOmega (1/sr, normalized)")
    x.set_xlim(0, 70)
    x.legend(fontsize=7.5, frameon=False)
    x = ax[1, 0]
    x.semilogx(r_beam["pars"], r_beam["rms"], color=C_SERIES[0], lw=2)
    x.axvline(r_beam["best"], color=C_SERIES[0], lw=1, ls=":")
    x.text(r_beam["best"] * 1.1, max(r_beam["rms"]) * 0.9, f"best {r_beam['best']:.3f}", color=C_TEXT, fontsize=8)
    style(x, "d  Sweep: Particle Beam slope std", "transverse slope std sigma_s (vx/vz)", "RMS CDF error vs target")
    x = ax[1, 1]
    hw = np.degrees([em.sigma_to_hwhm(p) for p in r_cut["pars"]])
    x.plot(hw, r_cut["rms"], color=C_SERIES[1], lw=2, label=f"cut at {math.degrees(theta_max):.0f} deg")
    x.plot(hw, r_unc["rms"], color=C_SERIES[1], lw=1.2, ls="--", label="cut at 90 deg")
    best_hw = math.degrees(em.sigma_to_hwhm(r_cut["best"]))
    x.axvline(best_hw, color=C_SERIES[1], lw=1, ls=":")
    x.text(best_hw * 1.03, max(r_cut["rms"]) * 0.9, f"best {best_hw:.1f} deg", color=C_TEXT, fontsize=8)
    style(x, "e  Sweep: launch.py launch HWHM", "launch HWHM (deg)", "RMS CDF error vs target")
    x.set_xscale("log")
    x.legend(fontsize=7.5, frameon=False)
    x = ax[1, 2]
    t0 = np.radians(np.linspace(0.05, 89.5, 1500))
    for pdf, col, lb in ((em.pdf_beam(t0, r_beam["best"]), C_SERIES[0], lbl_b),
                         (em.pdf_omega(t0, r_cut["best"], theta_max), C_SERIES[1], lbl_o)):
        dens = pdf / np.sin(t0)
        x.plot(np.degrees(t0), dens / np.nanmax(dens[:50]), color=col, lw=2, label=lb)
    style(x, "f  Launch distributions that give the best match", "launch angle theta0 (deg)",
          "dI/dOmega at launch (axis = 1)")
    x.legend(fontsize=7.5, frameon=False)
    fig.suptitle(f"Emission calibration: target HWHM {a.target_hwhm_deg:g} deg at {meta['plane_offset_mm']:g} mm in front of L1 "
                 f"(E_ion {meta['E_ion_eV']:g} eV, L1_v {meta['L1_v']:g} V)", x=0.01, ha="left", color=C_TEXT, fontsize=11)
    fig.tight_layout()
    fig.savefig(out.with_suffix(".png"), dpi=130)
    print(f"wrote {out.with_suffix('.png')}")

    if len(maps) > 1:   # ---- figure 2: sensitivity of the map to model settings
        fig, ax = plt.subplots(1, 2, figsize=(11, 4.3), facecolor="#fcfcfb")
        for i, ((m, meta, d), ent) in enumerate(zip(maps, results["maps"])):
            col = C_SERIES[i % len(C_SERIES)]
            lb = f"{meta['tag']}: L1_v {meta['L1_v']:g} V" + (f" ({', '.join(meta['set'])})" if meta["set"] else "")
            ax[0].plot(np.degrees(m.theta0), np.degrees(m.theta_ext), color=col, lw=2, label=lb)
            c, _ = em.extractor_cdf(m, "beam", ref_sig, th)
            xb, yb = dIdOmega(c, th)
            ax[1].plot(xb, yb, color=col, lw=2,
                       label=f"{meta['tag']}: HWHM {ent['with_reference_sigma_s']['extractor_equiv_hwhm_deg']:.1f} deg")
        xb, yb = dIdOmega(tgt, th)
        ax[1].plot(xb, yb, color=C_TEXT2, lw=2, ls="--", label=lbl_t)
        style(ax[0], "a  Angle map for each model setting", "launch angle theta0 (deg)", "angle at plane (deg)")
        style(ax[1], f"b  dI/dOmega at the plane, same launch (slope std {ref_sig:.3f})", "theta (deg)",
              "dI/dOmega (1/sr, normalized)")
        ax[1].set_xlim(0, 70)
        for x in ax:
            x.legend(fontsize=7.5, frameon=False)
        fig.tight_layout()
        fig.savefig(LOGS / "emission_sensitivity.png", dpi=130)
        print(f"wrote {LOGS / 'emission_sensitivity.png'}")


# --------------------------------------------------------------------------- 3D


def pbeam(j):
    f = j.component("comp1").physics("cpt").feature("pbeam1")
    assert str(f.getType()) == "ParticleBeam", f.getType()
    return f


def xmp_value(s: str) -> float | None:
    try:
        return float(s)
    except ValueError:
        return None


def cmd_check3d(a, cfg):
    client, model, path = start(cfg, "3d")
    j = model.java
    set_params(j, a.set)
    pb = pbeam(j)
    print(f"pbeam1: xmp {pb.getString('xmp')} -> {a.xmp}, sampling {pb.getString('SamplingFromPhaseSpaceEllipse')}, "
          f"N {pb.getString('N')}, El {pb.getString('El')}", flush=True)
    pb.set("xmp", a.xmp)
    j.param().set("t_end", f"{a.t_end_us}[us]")
    j.param().set("dt_out", f"{a.dt_out_us}[us]")
    if a.set:
        run(j, "std1")
    run(j, "std2")
    t, qx, qy, qz, vx, vy, vz = particle_all(j, "sol2", ["t", "qx", "qy", "qz", "cpt.vx", "cpt.vy", "cpt.vz"])
    good = np.isfinite(vx[:, 0]) & np.isfinite(vy[:, 0]) & np.isfinite(vz[:, 0])
    if not good.all():
        print(f"{(~good).sum()} particle(s) without a t = 0 state dropped", flush=True)
    t, qx, qy, qz, vx, vy, vz = (arr[good] for arr in (t, qx, qy, qz, vx, vy, vz))
    sx, sy = vx[:, 0] / vz[:, 0], vy[:, 0] / vz[:, 0]
    speed0 = np.sqrt(vx[:, 0] ** 2 + vy[:, 0] ** 2 + vz[:, 0] ** 2)
    sig_hat = float(np.sqrt(np.mean(sx**2 + sy**2) / 2))      # Rayleigh ML estimate of the slope std
    th = em.eval_grid()
    th0 = np.arctan(np.hypot(sx, sy))
    c0 = em.sample_cdf(th0, th)
    c0_model, _ = em.extractor_cdf(em.AngleMap(np.radians(np.linspace(0, 89.9, 900)),
                                               np.radians(np.linspace(0, 89.9, 900))), "beam", sig_hat, th)
    res = {"model": path.name, "xmp": a.xmp, "set": a.set or [], "n": int(len(sx)),
           "t0": {"slope_std_x": float(np.std(sx)), "slope_std_y": float(np.std(sy)), "slope_mean_x": float(np.mean(sx)),
                  "slope_mean_y": float(np.mean(sy)), "sigma_s_hat": sig_hat,
                  "sigma_s_per_xmp": sig_hat / xmp_value(a.xmp),
                  "speed_min": float(speed0.min()), "speed_max": float(speed0.max()),
                  "ks_launch_angles_vs_gaussian_slopes": em.cdf_ks(c0, c0_model)}}
    print(json.dumps(res["t0"], indent=1), flush=True)
    if a.t_end_us > 0.5:
        zp = z_plane_mm(j, a.plane_offset_mm)
        vx_c, vy_c, vz_c, x_c, y_c, t_c = em.plane_crossing(qz, vx, vy, vz, qx, qy, t, z_plane=zp)
        th_ext = np.arctan2(np.hypot(vx_c, vy_c), vz_c)
        ok = np.isfinite(th_ext)
        c3 = em.sample_cdf(th_ext[ok], th)
        res["plane"] = {"z_plane_mm": zp, "plane_offset_mm": a.plane_offset_mm, "n_crossed": int(ok.sum()),
                        "last_crossing_us": float(np.nanmax(t_c) * 1e6),
                        "equiv_hwhm_deg": math.degrees(em.equivalent_hwhm(c3, th)),
                        "median_deg": math.degrees(em.median_angle(c3, th))}
        if a.target_hwhm_deg:
            tgt = em.target_cdf(th, em.hwhm_to_sigma(math.radians(a.target_hwhm_deg)))
            res["plane"].update({"target_hwhm_deg": a.target_hwhm_deg, "vs_target_rms": em.cdf_rms(c3, tgt),
                                 "vs_target_ks": em.cdf_ks(c3, tgt)})
        if a.map2d:
            m, meta, _ = load_map(a.map2d)
            c2, _ = em.extractor_cdf(m, "beam", sig_hat, th)
            # per ion: the 2D map applied to each 3D ion's own launch angle (independent of how COMSOL samples)
            pred = np.interp(th0[ok], m.theta0, m.theta_ext)
            cp = em.sample_cdf(pred, th)
            ratio = th_ext[ok] / np.where(pred > 0, pred, np.nan)
            res["plane"].update({"map2d": Path(a.map2d).name,
                                 "pred2d_gaussian_slopes_equiv_hwhm_deg": math.degrees(em.equivalent_hwhm(c2, th)),
                                 "vs_2d_gaussian_slopes_ks": em.cdf_ks(c3, c2),
                                 "pred2d_per_ion_equiv_hwhm_deg": math.degrees(em.equivalent_hwhm(cp, th)),
                                 "vs_2d_per_ion_ks": em.cdf_ks(c3, cp),
                                 "angle_ratio_3d_over_2d_median": float(np.nanmedian(ratio)),
                                 "angle_ratio_3d_over_2d_iqr": [float(np.nanpercentile(ratio, 25)),
                                                                float(np.nanpercentile(ratio, 75))]})
        print(json.dumps(res["plane"], indent=1), flush=True)
        np.savez(LOGS / f"emission_check3d_{a.tag}.npz", sx=sx, sy=sy, theta_ext=th_ext, x_c=x_c, y_c=y_c, t_c=t_c)
        if a.target_hwhm_deg:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(1, 2, figsize=(11, 4.3), facecolor="#fcfcfb")
            ax[0].plot(np.degrees(th), tgt, color=C_TEXT2, lw=2, ls="--", label=f"target, HWHM {a.target_hwhm_deg:g} deg")
            if a.map2d:
                ax[0].plot(np.degrees(th), cp, color=C_SERIES[0], lw=2, label="2D map applied to the 3D launch angles")
            ax[0].plot(np.degrees(th), c3, color=C_SERIES[1], lw=2,
                       label=f"3D, {int(ok.sum())} ions, HWHM {res['plane']['equiv_hwhm_deg']:.1f} deg")
            style(ax[0], f"a  Fraction within theta at the plane (xmp {a.xmp})", "theta (deg)", "cumulative fraction")
            ax[0].legend(fontsize=7.5, frameon=False, loc="lower right")
            for cdf, col, ls, lb in [(tgt, C_TEXT2, "--", "target")] + ([(cp, C_SERIES[0], "-", "2D map, same launch")] if a.map2d else []) + [(c3, C_SERIES[1], "-", "3D")]:
                xb, yb = dIdOmega(cdf, th, bin_deg=2.0)
                ax[1].plot(xb, yb, color=col, lw=2, ls=ls, label=lb)
            ax[1].set_xlim(0, 70)
            style(ax[1], "b  dI/dOmega at the plane (2 deg bins)", "theta (deg)", "dI/dOmega (1/sr, normalized)")
            ax[1].legend(fontsize=7.5, frameon=False)
            fig.tight_layout()
            fig.savefig(LOGS / f"emission_check3d_{a.tag}.png", dpi=130)
    (LOGS / f"emission_check3d_{a.tag}.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    client.remove(model)   # never saved


def cmd_apply3d(a, cfg):
    client, model, path = start(cfg, "3d")
    out = path.with_name(a.out)
    if out.exists() or out.resolve() == path.resolve():
        sys.exit(f"refusing to overwrite {out}")
    j = model.java
    pb = pbeam(j)
    if "pbeam_xmp" in [str(n) for n in j.param().varnames()]:
        sys.exit("parameter pbeam_xmp already exists")
    old = str(pb.getString("xmp"))
    j.param().set("pbeam_xmp", a.xmp, f"Particle Beam transverse x'm (Gaussian); calibrated by "
                                      f"calibrate_emission.py: {a.note}")
    pb.set("xmp", "pbeam_xmp")
    print(f"pbeam1.xmp: {old} -> pbeam_xmp = {a.xmp}", flush=True)
    run(j, "std2")
    t = time.time()
    model.save(str(out))
    print(f"saved {out.name} in {time.time() - t:.0f} s (input {path.name} not saved)", flush=True)
    client.remove(model)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("map2d")
    p.add_argument("--plane-offset-mm", type=float, required=True, help="plane distance in front of the L1 front face")
    p.add_argument("--tag", default="ref")
    p.add_argument("--set", action="append", help="NAME=VALUE model parameter (repeatable)")
    p.add_argument("--n-rays", type=int, default=180)
    p.add_argument("--theta0-max-deg", type=float, default=89.5)
    p.add_argument("--t-end-us", type=float, default=20.0)
    p.add_argument("--dt-out-us", type=float, default=0.01)
    p = sub.add_parser("fit")
    p.add_argument("--target-hwhm-deg", type=float, required=True)
    p.add_argument("maps", nargs="+", help="map2d .npz files; the first is the reference")
    p = sub.add_parser("check3d")
    p.add_argument("--xmp", required=True, help="pbeam1 x'm (string, e.g. 0.5)")
    p.add_argument("--plane-offset-mm", type=float, default=0.0)
    p.add_argument("--t-end-us", type=float, required=True)
    p.add_argument("--dt-out-us", type=float, default=0.02)
    p.add_argument("--target-hwhm-deg", type=float)
    p.add_argument("--map2d")
    p.add_argument("--set", action="append")
    p.add_argument("--tag", default="check")
    p = sub.add_parser("apply3d")
    p.add_argument("--xmp", required=True)
    p.add_argument("--out", required=True, help="new .mph file name (next to the 3D model)")
    p.add_argument("--note", default="", help="text stored in the parameter description")
    a = ap.parse_args()
    cfg = load_config(ROOT / "config")
    {"map2d": cmd_map2d, "fit": cmd_fit, "check3d": cmd_check3d, "apply3d": cmd_apply3d}[a.cmd](a, cfg)


if __name__ == "__main__":
    main()
