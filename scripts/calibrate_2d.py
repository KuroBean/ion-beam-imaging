"""Calibrate a 2D-model parameter against the 3D potential (e.g. R_cross, the effective radius of the
-1 kV screen-cross ring that stands in for the non-axisymmetric cross arms).

Uses the 3D values stored by compare_axis.py (3D at azimuth 0 deg), so the 3D model is not reloaded.
For each value the 2D geometry and mesh are rebuilt and Study 1 (electrostatics) is re-solved.
Score: rms |V2D - V3D| on r = 0, 10, 30 mm over the window drift end .. MCP front.

Usage:  .venv\\Scripts\\python.exe scripts\\calibrate_2d.py axis.npz 2d.mph PARAM UNIT v1 v2 ...
   e.g. ... logs\\compare_axis.npz lens8_axisym_asm.mph R_cross mm 15 21 25 30 35 40 45.4
"""
import sys

import numpy as np

from compare_axis import eval_points
from comsol_session import load, start


def main():
    npz, path, param, unit = sys.argv[1:5]
    vals = [float(x) for x in sys.argv[5:]]
    d = np.load(npz)
    z = d["z"]
    client = start()
    m = load(client, path)
    j = m.java
    comp = j.component("comp1")
    mcp = j.param().evaluate("mcp_z") * 1e3
    win = (z > mcp - 70) & (z < mcp - 5)
    print(f"{param}: window z {mcp-70:.0f}..{mcp-5:.0f} mm; 3D reference {npz}; current {j.param().get(param)}")
    best = None
    for v in vals:
        j.param().set(param, f"{v:g}[{unit}]" if unit != "-" else f"{v:g}")
        comp.geom("geom1").run()
        comp.mesh("mesh1").run()
        j.study("std1").run()
        rms = []
        for r in (0, 10, 30):
            v2 = eval_points(m, "dset1", np.vstack([np.full_like(z, r), z]))
            diff = (v2 - d[f"V3d_r{r}_a0"])[win]
            diff = diff[np.isfinite(diff)]
            rms.append(np.sqrt(np.mean(diff**2)))
        tot = np.sqrt(np.mean(np.square(rms)))
        print(f"{param}={v:6.2f}: rms |V2D-V3D| r=0 {rms[0]:6.1f} V, r=10 {rms[1]:6.1f} V, r=30 {rms[2]:6.1f} V"
              f"  (combined {tot:6.1f} V)", flush=True)
        if best is None or tot < best[1]:
            best = (v, tot)
    print(f"best {param} = {best[0]:g} (combined rms {best[1]:.1f} V)")
    client.clear()


if __name__ == "__main__":
    main()
