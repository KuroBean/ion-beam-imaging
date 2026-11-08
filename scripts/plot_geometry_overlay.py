"""Overlay the 2D axisymmetric geometry (its boundary mesh edges) on the 3D
model's cross-sections (logs/xsec_segments.npz from cross_section.py).

Usage:  .venv\\Scripts\\python.exe scripts\\plot_geometry_overlay.py
Output: logs/overlay_overview.png, logs/overlay_source.png, logs/overlay_mcp.png
"""
import numpy as np

from comsol_session import PROJECT_DIR, load, start

OUT = PROJECT_DIR / "logs"


def main():
    client = start()
    model = load(client, PROJECT_DIR / "lens8_axisym.mph")
    mesh = model.java.component("comp1").mesh("mesh1")
    V = np.array([np.array(r) for r in mesh.getVertex()])  # (2, N): r, z
    E = np.array([np.array(r) for r in mesh.getElem("edg")]).astype(int)  # (2, M)
    client.clear()
    segs2d = np.stack([V[:, E[0]].T, V[:, E[1]].T], axis=1)  # (M, 2, 2) as (r, z)
    np.save(OUT / "geom2d_edges.npy", segs2d)
    plot(segs2d)


def plot(segs2d):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection

    x3 = np.load(OUT / "xsec_segments.npz")
    views = {"overview": ((0, 180), (-55, 790), (16, 5)), "source": ((0, 40), (60, 140), (10, 5.5)),
             "mcp": ((0, 80), (490, 535), (9, 9))}
    for name, (rl, zl, fs) in views.items():
        fig, ax = plt.subplots(figsize=fs, facecolor="#fcfcfb")
        ax.set_facecolor("#fcfcfb")
        for a, ls in ((0, "-"), (45, ":"), (90, "--"), (135, "-.")):
            s = x3[f"segs_{a}"]
            s = s[(s[:, :, 0] >= -1e-9).all(1)]  # r >= 0 half only
            ax.add_collection(LineCollection(s[:, :, ::-1], colors="#eb6834", linewidths=0.8,
                                             linestyles=ls, alpha=0.9 if a == 0 else 0.5))
        ax.add_collection(LineCollection(segs2d[:, :, ::-1], colors="#2a78d6", linewidths=1.4))
        ax.plot([], [], color="#eb6834", lw=2, label="3D cross-sections (0/45/90/135°)")
        ax.plot([], [], color="#2a78d6", lw=2, label="2D axisymmetric model")
        ax.set_xlim(zl); ax.set_ylim(rl); ax.set_aspect("equal")
        ax.set_xlabel("z (mm)"); ax.set_ylabel("r (mm)")
        ax.grid(color="#e6e5e0", lw=0.5)
        for sp in ax.spines.values():
            sp.set_color("#c3c2b7")
        ax.legend(frameon=False, loc="upper left", fontsize=9)
        ax.set_title(f"2D model vs 3D geometry — {name}", loc="left", fontsize=11)
        fig.tight_layout()
        fig.savefig(OUT / f"overlay_{name}.png", dpi=140)
        plt.close(fig)
        print(f"wrote overlay_{name}.png", flush=True)


if __name__ == "__main__":
    main()
