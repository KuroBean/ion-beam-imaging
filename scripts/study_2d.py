"""2D studies for task 10 (cfg 3, the stored 3D geometry): voltage scan and model-tip-size sweep.

  scan   Author's starting point (2026-11-12): tip +10 V, extractor E1 -110 V, Einzel lens on L2-L4,
         rest grounded. Family A: L2 and L4 tied to E1 (LV2), L3 on LV3. Family B: L2, L4 grounded.
         L3 is scanned. MCP front -10 kV, mesh -1 kV.
  grid   Tip +10/+50/+100/+200 V x families A, B x L3 -300/-150/0 V (E1 -110 V).
  search Short Optuna (TPE) search maximizing the weight fraction on the active MCP over tip (LV1),
         E1 (LV2), L3 (LV3) and L2+L4 (LV4); rest grounded. A starting point for task 10, not the
         optimizer loop (optimize.py, which maximizes the resolution score).
  tip    One setting (--family, --l3) with the model tip face radius r_tip = 200/100/50/25 um
         (pre-acceleration on, launch.model_tip_radius_um follows r_tip, tip mesh hmax = r_tip/5),
         plus pre-acceleration off at 100 um, and n_theta 51 at 100 um. Answers whether a smaller
         model tip changes the result, i.e. how good the pre-acceleration stand-in is.

Runs in-process (one COMSOL session, 2D model loaded once, never saved); results in results/<job_id>,
summary in logs/study_2d_<mode>.json and a table on stdout.

Usage:  .venv\\Scripts\\python.exe scripts\\study_2d.py scan | grid | search [--trials 50]
        .venv\\Scripts\\python.exe scripts\\study_2d.py tip --family A --l3 -200 --tip 10
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ionopt.checker import check  # noqa: E402
from ionopt.config import ConfigurationDef, load_config  # noqa: E402
from ionopt.jobs import build_job  # noqa: E402
from ionopt.results import execute, prepare_job_dir  # noqa: E402
from ionopt.worker.comsol_worker import ComsolRunner  # noqa: E402

MM = 1e-3
POSITIONS = {"lens_gap": 13.482 * MM, "z_mcp": 410.9 * MM, "mesh_gap": 12.7 * MM}   # stored 3D geometry, cfg 3
HV = {"HV1": -10000.0, "HV4": -1000.0}
WIRING = {"A": {"tip": "LV1", "e1": "LV2", "e2": "LV2", "e4": "LV2", "e3": "LV3"},
          "B": {"tip": "LV1", "e1": "LV2", "e3": "LV3"},
          "S": {"tip": "LV1", "e1": "LV2", "e3": "LV3", "e2": "LV4", "e4": "LV4"}}   # search: A and B are special cases
SEARCH_RANGES = {"LV1": (0.0, 300.0), "LV2": (-300.0, 300.0), "LV3": (-300.0, 300.0), "LV4": (-300.0, 300.0)}
SCAN = [("A", v) for v in (-300, -200, -100, 0, 5)] + [("B", v) for v in (-300, -150, -75, -30)]
TIP_UM = (200, 100, 50, 25)
GRID_TIP = (10, 50, 100, 200)       # E1 stays at -110 V
GRID_L3 = (-300, -150, 0)


def setting(family: str, l3: float, tip_v: float = 10.0, e1_v: float = -110.0, lv4: float | None = None):
    conf = ConfigurationDef(config_id=f"task10_{family}", description=f"family {family}", cfg=3,
                            wiring=WIRING[family])
    ch = {"LV1": tip_v, "LV2": e1_v, "LV3": float(l3), **HV}
    if lv4 is not None:
        ch["LV4"] = float(lv4)
    return conf, ch


def summarize(name: str, out: Path, meta, m) -> dict:
    row = {"case": name, "job_id": meta.job_id, "status": meta.status, "error": meta.error}
    if meta.status != "success":
        return row
    d = pd.read_csv(out / "ions_derived.csv")
    mcp = d[d.fate == "mcp_active"]
    row.update({
        "valid": m.valid, "score": m.score, "flags": m.flags,
        "fates": {k: round(v, 3) for k, v in m.fates.items() if v},
        "eta": m.requirements.get("eta"), "spot": {k: m.spot.get(k) for k in ("rms_axis_mm", "r90_mm", "r_max_mm")},
        "monotonic": m.mapping.get("monotonic"), "theta_eval_max_deg": m.mapping.get("eval_theta_max_deg"),
        "KE0_eV": float(d.KE0_eV.iloc[0]),
        "E_err_rel_max": float(d.energy_error_rel.abs().max()), "E_err_eV_max": float(d.energy_error_eV.abs().max()),
        "tof_mcp_us": [round(float(mcp.tof_us.min()), 1), round(float(mcp.tof_us.max()), 1)] if len(mcp) else None,
        "r_land_mm": mcp.groupby("theta_deg").r_land_mm.mean().round(3).to_dict() if len(mcp) else {},
        "timings_s": meta.model_extra.get("timings_s"), "mesh_elements": meta.mesh_elements,
        "preacceleration": meta.model_extra.get("preacceleration"),
        "v_tip_model": (meta.model_extra.get("comsol_params") or {}).get("v_tip"),
    })
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["scan", "grid", "tip", "search"])
    ap.add_argument("--trials", type=int, default=50)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--family", choices=["A", "B"], default="A")
    ap.add_argument("--l3", type=float, default=-200.0)
    ap.add_argument("--tip", type=float, default=10.0)
    a = ap.parse_args()
    logging.basicConfig(level=logging.WARNING)
    base = load_config(ROOT / "config", override_files=[ROOT / "config" / "dev_overrides.yaml"])
    runner = ComsolRunner(base)

    cases = []          # (name, overrides, family, l3, r_tip_um or None)
    if a.mode == "scan":
        cases = [(f"{f} L3={v:+g}", [], f, v, None, 10.0) for f, v in SCAN]
    elif a.mode == "grid":
        cases = [(f"{f} tip={t:+g} L3={v:+g}", [], f, v, None, t) for t in GRID_TIP for f in "AB" for v in GRID_L3]
    else:
        f, v = a.family, a.l3
        t = a.tip
        cases = [(f"{f} tip={t:+g} L3={v:+g} r_tip={r}um", [f"spec.launch.model_tip_radius_um={r}"], f, v, r, t)
                 for r in TIP_UM]
        cases += [(f"{f} tip={t:+g} L3={v:+g} r_tip=100um preaccel off", ["spec.launch.preaccel=false"], f, v, 100, t),
                  (f"{f} tip={t:+g} L3={v:+g} r_tip=100um n_theta=51", ["spec.launch.n_theta=51"], f, v, 100, t)]

    rows, state = [], {"tip": None}

    def run_case(name, ov, conf, ch, r_tip=None):
        cfg = base.with_overrides(ov)
        job = build_job(cfg, conf, ch, POSITIONS, fidelity="2d", tags={"purpose": f"task10_study_{a.mode}", "case": name})
        if r_tip is not None and r_tip != state["tip"]:
            ad = runner.adapter("2d")
            comp = ad.j.component("comp1")
            ad.j.param().set("r_tip", f"{r_tip / 1000}[mm]")
            comp.mesh("mesh1").feature("ftri1").feature("s_tip").set("hmax", f"{min(0.02, r_tip / 1000 / 5)}")
            t = time.time()
            comp.geom("geom1").run()
            comp.mesh("mesh1").run()
            print(f"r_tip = {r_tip} um: remeshed in {time.time() - t:.0f} s, {comp.mesh('mesh1').getNumElem()} elements",
                  flush=True)
            state["tip"] = r_tip
        out = prepare_job_dir(job, cfg, cfg.path("results_dir") / job.job_id)
        t = time.time()
        meta = execute(job, cfg, out, runner, backend="study_2d")
        m = check(out, cfg) if meta.status == "success" else None
        row = summarize(name, out, meta, m)
        row["channels"] = ch
        row["wiring"] = conf.wiring
        rows.append(row)
        print(f"[{time.time() - t:4.0f} s] {name:34s} " + (
            f"fates {row['fates']} eta {row['eta']:.3f} score {row['score']} rms {row['spot']['rms_axis_mm']} "
            f"KE0 {row['KE0_eV']:.1f} Emax {row['E_err_rel_max']:.2g}/{row['E_err_eV_max']:.2g}eV "
            f"tof {row['tof_mcp_us']} flags {row['flags']}" if meta.status == "success" else f"{meta.status}: {meta.error}"),
            flush=True)
        return row

    if a.mode == "search":
        import optuna   # noqa: PLC0415
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=a.seed))
        # seed with the best grid settings and the author's starting point
        study.enqueue_trial({"LV1": 200.0, "LV2": -110.0, "LV3": -300.0, "LV4": 0.0})
        study.enqueue_trial({"LV1": 100.0, "LV2": -110.0, "LV3": -150.0, "LV4": 0.0})
        study.enqueue_trial({"LV1": 10.0, "LV2": -110.0, "LV3": -200.0, "LV4": -110.0})

        def objective(trial):
            v = {k: trial.suggest_float(k, lo, hi) for k, (lo, hi) in SEARCH_RANGES.items()}
            conf, ch = setting("S", v["LV3"], v["LV1"], v["LV2"], v["LV4"])
            name = f"S #{trial.number} " + " ".join(f"{k}={x:+.0f}" for k, x in v.items())
            row = run_case(name, [], conf, ch)
            return float((row.get("fates") or {}).get("mcp_active", 0.0)) if row["status"] == "success" else 0.0

        study.optimize(objective, n_trials=a.trials)
        best = sorted(rows, key=lambda r: -(r.get("fates") or {}).get("mcp_active", 0.0))[:8]
        print("\nbest by MCP fraction:")
        for r in best:
            print(f"  {r['case']:44s} mcp {(r.get('fates') or {}).get('mcp_active', 0):.3f} rms {(r.get('spot') or {}).get('rms_axis_mm')} "
                  f"theta_max {r.get('theta_eval_max_deg')} score {r.get('score')} {r['job_id']}")
    else:
        for name, ov, fam, l3, r_tip, tip_v in cases:
            conf, ch = setting(fam, l3, tip_v)
            run_case(name, ov, conf, ch, r_tip)
    runner.close()
    out = ROOT / "logs" / f"study_2d_{a.mode}.json"
    out.write_text(json.dumps(rows, indent=1, default=str))
    print(f"wrote {out}")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Total {time.time() - t0:.0f} s")
