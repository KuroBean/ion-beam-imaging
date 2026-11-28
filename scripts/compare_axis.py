"""Compare the electrostatic potential of the 2D axisymmetric model with the 3D
model along lines parallel to the beam axis (r = 0, 10, 30 mm).

3D values are taken from the stored solution in the 3D .mph (Study 1); lines
at r > 0 are evaluated at 4 azimuths (0, 45, 90, 135 deg) to show the spread
caused by non-axisymmetric parts.

Usage:  .venv\\Scripts\\python.exe scripts\\compare_axis.py [2d.mph] [3d.mph]
Output: logs/compare_axis.png, logs/compare_axis.npz
"""
import sys

import jpype
import numpy as np

from comsol_session import MODEL_FILE, PROJECT_DIR, load, start

OUT = PROJECT_DIR / "logs"
RADII = [0.0, 10.0, 30.0]
Z0, Z1, NPTS = -50.0, 781.8, 4000


def sarr2(rows):
    return jpype.JArray(jpype.JString, 2)([[str(v) for v in r] for r in rows])


def eval_points(model, dset, coords, expr="V"):
    """Evaluate expr at arbitrary points using a Cut Point dataset."""
    j = model.java
    tag = "cpt_cmp"
    if tag in [str(t) for t in j.result().dataset().tags()]:
        j.result().dataset().remove(tag)
    dim = coords.shape[0]
    cp = j.result().dataset().create(tag, "CutPoint3D" if dim == 3 else "CutPoint2D")
    cp.set("data", dset)
    for i, ax in enumerate(("pointx", "pointy", "pointz")[:dim]):
        cp.set(ax, " ".join(f"{v:.6g}" for v in coords[i]))
    ev = j.result().numerical().create("ev_cmp", "EvalPoint")
    ev.set("data", tag)
    ev.set("expr", jpype.JArray(jpype.JString)([expr]))
    vals = np.array(ev.getReal()).ravel()  # NaN outside the geometry / in excluded domains
    j.result().numerical().remove("ev_cmp")
    j.result().dataset().remove(tag)
    return vals


def main():
    path2d = sys.argv[1] if len(sys.argv) > 1 else str(PROJECT_DIR / "lens8_axisym.mph")
    path3d = sys.argv[2] if len(sys.argv) > 2 else str(MODEL_FILE)
    z = np.linspace(Z0, Z1, NPTS)
    client = start()
    res = {"z": z}

    m2 = load(client, path2d)
    for r in RADII:
        res[f"V2d_r{r:g}"] = eval_points(m2, "dset1", np.vstack([np.full_like(z, r), z]))
    client.remove(m2)

    m3 = load(client, path3d)
    for r in RADII:
        for a in ((0,) if r == 0 else (0, 45, 90, 135)):
            th = np.deg2rad(a)
            pts = np.vstack([np.full_like(z, r * np.cos(th)), np.full_like(z, r * np.sin(th)), z])
            res[f"V3d_r{r:g}_a{a}"] = eval_points(m3, "dset1", pts)
            print(f"3D r={r} a={a} done", flush=True)
    client.clear()
    np.savez_compressed(OUT / "compare_axis.npz", **res)
    plot(res)


def plot(res):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    z = res["z"]
    c2d, c3d = "#2a78d6", "#eb6834"
    fig, axes = plt.subplots(len(RADII), 2, figsize=(15, 3.6 * len(RADII)), facecolor="#fcfcfb",
                             gridspec_kw={"width_ratios": [2.2, 1]})
    for i, r in enumerate(RADII):
        v2 = res[f"V2d_r{r:g}"]
        keys = [k for k in res if k.startswith(f"V3d_r{r:g}_")]
        for col, (zl, title) in enumerate((((Z0, Z1), "full length"), ((55, 160), "source region"))):
            ax = axes[i, col]
            ax.set_facecolor("#fcfcfb")
            for n, k in enumerate(keys):
                ax.plot(z, res[k], color=c3d, lw=2 if n == 0 else 1, alpha=1 if n == 0 else 0.5,
                        label="3D model" if n == 0 else (None if n > 1 else "3D, other azimuths"))
            ax.plot(z, v2, color=c2d, lw=2, ls="--", label="2D axisymmetric")
            ax.set_xlim(zl)
            m = (z >= zl[0]) & (z <= zl[1])
            allv = np.concatenate([res[k][m] for k in keys] + [v2[m]])
            allv = allv[np.isfinite(allv)]
            if allv.size:
                pad = 0.05 * (allv.max() - allv.min() + 1)
                ax.set_ylim(allv.min() - pad, allv.max() + pad)
            ax.set_title(f"V along r = {r:g} mm — {title}", loc="left", fontsize=10, color="#0b0b0b")
            ax.set_xlabel("z (mm)")
            ax.set_ylabel("V (V)")
            ax.grid(color="#e6e5e0", lw=0.5)
            for s in ax.spines.values():
                s.set_color("#c3c2b7")
            if i == 0 and col == 0:
                ax.legend(frameon=False, fontsize=9)
        # summary
        both = np.isfinite(v2) & np.isfinite(res[keys[0]])
        d = np.abs(v2[both] - res[keys[0]][both])
        print(f"r={r:g} mm: max |V2D - V3D| = {d.max():.1f} V, median = {np.median(d):.2f} V "
              f"over {both.sum()} points", flush=True)
    fig.tight_layout()
    fig.savefig(OUT / "compare_axis.png", dpi=130)
    print("wrote compare_axis.png", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--replot":
        plot(dict(np.load(OUT / "compare_axis.npz")))
    else:
        main()
