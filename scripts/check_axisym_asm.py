"""Sanity checks for the 2D axisymmetric model with the real lens assembly.

  * geometry: 2D boundary edges overlaid on the STEP-part cross-sections (lens/accelerator/deflector)
  * on-axis potential V(z)
  * particle trajectories, where they stop, kinetic-energy conservation
  * cfg 1 / cfg 2: geometry still builds; deflectors removed; clearance to the MCP stack

Usage:  .venv\\Scripts\\python.exe scripts\\check_axisym_asm.py [2d.mph]
Output: logs/axisym_asm_*.png, printed summary
"""
import sys

import numpy as np

from comsol_session import PROJECT_DIR, load, start
from compare_particles import particle_data

OUT = PROJECT_DIR / "logs"
BLUE, ORANGE, INK2, GRID = "#2a78d6", "#eb6834", "#52514e", "#e6e5e0"


def edges(model):
    mesh = model.java.component("comp1").mesh("mesh1")
    V = np.array([np.array(r) for r in mesh.getVertex()])
    E = np.array([np.array(r) for r in mesh.getElem("edg")]).astype(int)
    return np.stack([V[:, E[0]].T, V[:, E[1]].T], axis=1)  # (M, 2, 2) as (r, z)


def interp_V(j, r, z):
    """Electric potential of Study 1 at points (r, z) in mm."""
    import jpype
    inter = j.result().numerical().create("int_v", "Interp")
    inter.set("data", "dset1")
    inter.set("expr", "V")
    inter.setInterpolationCoordinates(jpype.JArray(jpype.JDouble, 2)([[float(x) for x in r], [float(x) for x in z]]))
    out = np.array([np.array(row) for row in inter.getReal()]).ravel()
    j.result().numerical().remove("int_v")
    return out


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection

    path = sys.argv[1] if len(sys.argv) > 1 else str(PROJECT_DIR / "lens8_axisym_asm.mph")
    client = start()
    model = load(client, path)
    j = model.java
    par = j.param()
    z_asm = par.evaluate("z_asm") * 1e3
    tip = par.evaluate("tip_z") * 1e3
    mcp = par.evaluate("mcp_z") * 1e3
    segs = edges(model)

    # on-axis potential
    zz = np.linspace(tip + 0.01, mcp - 0.01, 3000)
    Vax = interp_V(j, [0.0] * len(zz), zz)

    # particles (qr, qz in the model length unit, mm)
    a = particle_data(model, ["qr", "qz", "cpt.Ep"])
    r, z, ke = a[0], a[1], a[2]
    e_unit = 1.602176634e-19
    ke_ev = ke / e_unit
    n = r.shape[0]
    last = np.array([np.max(np.nonzero(np.isfinite(z[i]))[0]) for i in range(n)])
    zf = z[np.arange(n), last]
    rf = r[np.arange(n), last]
    kef = ke_ev[np.arange(n), last]
    # energy conservation: KE + qV along the path (V at final point from the field)
    Vf = interp_V(j, rf, zf)
    Z = par.evaluate("Z_ion")
    e0 = ke_ev[:, 0]
    err = kef + Z * Vf - e0          # tip is grounded: V0 = 0 at the release point
    print(f"  KE finite: start {np.isfinite(e0).sum()}, end {np.isfinite(kef).sum()}; E0 range {np.nanmin(e0):.3f}..{np.nanmax(e0):.3f} eV")
    on_mcp = np.abs(zf - mcp) < 0.05
    print(f"particles: {n}; stopped on MCP front (z={mcp:.2f}): {on_mcp.sum()}  elsewhere: {(~on_mcp).sum()}")
    if on_mcp.any():
        print(f"  MCP spot: rms r = {np.sqrt(np.mean(rf[on_mcp]**2)):.3f} mm, max r = {rf[on_mcp].max():.3f} mm")
    stuck = zf[~on_mcp]
    if len(stuck):
        hz, he = np.histogram(stuck, bins=[0, tip + 1, z_asm - 140, z_asm - 40, z_asm + 2, mcp - 1, 1e4])
        print("  stopped elsewhere by z bin:", dict(zip([f"{he[k]:.0f}-{he[k+1]:.0f}" for k in range(len(hz))], hz)))
    print(f"  energy error KE+qV-E0: median {np.nanmedian(err):+.3f} eV, 95th pct |.| {np.nanpercentile(np.abs(err), 95):.3f} eV, max {np.nanmax(np.abs(err)):.3f} eV")
    print(f"  arrival time (last output with finite z): max {last.max()} steps")

    # cfg 1 / 2 geometry
    geom = j.component("comp1").geom("geom1")
    for cfg in ("1", "2", "3"):
        par.set("cfg", cfg)
        geom.run()
        m = par.evaluate("mcp_z") * 1e3
        nd = len(list(j.component("comp1").selection("geom1_D1_dom").entities(2))) if \
            "geom1_D1_dom" in [str(t) for t in j.component("comp1").selection().tags()] else 0
        l9_back = z_asm + (-42.325 + 15)
        print(f"cfg {cfg}: {geom.getNDomains()} domains, deflector D1 domains={nd}; mcp_z={m:.1f} mm, "
              f"screen hub front at {m - 15.6:.1f} mm, L9 lip end at {l9_back:.1f} mm, "
              f"D2 end at {z_asm + 0.77:.1f} mm")
    client.clear()

    # ---- plots ----
    s = np.load(r"D:\Users\kshimojo\AppData\Local\Temp\1\claude\fc14a95549bfbe0b\bbec2d34-4707-40c8-bb4b-c34bfb07aebd"
                r"\scratchpad\xsec_raw.npy", allow_pickle=True).item() if len(sys.argv) < 3 else None
    fig, ax = plt.subplots(figsize=(15, 4.8), facecolor="#fcfcfb")
    if s:
        for k, v in s.items():
            if k.startswith("wpB_") and ".wpA." not in k and any(p in k for p in ("lens", "accel", "deflector")):
                for seg in v:
                    seg = np.asarray(seg, float)
                    ax.plot(seg[:, 1] + z_asm, np.abs(seg[:, 0]), color=ORANGE, lw=0.7, alpha=0.8)
            if k.startswith("wpA_") and ".wpA." not in k and "deflector" in k:
                for seg in v:
                    seg = np.asarray(seg, float)
                    ax.plot(seg[:, 0] + z_asm, np.abs(seg[:, 1] + 0.5305), color=ORANGE, lw=0.7, ls=":", alpha=0.8)
    ax.add_collection(LineCollection(segs[:, :, ::-1], colors=BLUE, linewidths=1.2))
    ax.plot([], [], color=ORANGE, lw=2, label="STEP part cross-sections (y-z cut; deflectors also x-z, dotted)")
    ax.plot([], [], color=BLUE, lw=2, label="2D axisymmetric model")
    ax.set(xlim=(tip - 5, z_asm + 5), ylim=(0, 36), xlabel="z (mm)", ylabel="r (mm)")
    ax.set_aspect("equal")
    ax.grid(color=GRID, lw=0.5)
    ax.legend(frameon=False, loc="upper left", fontsize=8, bbox_to_anchor=(0, -0.22), ncol=2)
    ax.set_title("2D lens assembly vs STEP geometry", loc="left", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "axisym_asm_geometry.png", dpi=140)
    plt.close(fig)

    fig, axs = plt.subplots(2, 1, figsize=(13, 8), facecolor="#fcfcfb", sharex=True)
    axs[0].plot(zz, Vax, color=BLUE, lw=1.5)
    axs[0].set(ylabel="V on axis (V)", title="On-axis potential")
    for i in range(0, n, max(1, n // 300)):
        ok = np.isfinite(z[i])
        axs[1].plot(z[i][ok], r[i][ok], color=BLUE, lw=0.4, alpha=0.5)
    axs[1].add_collection(LineCollection(segs[:, :, ::-1], colors=INK2, linewidths=0.6))
    axs[1].set(xlabel="z (mm)", ylabel="r (mm)", ylim=(0, 40), title="Trajectories (every few particles)")
    for a_ in axs:
        a_.grid(color=GRID, lw=0.5)
        a_.title.set_ha("left"); a_.title.set_x(0)
    fig.tight_layout()
    fig.savefig(OUT / "axisym_asm_axis_traj.png", dpi=140)
    print("wrote logs/axisym_asm_geometry.png, logs/axisym_asm_axis_traj.png")


if __name__ == "__main__":
    main()


