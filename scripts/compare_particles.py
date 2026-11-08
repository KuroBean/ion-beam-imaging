"""Compare particle tracing results of the 2D axisymmetric and 3D models.

For each model: final particle positions (last output time) from Study 2,
radial position r of every particle, and where it stopped (MCP front face or
elsewhere).  Also extracts r(z) envelopes along the trajectories.

Usage:  .venv\\Scripts\\python.exe scripts\\compare_particles.py [2d.mph] [3d.mph]
Output: logs/compare_particles.png / .npz
"""
import sys

import jpype
import numpy as np

from comsol_session import MODEL_FILE, PROJECT_DIR, load, start

OUT = PROJECT_DIR / "logs"


def particle_data(model, exprs, sol="sol2"):
    """Return array [len(exprs), n_particles, n_times] for all output times."""
    j = model.java
    ds = j.result().dataset()
    tag = "part_cmp"
    if tag in [str(t) for t in ds.tags()]:
        ds.remove(tag)
    p = ds.create(tag, "Particle")
    p.set("solution", sol)
    ev = j.result().numerical().create("pev_cmp", "Particle")
    ev.set("data", tag)
    ev.set("innerinput", "all")
    ev.set("evaluate", "all")
    arrs = []
    for e in exprs:
        ev.set("expr", e)
        arrs.append(np.array([np.array(row) for row in ev.getReal()]))  # [particle, time]
    arr = np.array(arrs)
    j.result().numerical().remove("pev_cmp")
    ds.remove(tag)
    return arr


def main():
    path2d = sys.argv[1] if len(sys.argv) > 1 else str(PROJECT_DIR / "lens8_axisym.mph")
    path3d = sys.argv[2] if len(sys.argv) > 2 else str(MODEL_FILE)
    client = start()
    res = {}

    m2 = load(client, path2d)
    a2 = particle_data(m2, ["qr", "qz"])
    print("2D particle array shape", a2.shape, flush=True)
    res["r2"], res["z2"] = a2
    client.remove(m2)

    m3 = load(client, path3d)
    a3 = particle_data(m3, ["qx", "qy", "qz"])
    print("3D particle array shape", a3.shape, flush=True)
    res["x3"], res["y3"], res["z3"] = a3
    client.clear()
    np.savez_compressed(OUT / "compare_particles.npz", **res)
    summarize(res)


def summarize(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    r2, z2 = res["r2"], res["z2"]
    r3 = np.hypot(res["x3"], res["y3"])
    z3 = res["z3"]
    # arrays are [particle, time]?  normalise so time is the last axis
    for name, r, z in (("2D", r2, z2), ("3D", r3, z3)):
        zf, rf = z[:, -1], r[:, -1]
        ok = np.isfinite(zf)
        print(f"{name}: {r.shape[0]} particles, {r.shape[1]} times; final z: "
              f"min {np.nanmin(zf):.2f} max {np.nanmax(zf):.2f} mm; "
              f"final r: mean {np.nanmean(rf[ok]):.4f}, rms {np.sqrt(np.nanmean(rf[ok]**2)):.4f}, "
              f"max {np.nanmax(rf[ok]):.4f} mm", flush=True)
        hit = ok & (np.abs(zf - 515.9) < 0.05)
        print(f"   particles ending on MCP front (z=515.9): {hit.sum()}", flush=True)
        if hit.sum():
            rh = rf[hit]
            print(f"   MCP spot: r mean {rh.mean():.3f}, rms {np.sqrt(np.mean(rh**2)):.3f}, "
                  f"r50 {np.percentile(rh, 50):.3f}, r90 {np.percentile(rh, 90):.3f}, max {rh.max():.3f} mm", flush=True)

    c2d, c3d = "#2a78d6", "#eb6834"
    fig, axes = plt.subplots(1, 3, figsize=(17, 5), facecolor="#fcfcfb",
                             gridspec_kw={"width_ratios": [2.2, 1, 1]})
    ax = axes[0]
    for i in range(min(r3.shape[0], 200)):
        ax.plot(z3[i], r3[i], color=c3d, lw=0.4, alpha=0.4)
    for i in range(min(r2.shape[0], 200)):
        ax.plot(z2[i], r2[i], color=c2d, lw=0.4, alpha=0.4)
    ax.plot([], [], color=c3d, lw=2, label="3D model")
    ax.plot([], [], color=c2d, lw=2, label="2D axisymmetric")
    ax.set_xlabel("z (mm)"); ax.set_ylabel("r (mm)")
    ax.set_title("Trajectories (first 200 particles)", loc="left", fontsize=10)
    ax.legend(frameon=False)
    ax = axes[1]
    for i in range(min(r3.shape[0], 200)):
        ax.plot(z3[i], r3[i], color=c3d, lw=0.4, alpha=0.4)
    for i in range(min(r2.shape[0], 200)):
        ax.plot(z2[i], r2[i], color=c2d, lw=0.4, alpha=0.4)
    ax.set_xlim(100, 140)
    ax.set_title("Source / lens region", loc="left", fontsize=10)
    ax.set_xlabel("z (mm)")
    ax = axes[2]
    bins = np.linspace(0, max(np.nanmax(r2[:, -1]), np.nanmax(r3[:, -1])) * 1.05, 40)
    ax.hist(r3[:, -1][np.isfinite(r3[:, -1])], bins=bins, color=c3d, alpha=0.6, label="3D")
    ax.hist(r2[:, -1][np.isfinite(r2[:, -1])], bins=bins, histtype="step", color=c2d, lw=2, label="2D")
    ax.set_xlabel("final r (mm)"); ax.set_ylabel("particles")
    ax.set_title("Radial distribution at end", loc="left", fontsize=10)
    ax.legend(frameon=False)
    for a in axes:
        a.set_facecolor("#fcfcfb")
        a.grid(color="#e6e5e0", lw=0.5)
        for s in a.spines.values():
            s.set_color("#c3c2b7")
    fig.tight_layout()
    fig.savefig(OUT / "compare_particles.png", dpi=130)
    print("wrote compare_particles.png", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--replot":
        summarize(dict(np.load(OUT / "compare_particles.npz")))
    else:
        main()
