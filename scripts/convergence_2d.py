"""Numerical convergence check of the 2D axisymmetric model.

Runs the saved 2D model at the baseline settings, with a 2x finer mesh, and
with a 10x tighter particle-tracing tolerance, and reports MCP spot statistics,
crossover position and energy-conservation error for each.

Usage:  .venv\\Scripts\\python.exe scripts\\convergence_2d.py
"""
import time

import numpy as np

from comsol_session import PROJECT_DIR, load, start
from compare_axis import eval_points
from compare_particles import particle_data

E_CHARGE = 1.602176634e-19


def stats(model, label):
    r, z, ep = particle_data(model, ["qr", "qz", "cpt.Ep"])
    rf, zf = r[:, -1], z[:, -1]
    hit = np.isfinite(zf) & (np.abs(zf - 515.9) < 0.05)
    # crossover: z where each particle first returns to the axis after leaving it
    zc = []
    for i in range(r.shape[0]):
        k = np.nonzero((np.abs(r[i, 20:]) < 0.05))[0]
        if len(k):
            zc.append(z[i, 20 + k[0]])
    # energy error at t index 100 (100 us)
    k = 100
    ok = np.isfinite(z[:, k]) & (z[:, k] > 105.05) & (z[:, k] < 515.8)
    V = eval_points(model, "dset1", np.vstack([r[ok, k], z[ok, k]]))
    e0 = 0.5 * 1.7e-24 * 434.2 ** 2 / E_CHARGE
    err = ep[ok, k] / E_CHARGE - (e0 - V)
    rh = rf[hit]
    print(f"{label:28s} hits {hit.sum():4d}  spot r_rms {np.sqrt(np.mean(rh**2)):.3f}  r50 {np.median(rh):.3f}  "
          f"r90 {np.percentile(rh, 90):.3f} mm  crossover z {np.median(zc):.2f} mm  "
          f"energy err {np.median(err):+.2f} eV", flush=True)


def solve(model):
    t = time.time()
    model.solve("Study 1 - electrostatics")
    model.solve("Study 2 - particle tracing")
    return time.time() - t


def main():
    client = start()
    model = load(client, PROJECT_DIR / "lens8_axisym.mph")
    j = model.java
    mesh = j.component("comp1").mesh("mesh1")
    stats(model, "baseline (saved)")

    # 2x finer mesh everywhere
    ft = mesh.feature("ftri1")
    mesh.feature("size").set("hmax", "2")
    for t in ft.feature().tags():
        f = ft.feature(t)
        try:
            h = float(f.getString("hmax"))
            f.set("hmax", str(h / 2))
        except Exception:
            pass
    mesh.run()
    print(f"fine mesh: {mesh.getNumElem()} elements", flush=True)
    dt = solve(model)
    stats(model, f"mesh x2 finer ({dt:.0f} s)")

    # tighter time-stepping tolerance for particle tracing
    for s in j.sol().tags():
        for ft_ in j.sol(s).feature().tags():
            f = j.sol(s).feature(ft_)
            if str(f.getType()) == "Time":
                f.set("rtol", "1e-6")
    t = time.time()
    model.solve("Study 2 - particle tracing") if False else j.sol("sol2").runAll()
    stats(model, f"mesh x2 + rtol 1e-6 ({time.time()-t:.0f} s)")
    client.clear()


if __name__ == "__main__":
    main()
