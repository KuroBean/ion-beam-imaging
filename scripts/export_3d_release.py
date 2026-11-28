"""Export the 3D model's particle initial conditions (t = 0 of Study 2) as an
equivalent 2D-axisymmetric release file.

The 3D beam starts within ~50 nm of the axis, so each 3D particle is an
(almost exactly) meridional ray.  Its 2D equivalent starts on the axis with
  v_r = sqrt(vx^2 + vy^2),  v_z = vz,  v_phi = 0.

Writes data/release_from_3d.txt with columns:  r[mm]  z[mm]  vr  vz [m/s]
(COMSOL reads 2D-axisymmetric velocity columns in the order vr, vz)
(also keeps the raw 3D values in data/release_3d_raw.txt)

Usage:  .venv\\Scripts\\python.exe scripts\\export_3d_release.py [3d.mph]
"""
import sys

import numpy as np

from comsol_session import MODEL_FILE, PROJECT_DIR, load, start
from compare_particles import particle_data

DATA = PROJECT_DIR / "data"
R0 = 1e-6  # mm, start just off the axis


def main():
    DATA.mkdir(exist_ok=True)
    client = start()
    m = load(client, sys.argv[1] if len(sys.argv) > 1 else MODEL_FILE)
    a = particle_data(m, ["qx", "qy", "qz", "cpt.vx", "cpt.vy", "cpt.vz"])[:, :, 0]  # t = 0
    client.clear()
    x, y, z, vx, vy, vz = a
    ok = np.all(np.isfinite(a), axis=0)
    print(f"{ok.sum()} of {a.shape[1]} particles have finite initial values")
    np.savetxt(DATA / "release_3d_raw.txt", a[:, ok].T, fmt="%.9g", comments="% ",
               header="3D initial conditions (t=0): x[mm] y[mm] z[mm] vx vy vz [m/s]")
    vr = np.hypot(vx, vy)
    out = np.c_[np.full(ok.sum(), R0), z[ok] + 1e-6, vr[ok], vz[ok]]
    np.savetxt(DATA / "release_from_3d.txt", out, fmt="%.9g", comments="% ",
               header="2D-axisymmetric equivalent of the 3D beam: r[mm] z[mm] vr vz [m/s]")
    r0 = np.hypot(x, y)[ok] * 1e6
    print(f"3D start radius: max {r0.max():.1f} nm; |v|: {np.sqrt(vx**2+vy**2+vz**2)[ok].mean():.1f} m/s; "
          f"half-angle (deg): mean {np.degrees(np.arctan2(vr[ok], vz[ok])).mean():.2f}, "
          f"max {np.degrees(np.arctan2(vr[ok], vz[ok])).max():.2f}")


if __name__ == "__main__":
    main()

