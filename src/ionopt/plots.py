"""Standard diagnostic plots from exported data (plan 9.7).

Saved to results/<job_id>/plots/. Figure sizes and axis limits are fixed per chamber
setup (from constraints.yaml, falling back to the run's geometry) so plots from
different runs are directly comparable - the Phase 2 critic agent relies on that.
"""
from __future__ import annotations

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, Normalize, SymLogNorm  # noqa: E402
from matplotlib.patches import Circle, Rectangle  # noqa: E402

from . import units  # noqa: E402
from .config import Config, range_known  # noqa: E402
from .schemas import FATES, FILES  # noqa: E402
from .utils import read_json  # noqa: E402

# reference palette (dataviz skill, light mode)
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
BLUE = "#2a78d6"
BLUE_LIGHT = "#b7d3f6"
RED = "#e34948"
SEQ = LinearSegmentedColormap.from_list("seq_blue", ["#9ec5f4", "#5598e7", "#2a78d6", "#1c5cab", "#0d366b"])
DIV = LinearSegmentedColormap.from_list("div_blue_red", ["#104281", "#3987e5", "#f0efec", "#e34948", "#9b2423"])
FIGSIZE = (7.0, 4.2)
DPI = 130

plt.rcParams.update({
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "axes.edgecolor": AXIS, "axes.labelcolor": INK2, "axes.titlecolor": INK, "axes.titlesize": 11,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "axes.labelsize": 9,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "xtick.color": MUTED, "ytick.color": MUTED,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "text.color": INK, "legend.frameon": False,
    "legend.fontsize": 8, "lines.linewidth": 1.5, "font.family": "sans-serif", "axes.axisbelow": True,
})


# --------------------------------------------------------------------------- limits


def z_limits_mm(cfg: Config, chamber: int, geom: dict) -> tuple[float, float]:
    """Fixed z range for a chamber setup: tip to the farthest allowed MCP position."""
    rng = cfg.chamber(chamber).z_mcp_mm
    z_hi = rng[1] if range_known(rng) else geom["z_mcp_m"] / units.MM
    return -0.02 * z_hi, 1.04 * z_hi


def _r_active_mm(cfg: Config) -> float:
    return cfg.spec.detector.mcp_active_diameter_mm / 2


def _electrode_rects(ax, geom: dict, scale=1 / units.MM, mirror=False):
    for e in geom.get("electrodes", []):
        if None in (e.get("thickness_m"), e.get("r_in_m"), e.get("r_out_m")):
            ax.axvline(e["z_m"] * scale, color=INK2, lw=0.8, ls=":")
            continue
        z0 = (e["z_m"] - e["thickness_m"] / 2) * scale
        for sgn in ((1, -1) if mirror else (1,)):
            y0 = sgn * e["r_in_m"] * scale if sgn > 0 else -e["r_out_m"] * scale
            ax.add_patch(Rectangle((z0, y0), e["thickness_m"] * scale, (e["r_out_m"] - e["r_in_m"]) * scale,
                                   fill=False, ec=INK, lw=0.9))


def _save(fig, path: Path) -> Path:
    fig.tight_layout()
    fig.savefig(path, dpi=DPI)
    plt.close(fig)
    return path


def _subtitle(ax, text: str):
    """One-line note under the title (the title is moved up to make room)."""
    ax.set_title(ax.get_title(loc="left"), loc="left", pad=16)
    ax.text(0, 1.012, text, transform=ax.transAxes, fontsize=8, color=INK2, va="bottom")


# --------------------------------------------------------------------------- individual plots


def plot_trajectories(d: Path, out: Path, cfg: Config, job, geom: dict, ions: pd.DataFrame) -> Path | None:
    f = d / FILES["traj"]
    if not f.is_file():
        return None
    tr = pd.read_csv(f).merge(ions[["ion_id", "theta_deg"]], on="ion_id")
    fig, ax = plt.subplots(figsize=FIGSIZE)
    norm = Normalize(0, cfg.spec.launch.theta_max_deg)
    for _, g in tr.groupby("ion_id"):
        r = np.hypot(g["x_m"], g["y_m"]) / units.MM
        ax.plot(g["z_m"] / units.MM, r, color=SEQ(norm(g["theta_deg"].iloc[0])), lw=0.6, alpha=0.8)
    _electrode_rects(ax, geom)
    ax.set_xlim(*z_limits_mm(cfg, job.cfg, geom))
    ax.set_ylim(0, 1.5 * _r_active_mm(cfg))
    ax.set(xlabel="z from tip (mm)", ylabel="r (mm)", title="Trajectories (side view)")
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=SEQ), ax=ax, label="launch angle θ (deg)", pad=0.01)
    return _save(fig, out / "trajectories.png")


def plot_field_map(d: Path, out: Path, cfg: Config, job, geom: dict) -> Path | None:
    f = d / FILES["cutplane_field"]
    if not f.is_file():
        return None
    cp = pd.read_csv(f)
    zs, rs = np.unique(cp["z_m"]), np.unique(cp["r_m"])
    grid = cp.pivot_table(index="r_m", columns="z_m", values="V_V").reindex(index=rs, columns=zs).to_numpy()
    vmax = max(abs(np.nanmin(grid)), abs(np.nanmax(grid)), 1e-9)
    fig, ax = plt.subplots(figsize=FIGSIZE)
    m = ax.pcolormesh(zs / units.MM, rs / units.MM, grid, cmap=DIV, norm=SymLogNorm(linthresh=10.0, vmin=-vmax, vmax=vmax),
                      shading="auto", rasterized=True)
    ax.contour(zs / units.MM, rs / units.MM, grid, levels=15, colors=INK2, linewidths=0.3, alpha=0.6)
    _electrode_rects(ax, geom)
    ax.axvline(geom["z_mcp_m"] / units.MM, color=INK, lw=1.2)
    ax.axvline(geom["z_mesh_m"] / units.MM, color=INK, lw=0.8, ls="--")
    ax.set_xlim(*z_limits_mm(cfg, job.cfg, geom))
    ax.set(xlabel="z from tip (mm)", ylabel="r (mm)", title="Potential map (r–z plane)")
    ax.grid(False)
    _subtitle(ax, "solid: MCP face  ·  dashed: mesh  ·  boxes: electrodes  ·  color: symmetric log scale (linear within ±10 V)")
    fig.colorbar(m, ax=ax, label="V (V)", pad=0.01)
    return _save(fig, out / "field_map.png")


def plot_r_theta(out: Path, cfg: Config, metrics: dict) -> Path:
    mp = metrics["mapping"]
    th = np.array(mp["theta_deg"])
    r = np.array([np.nan if v is None else v for v in mp["r_mm"]])
    se = np.array([np.nan if v is None else v for v in mp["sigma_E_mm"]])
    st = np.sqrt(np.nan_to_num(se) ** 2 + mp["sigma_mcp_mm"] ** 2)
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.fill_between(th, r - st, r + st, color=BLUE_LIGHT, lw=0, label="± σ_tot")
    ax.plot(th, r, color=BLUE, marker="o", ms=3, label="mean r(θ)")
    if mp.get("eval_theta_max_deg") is not None:
        ax.axvspan(mp["eval_theta_max_deg"], cfg.spec.launch.theta_max_deg, color=GRID, alpha=0.5, lw=0)
        ax.text(mp["eval_theta_max_deg"], 0.5, "  outside evaluation range", transform=ax.get_xaxis_transform(),
                fontsize=8, color=INK2, va="center")
    ax.axhline(_r_active_mm(cfg), color=INK2, lw=0.8, ls="--")
    ax.text(cfg.spec.launch.theta_max_deg, _r_active_mm(cfg), "active area edge ", fontsize=8, color=INK2,
            va="bottom", ha="right")
    ax.set_xlim(0, cfg.spec.launch.theta_max_deg)
    ax.set_ylim(0, 1.1 * _r_active_mm(cfg))
    ax.set(xlabel="launch angle θ (deg)", ylabel="landing radius r (mm)", title="Mapping r(θ)")
    ax.legend(loc="upper left", bbox_to_anchor=(0, 0.88))
    _subtitle(ax, f"monotonic: {mp['monotonic']}   σ_MCP = {mp['sigma_mcp_mm'] * 1e3:.0f} µm")
    return _save(fig, out / "r_theta.png")


def plot_dtheta(out: Path, cfg: Config, metrics: dict) -> Path:
    mp = metrics["mapping"]
    th = np.array(mp["theta_deg"])
    dt = np.array([np.nan if v is None else v for v in mp["dtheta_deg"]])
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(th, dt, color=BLUE, marker="o", ms=3)
    if metrics.get("score") is not None:
        ax.axhline(metrics["score"], color=INK2, lw=0.8, ls="--")
        ax.text(cfg.spec.launch.theta_max_deg, metrics["score"], f"score {metrics['score']:.3g}°",
                fontsize=8, color=INK2, va="bottom", ha="right")
    ax.set_yscale("log")
    ax.set_xlim(0, cfg.spec.launch.theta_max_deg)
    ax.set_ylim(1e-2, cfg.optimizer.nonevaluable_score_deg)
    ax.set(xlabel="launch angle θ (deg)", ylabel="angular resolution Δθ (deg)", title="Resolution Δθ(θ)")
    _subtitle(ax, "lower is better; score = max over the evaluation range")
    return _save(fig, out / "dtheta.png")


def plot_fates(out: Path, metrics: dict) -> Path:
    fr = [metrics["fates"].get(f, 0.0) for f in FATES]
    fig, ax = plt.subplots(figsize=FIGSIZE)
    y = np.arange(len(FATES))[::-1]
    ax.barh(y, fr, height=0.6, color=BLUE)
    for yi, v in zip(y, fr):
        ax.text(v + 0.01, yi, f"{v:.1%}", va="center", fontsize=8, color=INK2)
    ax.set_yticks(y, [f.replace("_", " ") for f in FATES], color=INK2)
    ax.set_xlim(0, 1.12)
    ax.grid(axis="y", visible=False)
    ax.set(xlabel="fraction of launched ion weight", title="Ion fates")
    return _save(fig, out / "fates.png")


def plot_landing(out: Path, cfg: Config, dv: pd.DataFrame, fidelity: str) -> Path:
    ra = _r_active_mm(cfg)
    on = dv[dv["fate"].isin(["mcp_active", "mcp_outside"])]
    fig, ax = plt.subplots(figsize=(5.2, 4.6) if fidelity == "3d" else FIGSIZE)
    if fidelity == "3d":
        norm = Normalize(0, cfg.spec.launch.theta_max_deg)
        ax.add_patch(Circle((0, 0), ra, fill=False, ec=INK2, lw=1, ls="--"))
        s = ax.scatter(on["x_land_mm"], on["y_land_mm"], c=on["theta_deg"], cmap=SEQ, norm=norm, s=10,
                       edgecolors=SURFACE, linewidths=0.4)
        ax.set_aspect("equal")
        ax.set_xlim(-1.1 * ra, 1.1 * ra)
        ax.set_ylim(-1.1 * ra, 1.1 * ra)
        ax.set(xlabel="x (mm)", ylabel="y (mm)", title="MCP hit map")
        fig.colorbar(s, ax=ax, label="launch angle θ (deg)", pad=0.01, shrink=0.85)
        _subtitle(ax, f"dashed: {2 * ra:.0f} mm active area")
    else:
        bins = np.linspace(0, 1.1 * ra, 45)
        ax.hist(on["r_land_mm"], bins=bins, weights=on["weight"], color=BLUE, rwidth=0.9)
        ax.axvline(ra, color=INK2, lw=0.8, ls="--")
        ax.text(ra, 0.97, f" {2 * ra:.0f} mm active area edge", transform=ax.get_xaxis_transform(), fontsize=8,
                color=INK2, va="top")
        ax.set_xlim(0, 1.1 * ra)
        ax.set(xlabel="landing radius r (mm)", ylabel="ion weight per bin", title="Landing radius")
    return _save(fig, out / "landing.png")


def plot_axis_potential(d: Path, out: Path, cfg: Config, job, geom: dict) -> Path | None:
    f = d / FILES["axis_potential"]
    if not f.is_file():
        return None
    ap = pd.read_csv(f)
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.plot(ap["z_m"] / units.MM, ap["V_V"], color=BLUE)
    ax.axhline(0, color=AXIS, lw=0.8)
    for e in geom.get("electrodes", []):
        ax.axvline(e["z_m"] / units.MM, color=MUTED, lw=0.6, ls=":")
    ax.axvline(geom["z_mesh_m"] / units.MM, color=INK2, lw=0.8, ls="--")
    ax.axvline(geom["z_mcp_m"] / units.MM, color=INK, lw=1.0)
    ax.set_xlim(*z_limits_mm(cfg, job.cfg, geom))
    ax.set(xlabel="z from tip (mm)", ylabel="V on axis (V)", title="Axis potential")
    _subtitle(ax, "dotted: electrodes  ·  dashed: mesh  ·  solid: MCP face. Ions slow down where V nears the tip potential")
    return _save(fig, out / "axis_potential.png")


# --------------------------------------------------------------------------- driver


def make_plots(result_dir: Path | str, cfg: Config) -> list[Path]:
    """All standard plots for a checked result folder (needs metrics.json and ions_derived.csv)."""
    from .results import load_job

    d = Path(result_dir)
    out = d / "plots"
    out.mkdir(exist_ok=True)
    job = load_job(d)
    made: list[Path | None] = []
    geom = read_json(d / FILES["geometry"]) if (d / FILES["geometry"]).is_file() else None
    metrics = read_json(d / FILES["metrics"]) if (d / FILES["metrics"]).is_file() else None
    if geom:
        ions = pd.read_csv(d / FILES["ions_launch"]) if (d / FILES["ions_launch"]).is_file() else None
        if ions is not None:
            made.append(plot_trajectories(d, out, cfg, job, geom, ions))
        made.append(plot_field_map(d, out, cfg, job, geom))
        made.append(plot_axis_potential(d, out, cfg, job, geom))
    if metrics and metrics.get("mapping"):
        made += [plot_r_theta(out, cfg, metrics), plot_dtheta(out, cfg, metrics), plot_fates(out, metrics)]
    if (d / FILES["ions_derived"]).is_file():
        made.append(plot_landing(out, cfg, pd.read_csv(d / FILES["ions_derived"]), job.fidelity))
    return [p for p in made if p is not None]
