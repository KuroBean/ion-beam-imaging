"""Sweep the effective screen-cross radius R_cross in the 2D model and compare
the potential near the screen/MCP with the 3D model (from compare_axis.npz).

Usage:  .venv\\Scripts\\python.exe scripts\\tune_cross.py [R1 R2 ...]
"""
import sys
import time

import numpy as np

from comsol_session import PROJECT_DIR, load, start
from compare_axis import eval_points

OUT = PROJECT_DIR / "logs"


def main():
    radii = [float(x) for x in sys.argv[1:]] or [8.485, 15, 20, 25, 30, 35, 40, 45.4]
    ref = dict(np.load(OUT / "compare_axis.npz"))
    z = ref["z"]
    win = (z > 300) & (z < 515)
    ref0 = ref["V3d_r0_a0"]
    ref10 = np.nanmean([ref[f"V3d_r10_a{a}"] for a in (0, 45, 90, 135)], axis=0)
    ref30 = np.nanmean([ref[f"V3d_r30_a{a}"] for a in (0, 45, 90, 135)], axis=0)

    client = start()
    model = load(client, PROJECT_DIR / "lens8_axisym.mph")
    j = model.java
    rows = []
    curves = {}
    for R in radii:
        j.param().set("R_cross", f"{R}[mm]")
        t = time.time()
        j.component("comp1").mesh("mesh1").run()
        model.solve("Study 1 - electrostatics")
        out = []
        for r, refv in ((0, ref0), (10, ref10), (30, ref30)):
            v = eval_points(model, "dset1", np.vstack([np.full_like(z, r), z]))
            curves[f"R{R}_r{r}"] = v
            ok = win & np.isfinite(v) & np.isfinite(refv)
            out.append(np.sqrt(np.mean((v[ok] - refv[ok]) ** 2)))
        rows.append((R, *out))
        print(f"R_cross={R:6.2f} mm  RMS dV (z 300-515):  r=0: {out[0]:7.1f} V   r=10: {out[1]:7.1f} V   "
              f"r=30: {out[2]:7.1f} V   ({time.time()-t:.1f} s)", flush=True)
    client.clear()
    np.savez_compressed(OUT / "tune_cross.npz", z=z, rows=np.array(rows), **curves)
    best = min(rows, key=lambda x: x[1] + x[2])
    print(f"best (r=0 + r=10): R_cross = {best[0]} mm", flush=True)


if __name__ == "__main__":
    main()
