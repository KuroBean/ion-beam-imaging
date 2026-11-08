"""Cut the meshed 3D geometry with half-planes through the z (beam) axis.

For each angle theta, the plane through the z axis containing the direction
(cos theta, sin theta, 0) is intersected with every surface-mesh triangle.
The resulting segments are expressed in (r, z), where r is the signed distance
along that direction.  Overlaying several angles shows which parts are
axisymmetric and gives the r-z profile needed for the 2D axisymmetric model.

Outputs (in logs/):
  xsec_segments.npz  - segments per angle with boundary ids and group labels
  xsec_overview.png, xsec_source.png, xsec_mcp.png  - plots

Usage:  .venv\\Scripts\\python.exe scripts\\cross_section.py
"""
import sys

import numpy as np

from comsol_session import PROJECT_DIR, load, start

OUT = PROJECT_DIR / "logs"
ANGLES_DEG = [0, 45, 90, 135]

# Boundary groups, taken from the physics feature selections (in priority order:
# a boundary in several features gets the first matching group).
GROUPS = [
    ("Needle (gnd)", ["es/gnd2"]),
    ("Lens 1 (-120 V)", ["es/pot3"]),
    ("Lens 2 (-40 V)", ["es/pot4"]),
    ("MCP front/back + holder", ["es/pot5", "es/pot6", "cpt/wall5"]),
    ("Screen mesh + cross (-1 kV)", ["es/pot7", "es/pot8", "cpt/wall6"]),
    ("Chamber 1 tube (gnd)", ["es/gnd4"]),
    ("Chamber 2 sphere (gnd)", ["es/gnd3"]),
]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6"]
OTHER_COLOR = "#a8a7a2"


def jarr(a):
    return np.array([np.array(row) for row in a])


def boundary_groups(j, nbnd):
    comp = j.component("comp1")
    grp = np.full(nbnd + 1, -1, dtype=int)  # index by 1-based boundary id
    for gi, (_, feats) in enumerate(GROUPS):
        for f in feats:
            ph, tag = f.split("/")
            ents = np.array(list(comp.physics(ph).feature(tag).selection().entities(2)), dtype=int)
            ents = ents[grp[ents] < 0]
            grp[ents] = gi
    return grp


def cut(V, T, theta):
    """Intersect triangles with plane through z axis at angle theta.

    Returns (segs[K,2,2] in (r,z), tri_index[K]).
    """
    d = np.array([np.cos(theta), np.sin(theta), 0.0])
    n = np.array([-np.sin(theta), np.cos(theta), 0.0])
    s = V.T @ n  # signed distance of each vertex from the plane
    st = s[T]  # (M,3)
    sign = np.sign(st)
    hit = ~((sign > 0).all(1) | (sign < 0).all(1))
    hit &= ~(sign == 0).all(1)
    idx = np.nonzero(hit)[0]
    segs = []
    keep = []
    for k in idx:
        pts = []
        for a, b in ((0, 1), (1, 2), (2, 0)):
            sa, sb = st[k, a], st[k, b]
            if sa == 0:
                pts.append(V[:, T[k, a]])
            if (sa < 0 < sb) or (sb < 0 < sa):
                t = sa / (sa - sb)
                pts.append(V[:, T[k, a]] + t * (V[:, T[k, b]] - V[:, T[k, a]]))
        if len(pts) >= 2:
            p, q = pts[0], pts[1]
            segs.append([[p @ d, p[2]], [q @ d, q[2]]])
            keep.append(k)
    return np.array(segs), np.array(keep, dtype=int)


def main():
    client = start()
    model = load(client)
    j = model.java
    comp = j.component("comp1")
    mesh = comp.mesh("mesh1")
    print("reading mesh ...", flush=True)
    V = jarr(mesh.getVertex())  # (3, N), model length unit (mm)
    T = jarr(mesh.getElem("tri")).T.astype(int)  # (M, 3), 0-based
    E = np.array(mesh.getElemEntity("tri"), dtype=int)  # (M,), 1-based boundary id
    nbnd = comp.geom("geom1").getNBoundaries()
    grp = boundary_groups(j, nbnd)
    print(f"vertices {V.shape[1]}, surface triangles {T.shape[0]}, boundaries {nbnd}", flush=True)
    print(f"x range {V[0].min():.1f}..{V[0].max():.1f}, y range {V[1].min():.1f}..{V[1].max():.1f}, "
          f"z range {V[2].min():.1f}..{V[2].max():.1f}", flush=True)
    client.clear()

    data = {}
    for a in ANGLES_DEG:
        segs, tri = cut(V, T, np.deg2rad(a))
        data[f"segs_{a}"] = segs
        data[f"bnd_{a}"] = E[tri]
        data[f"grp_{a}"] = grp[E[tri]]
        print(f"angle {a:3d}: {len(segs)} segments", flush=True)
    data["group_names"] = np.array([g[0] for g in GROUPS])
    np.savez_compressed(OUT / "xsec_segments.npz", **data)
    plot(data)


def plot(data, views=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.collections import LineCollection
    from matplotlib.lines import Line2D

    views = views or {
        "overview": None,
        "source": ((-45, 45), (40, 140)),
        "mcp": ((-110, 110), (440, 560)),
    }
    names = list(data["group_names"])
    styles = {0: "-", 45: ":", 90: "--", 135: "-."}
    for vname, lim in views.items():
        fig, ax = plt.subplots(figsize=(14, 7) if lim is None else (9, 9), facecolor="#fcfcfb")
        ax.set_facecolor("#fcfcfb")
        for a in ANGLES_DEG:
            segs, g = data[f"segs_{a}"], data[f"grp_{a}"]
            if len(segs) == 0:
                continue
            # plot as (z, r) so the beam axis runs left to right
            zr = segs[:, :, ::-1]
            cols = [COLORS[i] if i >= 0 else OTHER_COLOR for i in g]
            ax.add_collection(LineCollection(zr, colors=cols, linewidths=1.2 if a == 0 else 0.8,
                                             linestyles=styles[a], alpha=1.0 if a == 0 else 0.7))
        ax.axhline(0, color="#52514e", lw=0.6, ls=(0, (6, 4)))
        ax.set_aspect("equal")
        if lim:
            ax.set_xlim(lim[1]); ax.set_ylim(lim[0])
        else:
            ax.autoscale()
        ax.set_xlabel("z (mm)  - beam axis", color="#0b0b0b")
        ax.set_ylabel("r (mm), signed along cut direction", color="#0b0b0b")
        ax.grid(color="#e6e5e0", lw=0.5)
        for s in ax.spines.values():
            s.set_color("#c3c2b7")
        handles = [Line2D([], [], color=c, lw=2, label=n) for c, n in zip(COLORS, names)]
        handles.append(Line2D([], [], color=OTHER_COLOR, lw=2, label="Other (zero charge / unassigned)"))
        handles += [Line2D([], [], color="#52514e", lw=1, ls=styles[a], label=f"cut at {a}°") for a in ANGLES_DEG]
        ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1), fontsize=8, frameon=False)
        ax.set_title(f"3D model cross-sections through beam axis — {vname}", color="#0b0b0b", loc="left")
        fig.tight_layout()
        fig.savefig(OUT / f"xsec_{vname}.png", dpi=150)
        plt.close(fig)
        print(f"wrote xsec_{vname}.png", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--replot":
        d = dict(np.load(OUT / "xsec_segments.npz", allow_pickle=False))
        plot(d)
    else:
        main()
