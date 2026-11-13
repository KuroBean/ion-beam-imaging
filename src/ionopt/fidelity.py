"""Fidelity check (plan 9.10 / task 10): how much do 2D and 3D differ on the same setting?

For each pair of finished jobs (same channels, wiring, positions and launch; one 2D, one 3D) this
compares what the optimizer and the checker use: fates and collection efficiency, the mapping
r(theta) and its resolution dtheta(theta), the spot statistics, and per-angle fates (3D: fraction
of the azimuths that end where the 2D ray ends).

The 3D mapping is already azimuth-averaged by the checker (mean landing radius per theta), so the
two r(theta) curves are directly comparable on the shared theta grid.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

SPOT_KEYS = ("rms_axis_mm", "r50_mm", "r90_mm", "r_max_mm", "centroid_offset_mm", "tof_mean_us", "impact_KE_mean_eV")


def _load(d: Path) -> tuple[dict, pd.DataFrame]:
    d = Path(d)
    return json.loads((d / "metrics.json").read_text()), pd.read_csv(d / "ions_derived.csv")


def _rel(a, b):
    if a is None or b is None:
        return None
    return float((b - a) / abs(a)) if a else None


def compare_runs(dir_2d: Path, dir_3d: Path) -> dict:
    """2D vs 3D differences for one setting (3D minus 2D; rel = (3D - 2D) / |2D|)."""
    m2, d2 = _load(dir_2d)
    m3, d3 = _load(dir_3d)
    out: dict = {"job_2d": m2["job_id"], "job_3d": m3["job_id"], "valid_2d": m2["valid"], "valid_3d": m3["valid"]}

    # fates and collection efficiency
    out["fates_2d"] = m2["fates"]
    out["fates_3d"] = m3["fates"]
    out["fate_diff"] = {k: m3["fates"].get(k, 0.0) - v for k, v in m2["fates"].items()}
    e2, e3 = m2["requirements"]["eta"], m3["requirements"]["eta"]
    out["eta"] = {"2d": e2, "3d": e3, "diff": e3 - e2, "rel": _rel(e2, e3)}

    # per-theta fate agreement (2D: one ray per theta and energy; 3D: n_phi rays)
    a = d2.groupby(["theta_deg", "KE0_eV"]).surface.first().rename("surface_2d").reset_index()
    a["theta_deg"] = a.theta_deg.round(6)
    b = d3.assign(theta_deg=d3.theta_deg.round(6)).merge(a, on=["theta_deg", "KE0_eV"], how="left")
    b["same"] = b.surface == b.surface_2d
    agree = b.groupby("theta_deg").same.mean()
    w = d3.assign(theta_deg=d3.theta_deg.round(6)).groupby("theta_deg").weight.sum()
    out["fate_agreement"] = {"weighted": float((agree * w).sum() / w.sum()),
                             "per_theta": {float(k): round(float(v), 3) for k, v in agree.items()}}

    # mapping r(theta) and dtheta on the shared grid, where both land >= eval fraction
    mp2, mp3 = m2["mapping"], m3["mapping"]
    t2, t3 = np.round(mp2["theta_deg"], 6), np.round(mp3["theta_deg"], 6)
    common = sorted(set(t2) & set(t3))
    i2 = {t: i for i, t in enumerate(t2)}
    i3 = {t: i for i, t in enumerate(t3)}
    rows = []
    for t in common:
        j2, j3 = i2[t], i3[t]
        r2, r3 = mp2["r_mm"][j2], mp3["r_mm"][j3]
        dt2, dt3 = mp2["dtheta_deg"][j2], mp3["dtheta_deg"][j3]
        rows.append({"theta_deg": float(t), "r_2d_mm": r2, "r_3d_mm": r3,
                     "landed_2d": mp2["landed_frac"][j2], "landed_3d": mp3["landed_frac"][j3],
                     "dtheta_2d_deg": dt2, "dtheta_3d_deg": dt3})
    df = pd.DataFrame(rows)
    both = df[(df.landed_2d >= 0.99) & (df.landed_3d >= 0.99)].dropna(subset=["r_2d_mm", "r_3d_mm"]) if len(df) else df
    out["mapping"] = {
        "n_theta_both_landed": int(len(both)),
        "theta_max_both_deg": float(both.theta_deg.max()) if len(both) else None,
        "dr_max_mm": float((both.r_3d_mm - both.r_2d_mm).abs().max()) if len(both) else None,
        "dr_rms_mm": float(np.sqrt(((both.r_3d_mm - both.r_2d_mm) ** 2).mean())) if len(both) else None,
        "dtheta_rel_median": float(((both.dtheta_3d_deg - both.dtheta_2d_deg) / both.dtheta_2d_deg.abs()).median())
        if len(both) else None,
        "eval_theta_max_deg": {"2d": mp2.get("eval_theta_max_deg"), "3d": mp3.get("eval_theta_max_deg")},
        "score": {"2d": m2.get("score"), "3d": m3.get("score"), "rel": _rel(m2.get("score"), m3.get("score"))},
        "monotonic": {"2d": mp2.get("monotonic"), "3d": mp3.get("monotonic")},
        "table": df.round(4).to_dict(orient="records"),
    }
    out["spot"] = {k: {"2d": m2["spot"].get(k), "3d": m3["spot"].get(k), "diff": (
        None if m2["spot"].get(k) is None or m3["spot"].get(k) is None else m3["spot"][k] - m2["spot"][k])}
        for k in SPOT_KEYS}
    return out


def summarize(pairs: list[dict]) -> dict:
    """Across settings: the worst and median 2D-vs-3D differences."""
    def col(f):
        v = [f(p) for p in pairs]
        v = [x for x in v if x is not None and np.isfinite(x)]
        return {"median": float(np.median(v)), "max_abs": float(np.max(np.abs(v)))} if v else None

    return {
        "n_settings": len(pairs),
        "eta_diff": col(lambda p: p["eta"]["diff"]),
        "fate_agreement": col(lambda p: p["fate_agreement"]["weighted"]),
        "dr_max_mm": col(lambda p: p["mapping"]["dr_max_mm"]),
        "dr_rms_mm": col(lambda p: p["mapping"]["dr_rms_mm"]),
        "dtheta_rel_median": col(lambda p: p["mapping"]["dtheta_rel_median"]),
        "score_rel": col(lambda p: p["mapping"]["score"]["rel"]),
        "rms_axis_diff_mm": col(lambda p: p["spot"]["rms_axis_mm"]["diff"]),
        "r90_diff_mm": col(lambda p: p["spot"]["r90_mm"]["diff"]),
        "centroid_offset_3d_mm": col(lambda p: p["spot"]["centroid_offset_mm"]["3d"]),
    }


# --------------------------------------------------------------------------- running a check


def load_settings(path: Path) -> list[dict]:
    """Settings file (JSON list): {name, cfg, wiring, channels (V), positions_mm {lens_gap, z_mcp, mesh_gap}}."""
    s = json.loads(Path(path).read_text())
    for x in s:
        missing = {"name", "cfg", "wiring", "channels", "positions_mm"} - set(x)
        if missing:
            raise ValueError(f"setting {x.get('name')!r} lacks {sorted(missing)}")
    return s


def run_fidelity_check(cfg, settings: list[dict], run_worker_inline: bool = True, log=print) -> dict:
    """Submit every setting as a 2D and a 3D job, run them, check them, compare each pair.

    With the queue backend and run_worker_inline, a COMSOL worker in this process works the queue until
    it is empty (2D jobs are submitted first). Writes results/fidelity_<timestamp>.json.
    """
    import time

    from . import units
    from .backends import make_backend
    from .checker import check
    from .config import ConfigurationDef
    from .jobs import build_job
    from .plots import make_plots

    backend = make_backend(cfg)
    jobs = {"2d": [], "3d": []}
    for fid in ("2d", "3d"):
        for s in settings:
            conf = ConfigurationDef(config_id=f"fidelity_{s['name']}", description=s.get("description", ""),
                                    cfg=s["cfg"], wiring=s["wiring"])
            pos = {k: v * units.MM for k, v in s["positions_mm"].items()}
            job = build_job(cfg, conf, s["channels"], pos, fidelity=fid,
                            tags={"purpose": "fidelity_check", "setting": s["name"]})
            jobs[fid].append(backend.submit(job))
            log(f"submitted {fid} {s['name']}: {jobs[fid][-1]}")
    if getattr(backend, "name", "") == "queue" and run_worker_inline:
        from .worker.comsol_worker import run_worker
        t = time.time()
        n = run_worker(cfg, stop_when_empty=True)
        log(f"worker processed {n} jobs in {time.time() - t:.0f} s")

    pairs, failed = [], []
    for s, j2, j3 in zip(settings, jobs["2d"], jobs["3d"]):
        dirs = {}
        for fid, jid in (("2d", j2), ("3d", j3)):
            b = backend.fetch(jid)
            if b.status != "success":
                failed.append({"setting": s["name"], "fidelity": fid, "job_id": jid, "error": b.error})
                continue
            check(Path(b.result_dir), cfg)
            make_plots(Path(b.result_dir), cfg)
            dirs[fid] = Path(b.result_dir)
        if len(dirs) == 2:
            c = compare_runs(dirs["2d"], dirs["3d"])
            c["setting"] = s["name"]
            c["timings_3d_s"] = backend.fetch(j3).meta.model_extra.get("timings_s")
            pairs.append(c)
            log(f"{s['name']}: eta 2D {c['eta']['2d']:.3f} 3D {c['eta']['3d']:.3f}, fate agreement "
                f"{c['fate_agreement']['weighted']:.3f}, dr max {c['mapping']['dr_max_mm']} mm")
    report = {"settings": settings, "pairs": pairs, "failed": failed, "summary": summarize(pairs) if pairs else None}
    out = cfg.path("results_dir") / f"fidelity_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, default=str))
    report["path"] = str(out)
    log(f"wrote {out}")
    return report
