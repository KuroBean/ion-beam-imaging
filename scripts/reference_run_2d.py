"""Task 9: independent reference for one worker job (plain MPh, no ionopt adapter code).

Loads the 2D base model, applies exactly the COMSOL parameter values the worker recorded
(meta.json "comsol_params", i.e. what a person would type in the GUI), points the release node at the
job's release.txt, sets the same particle tolerance, solves Study 1 then Study 2, and compares the final
particle states with the worker's ions_final.csv. Also writes <result>/gui_reference.txt with the same
settings as a checklist for a manual GUI run. Never saves the model.

Usage:  .venv\\Scripts\\python.exe scripts\\reference_run_2d.py results\\<job_id>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import jpype
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from compare_particles import particle_data  # noqa: E402  (independent of ionopt.worker)
from introspect_models import setup_mph  # noqa: E402
from ionopt.config import load_config  # noqa: E402

E = 1.602176634e-19


def gui_text(model_file, params, rel_file, rtol):
    lines = [f"Manual GUI reference run for {rel_file.parent.name}", "",
             f"1. Open {model_file} (do not save over it; Save As a copy if needed).",
             "2. Global Definitions > Parameters: set", *[f"     {k:12s} = {v}" for k, v in params.items()],
             "3. Charged Particle Tracing > 'Release: 3D beam initial conditions' (relf1):",
             f"     Filename = {rel_file}", "     Initial velocity: From file; then Import.",
             f"4. Solver Configurations > Solution 2 > Time-Dependent Solver 1: Relative tolerance = {rtol}",
             "5. Build geometry, Build mesh; Compute Study 1, then Study 2.",
             "6. Compare final positions / energies with ions_final.csv (plan coordinates: z = z_model - tip_z)."]
    return "\n".join(lines) + "\n"


def main():
    d = Path(sys.argv[1]).resolve()
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    params = meta["comsol_params"]
    rtol = meta.get("particle_rtol", "1e-9")
    cfg = load_config(ROOT / "config")
    model_file = ROOT / meta["model_file"]
    rel_file = d / "release.txt"
    (d / "gui_reference.txt").write_text(gui_text(model_file, params, rel_file, rtol), encoding="utf-8")

    mph = setup_mph(cfg.paths.comsol_root)
    client = mph.start()
    model = client.load(str(model_file))
    j = model.java
    for k, v in params.items():
        j.param().set(k, v)
    rel = j.component("comp1").physics("cpt").feature("relf1")
    rel.set("Filename", str(rel_file))
    rel.set("InitialVelocity", "FromFile")
    rel.set("icolp", jpype.JInt(0))
    rel.set("icolv", jpype.JInt(2))
    rel.importData()
    j.sol("sol2").feature("t1").set("rtol", rtol)
    j.component("comp1").geom("geom1").run()
    j.component("comp1").mesh("mesh1").run()
    model.solve("Study 1 - electrostatics")
    model.solve("Study 2 - particle tracing")
    tip_mm = float(j.param().evaluate("tip_z")) * 1e3
    a = particle_data(model, ["qr", "qz", "cpt.vr", "cpt.vz", "cpt.Ep"])     # [expr, particle, time]
    client.remove(model)

    last = np.isfinite(a[1]).sum(axis=1) - 1
    i = np.arange(a.shape[1])
    r, z, vr, vz, ep = (a[k][i, last] for k in range(5))
    ref = pd.DataFrame({"ion_id": i, "r_m": r * 1e-3, "z_m": (z - tip_mm) * 1e-3, "vr": vr, "vz": vz, "KE_eV": ep / E})
    w = pd.read_csv(d / "ions_final.csv").sort_values("ion_id").reset_index(drop=True)
    w["r_m"] = np.hypot(w.x_m, w.y_m)
    out = {"n_worker": len(w), "n_reference": len(ref)}
    for col, wcol in (("r_m", "r_m"), ("z_m", "z_m"), ("vr", "vx_mps"), ("vz", "vz_mps"), ("KE_eV", "KE_eV")):
        diff = np.abs(ref[col].to_numpy() - w[wcol].to_numpy())
        out[f"max_abs_diff_{col}"] = float(np.nanmax(diff))
    print(json.dumps(out, indent=1))
    (d / "reference_comparison.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    ok = out["n_worker"] == out["n_reference"] and out["max_abs_diff_r_m"] < 1e-9 and out["max_abs_diff_z_m"] < 1e-9 \
        and out["max_abs_diff_KE_eV"] < 1e-6
    print("RESULT:", "IDENTICAL (worker == independent reference)" if ok else "DIFFERENT, see above")
    print(f"GUI checklist: {d / 'gui_reference.txt'}")


if __name__ == "__main__":
    main()
