"""Find particle time-stepping settings that fix the 3D model's energy error
without remeshing.  Works on an in-memory copy; nothing is saved.

Runs the 3D particle study (sol2) for a short window with fewer particles and
reports, for each solver variant, the energy-conservation error
Ek - (E0 - qV) at a few times plus the solve time.

Usage:  .venv\\Scripts\\python.exe scripts\\tune_3d_timestepping.py [variant ...]
"""
import sys
import time

import numpy as np

from comsol_session import MODEL_FILE, load, start
from compare_axis import eval_points
from compare_particles import particle_data

E_CHARGE = 1.602176634e-19
N_TEST = "100"
TLIST = "range(0,0.5e-6,10e-6)"

VARIANTS = {
    "baseline": {},
    "genalpha_tol": {"rtol": "1e-6", "atolfactor": ["comp1_qcpt", "0.001", "comp1_V", "0.1"]},
    "genalpha_maxstep": {"maxstepconstraintgenalpha": "const", "maxstepgenalpha": "2e-9"},
    "dopri5_tol": {"timemethod": "rk", "rkmethod": "dopri5", "rtol": "1e-6",
                   "atolfactor": ["comp1_qcpt", "0.001", "comp1_V", "0.1"]},
}


def energy_report(model, label, dt):
    x, y, z, ep = particle_data(model, ["qx", "qy", "qz", "cpt.Ep"])
    e0 = 0.5 * 1.7e-24 * 434.2 ** 2 / E_CHARGE
    out = []
    for k in (2, 10, 20):
        ok = np.isfinite(z[:, k]) & (z[:, k] > 105.05)
        V = eval_points(model, "dset1", np.vstack([x[ok, k], y[ok, k], z[ok, k]]))
        err = ep[ok, k] / E_CHARGE - (e0 - V)
        out.append(f"t={k*0.5:4.1f}us: {np.nanmedian(err):+6.2f} [{np.nanpercentile(err,5):+6.2f},{np.nanpercentile(err,95):+6.2f}]")
    print(f"{label:18s} solve {dt:7.1f} s | energy error eV median [5%,95%]  " + "  ".join(out), flush=True)


def main():
    names = sys.argv[1:] or list(VARIANTS)
    client = start()
    model = load(client, MODEL_FILE)
    j = model.java
    j.component("comp1").physics("cpt").feature("pbeam1").set("N", N_TEST)
    t1 = j.sol("sol2").feature("t1")
    base = {p: t1.getString(p) for p in ("timemethod", "rtol", "maxstepconstraintgenalpha", "maxstepgenalpha",
                                         "rkmethod")}
    base_atol = [str(s) for s in t1.getStringArray("atolfactor")]
    for name in names:
        # reset to stored settings, then apply the variant
        for p, v in base.items():
            t1.set(p, v)
        t1.set("atolfactor", base_atol)
        t1.set("tlist", TLIST)
        for p, v in VARIANTS[name].items():
            t1.set(p, v)
        t = time.time()
        j.sol("sol2").runAll()
        energy_report(model, name, time.time() - t)
    client.clear()


if __name__ == "__main__":
    main()
