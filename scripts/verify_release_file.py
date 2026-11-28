"""Task 8: check that COMSOL reads ionopt's release files the way launch.py writes them.

For one model (2d or 3d, from config/paths.yaml) this, IN MEMORY ONLY (never saved):
  1. writes a small test launch with ionopt.launch.write_release_file (the real code path),
     ions at distinct off-axis positions and velocities so row order and columns can be told apart;
  2. adds a ReleaseFromDataFile node (or reuses the model's), disables the other release
     features, points it at the file;
  3. runs the particle study for a short time (T_TEST);
  4. reads every particle's position and velocity at t = 0 and compares with the file.

Usage:  .venv\\Scripts\\python.exe scripts\\verify_release_file.py 2d|3d
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import jpype
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from introspect_models import setup_mph, tags  # noqa: E402
from ionopt import units  # noqa: E402
from ionopt.config import load_config  # noqa: E402
from ionopt.launch import write_release_file  # noqa: E402

T_TEST = "range(0,1e-8,1e-7)"     # 0.1 us, enough to start every ion
REL_TAG = "relf_verify"
RELEASE_TYPES = ("ReleaseFromDataFile", "ParticleBeam", "Release", "Inlet", "ReleaseFromGrid", "ReleaseFromEdge",
                 "ReleaseFromPoint", "ReleaseFromBoundary", "ReleaseFromDomain")


def test_launch(fid: str) -> pd.DataFrame:
    """6 ions with distinct start points (a few um off the tip) and velocities."""
    k = np.arange(6)
    phi = np.deg2rad(30.0 * k + 10.0) if fid == "3d" else np.zeros(6)
    r0 = (1.0 + k) * 1e-6                 # m
    th = np.deg2rad(5.0 + 7.0 * k)
    v = 400.0 + 37.0 * k                  # m/s
    return pd.DataFrame({
        "ion_id": k, "x_m": r0 * np.cos(phi), "y_m": r0 * np.sin(phi), "z_m": (2.0 + k) * 1e-6,
        "vx_mps": v * np.sin(th) * np.cos(phi), "vy_mps": v * np.sin(th) * np.sin(phi), "vz_mps": v * np.cos(th)})


def particle_t0(j, sol: str, exprs: list[str]) -> np.ndarray:
    ds = j.result().dataset()
    for t in ("part_vrf",):
        if t in tags(ds):
            ds.remove(t)
    p = ds.create("part_vrf", "Particle")
    p.set("solution", sol)
    ev = j.result().numerical().create("pev_vrf", "Particle")
    ev.set("data", "part_vrf")
    ev.set("innerinput", "first")
    out = []
    for e in exprs:
        ev.set("expr", e)
        out.append(np.array([row[0] for row in ev.getReal()]))
    j.result().numerical().remove("pev_vrf")
    ds.remove("part_vrf")
    return np.array(out)


def main():
    fid = sys.argv[1]
    cfg = load_config(ROOT / "config")
    mph = setup_mph(cfg.paths.comsol_root)
    client = mph.start()
    t = time.time()
    model = client.load(str(cfg.path(f"models.{fid}")))
    print(f"loaded in {time.time() - t:.0f} s", flush=True)
    j = model.java
    comp = j.component("comp1")
    cpt = comp.physics("cpt")
    tip_z_m = float(j.param().evaluate("tip_z"))      # SI (m)

    df = test_launch(fid)
    rel_file = ROOT / "logs" / f"verify_release_{fid}.txt"
    write_release_file(df, rel_file, fid, z_shift_m=tip_z_m)
    print(rel_file.read_text())

    for ft in tags(cpt.feature()):
        f = cpt.feature(ft)
        if str(f.getType()) in RELEASE_TYPES and f.isActive():
            print(f"disable {ft} ({f.getType()})")
            f.active(False)
    rel = cpt.create(REL_TAG, "ReleaseFromDataFile")
    rel.set("Filename", str(rel_file))
    rel.set("icolp", jpype.JInt(0))                       # positions start at column 0
    rel.set("InitialVelocity", "FromFile")
    rel.set("icolv", jpype.JInt(2 if fid == "2d" else 3))  # velocities follow the positions
    rel.importData()

    # particle study = the one with a Transient step
    std = next(s for s in tags(j.study())
               if any(str(j.study(s).feature(f).getType()) == "Transient" for f in tags(j.study(s).feature())))
    step = next(f for f in tags(j.study(std).feature()) if str(j.study(std).feature(f).getType()) == "Transient")
    j.study(std).feature(step).set("tlist", T_TEST)
    sol = next(s for s in tags(j.sol()) if str(j.sol(s).study()) == std)
    print(f"running {std}/{step} (sol {sol}) ...", flush=True)
    t = time.time()
    j.study(std).run()
    print(f"ran in {time.time() - t:.0f} s", flush=True)

    if fid == "2d":
        got = particle_t0(j, sol, ["qr", "qz", "cpt.vr", "cpt.vz"])          # mm, m/s
        want = np.c_[np.hypot(df.x_m, df.y_m) / units.MM, (df.z_m + tip_z_m) / units.MM,
                     np.hypot(df.vx_mps, df.vy_mps), df.vz_mps].T
        names = ["r", "z", "vr", "vz"]
    else:
        got = particle_t0(j, sol, ["qx", "qy", "qz", "cpt.vx", "cpt.vy", "cpt.vz"])
        want = np.c_[df.x_m / units.MM, df.y_m / units.MM, (df.z_m + tip_z_m) / units.MM,
                     df.vx_mps, df.vy_mps, df.vz_mps].T
        names = ["x", "y", "z", "vx", "vy", "vz"]
    print(f"n particles: got {got.shape[1]}, file {want.shape[1]}")
    ok = got.shape == want.shape
    for n, g, w in zip(names, got, want):
        err = np.max(np.abs(g - w)) if ok else float("nan")
        print(f"  {n:3s} max |got - file| = {err:.3g}   got {np.array2string(g, precision=7)}")
        ok = ok and err <= 1e-6 * max(1.0, np.max(np.abs(w)))
    print("RESULT:", "PASS (columns, units, row order and z offset as written)" if ok else "FAIL")
    client.remove(model)   # never saved


if __name__ == "__main__":
    main()
