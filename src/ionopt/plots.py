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
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, Normalize, SymLogNorm  # noqa: E402
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


# --------------------------------------------------------------------------- one-page summary

LOST_FATES = ("electrode", "mesh_frame", "wall", "mcp_outside", "in_flight")
ELECTRODE_FILL = "#e8e7e1"


def _grid(f: Path):
    cp = pd.read_csv(f)
    zs, rs = np.unique(cp["z_m"]), np.unique(cp["r_m"])
    g = cp.pivot_table(index="r_m", columns="z_m", values="V_V").reindex(index=rs, columns=zs).to_numpy()
    return zs / units.MM, rs / units.MM, g


def _potential_bg(ax, zs, rs, g, vmax, contours: int = 0):
    m = ax.pcolormesh(zs, rs, g, cmap=DIV, norm=SymLogNorm(linthresh=10.0, vmin=-vmax, vmax=vmax),
                      shading="auto", rasterized=True, alpha=0.55)
    if contours:
        lv = np.linspace(np.nanmin(g), np.nanmax(g), contours)
        ax.contour(zs, rs, g, levels=lv, colors=INK2, linewidths=0.35, alpha=0.7)
    # conductors (and anything outside the vacuum) are blank in the exported grid: draw them as metal
    solid = np.isnan(g)
    if solid.any():
        ax.pcolormesh(zs, rs, np.where(solid, 1.0, np.nan), cmap=ListedColormap([ELECTRODE_FILL]), shading="auto",
                      rasterized=True, zorder=3)
        ax.contour(zs, rs, solid.astype(float), levels=[0.5], colors=INK2, linewidths=0.6, zorder=3)
    ax.grid(False)
    return m


def _electrode_labels(ax, geom: dict, pots: dict):
    """Electrode name and potential above each stack part (axes-fraction height, alternating rows)."""
    for i, e in enumerate(geom.get("electrodes", [])):
        v = pots.get(e["name"])
        ax.text(e["z_m"] / units.MM, 1.01 + 0.045 * (i % 2), e["name"].upper() + ("" if v is None else f" {v:+.0f}"),
                ha="center", va="bottom", fontsize=7, color=INK2, transform=ax.get_xaxis_transform(), clip_on=False)


def _electrodes_filled(ax, geom: dict):
    """Stack parts as rectangles (bounding boxes from constraints; used only without an exported grid)."""
    for e in geom.get("electrodes", []):
        if None in (e.get("thickness_m"), e.get("r_in_m"), e.get("r_out_m")):
            continue
        z0 = (e["z_m"] - e["thickness_m"] / 2) / units.MM
        ax.add_patch(Rectangle((z0, e["r_in_m"] / units.MM), e["thickness_m"] / units.MM,
                               (e["r_out_m"] - e["r_in_m"]) / units.MM, fc=ELECTRODE_FILL, ec=INK2, lw=0.7, zorder=3))


def _trajectories(ax, tr: pd.DataFrame, dv: pd.DataFrame, cfg: Config, z_max: float | None = None):
    fate = dv.set_index("ion_id")["fate"]
    norm = Normalize(0, cfg.spec.launch.theta_max_deg)
    for iid, g in tr.groupby("ion_id"):
        if z_max is not None:
            g = g[g["z_m"] <= z_max * units.MM * 1.02]
        r = np.hypot(g["x_m"], g["y_m"]) / units.MM
        lost = fate.get(iid) in LOST_FATES
        ax.plot(g["z_m"] / units.MM, r, color=RED if lost else SEQ(norm(g["theta_deg"].iloc[0])),
                lw=0.6 if lost else 0.9, alpha=0.75 if lost else 0.95, zorder=5)
    return norm


def _n(v, fmt: str) -> str:
    return "–" if v is None or (isinstance(v, float) and not math.isfinite(v)) else format(v, fmt)


def _stats_text(job, cfg: Config, metrics: dict, meta: dict, pots: dict) -> str:
    f = metrics.get("fates", {})
    req = metrics.get("requirements", {})
    mp = metrics.get("mapping", {})
    sp = metrics.get("spot", {})
    pre = meta.get("preacceleration") or {}
    lost = {k: f.get(k, 0) for k in LOST_FATES if f.get(k, 0) > 0}
    L = cfg.spec.launch
    lines = [
        f"job {job.job_id[:12]}   {job.fidelity.upper()}   cfg {job.cfg}",
        "   ".join(f"{k}={v}" for k, v in (job.tags or {}).items() if k in ("study_id", "trial", "purpose", "setting")),
        "",
        "TRANSMISSION",
        f"  reach active MCP     {f.get('mcp_active', 0):6.1%}",
        f"  collected (x mesh)   {_n(req.get('eta'), '6.1%')}",
        "  lost: " + (", ".join(f"{k.replace('_', ' ')} {v:.1%}" for k, v in lost.items()) or "none"),
        "",
        "IMAGE",
        f"  score (worst dθ)     {metrics.get('score') if metrics.get('score') is None else f'{metrics['score']:.3g}°'}",
        f"  evaluated θ          0–{mp.get('eval_theta_max_deg')}°   monotonic: {'yes' if mp.get('monotonic') else 'NO'}",
        f"  spot rms / r90       {_n(sp.get('rms_axis_mm'), '.2f')} / {_n(sp.get('r90_mm'), '.2f')} mm",
        f"  impact KE, TOF       {_n(sp.get('impact_KE_mean_eV'), '.0f')} eV, {_n(sp.get('tof_mean_us'), '.1f')} µs",
        "",
        "VOLTAGES (V)",
        "  " + "  ".join(f"{k} {v:+.0f}" for k, v in job.channels.items() if k.startswith("LV")),
        "  " + "  ".join(f"{k} {v:+.0f}" for k, v in job.channels.items() if not k.startswith("LV")),
        "  tip " + f"{pots.get('tip', float('nan')):+.1f}" + "   " + "  ".join(
            f"{k.upper()} {v:+.0f}" for k, v in pots.items() if k.startswith("e") and v),
        "  wiring " + " ".join(f"{k}:{v}" for k, v in job.wiring.items()),
        "",
        "POSITIONS (mm)   " + "  ".join(f"{k} {v / units.MM:.1f}" for k, v in job.positions.items()),
        "",
        f"LAUNCH  Na+ {L.E0_eV:g} eV, {L.hwhm_deg:g}° HWHM at the {L.emission_angle_at}",
    ]
    if pre.get("preaccel_eV"):
        amap = next(iter((pre.get("angle_map_deg") or {}).values()), {})
        lines.append(f"  pre-accel +{pre['preaccel_eV']:.1f} eV" +
                     (f";  20° -> {amap['20']:.1f}° at launch" if "20" in amap else ""))
    lines += ["", f"valid: {metrics.get('valid')}   feasible: {metrics.get('feasible')}"]
    lines += [f"  ! {fl}" for fl in (metrics.get("flags") or [])[:4]]
    return "\n".join(lines)


def plot_summary(d: Path, out: Path, cfg: Config, job, geom: dict, metrics: dict) -> Path | None:
    """One page per run: beam through the chamber and the lens stack, axis potential, mapping, numbers."""
    from .electrodes import node_potentials

    if not (d / FILES["traj"]).is_file() or not (d / FILES["ions_derived"]).is_file():
        return None
    ions = pd.read_csv(d / FILES["ions_launch"])
    tr = pd.read_csv(d / FILES["traj"]).merge(ions[["ion_id", "theta_deg"]], on="ion_id")
    dv = pd.read_csv(d / FILES["ions_derived"])
    meta = read_json(d / FILES["meta"]) if (d / FILES["meta"]).is_file() else {}
    pots = node_potentials(job, cfg)
    z_lo, z_hi = z_limits_mm(cfg, job.cfg, geom)
    r_el = max((e["r_out_m"] for e in geom.get("electrodes", [])), default=0.03) / units.MM

    fig = plt.figure(figsize=(15, 10.5))
    gs = fig.add_gridspec(3, 3, height_ratios=[1.0, 1.25, 0.95], width_ratios=[1, 1, 0.85], hspace=0.55, wspace=0.22)

    # whole chamber
    ax = fig.add_subplot(gs[0, :])
    vmax = 1.0
    if (d / FILES["cutplane_field"]).is_file():
        zs, rs, g = _grid(d / FILES["cutplane_field"])
        vmax = max(np.nanmax(np.abs(g)), 1.0)
        m = _potential_bg(ax, zs, rs, g, vmax)
        fig.colorbar(m, ax=ax, label="V (V)", pad=0.005, fraction=0.02)
    else:
        _electrodes_filled(ax, geom)
    norm = _trajectories(ax, tr, dv, cfg)
    ax.axvline(geom["z_mesh_m"] / units.MM, color=INK, lw=0.8, ls="--")
    ax.axvline(geom["z_mcp_m"] / units.MM, color=INK, lw=1.4)
    ax.axhline(_r_active_mm(cfg), xmin=0.95, color=INK, lw=0.8)
    ax.set_xlim(z_lo, z_hi)
    r_beam = float(np.nanmax(np.hypot(tr["x_m"], tr["y_m"]))) / units.MM if len(tr) else 0.0
    ax.set_ylim(0, 1.15 * max(_r_active_mm(cfg), min(r_beam, 1.4 * r_el)))
    ax.set(xlabel="z from tip (mm)", ylabel="r (mm)", title="Beam through the chamber")
    _subtitle(ax, "blue: reaches the MCP (shade = emission angle θ)  ·  red: lost  ·  dashed: mesh  ·  solid: MCP  ·  "
                  "background: potential (symmetric log, linear within ±10 V)")

    # lens region
    ax = fig.add_subplot(gs[1, :2])
    z_end = (max(e["z_m"] + e["thickness_m"] / 2 for e in geom["electrodes"]) / units.MM + 10) if geom.get("electrodes") else 160
    f_lens = d / FILES["cutplane_lens"]
    if f_lens.is_file():
        zs, rs, g = _grid(f_lens)
        _potential_bg(ax, zs, rs, g, vmax, contours=40)
        z_end = zs.max()
    else:
        _electrodes_filled(ax, geom)
    _electrode_labels(ax, geom, pots)
    _trajectories(ax, tr, dv, cfg, z_max=z_end)
    ax.plot([0], [0], marker=">", color=INK, ms=7, zorder=6, clip_on=False)
    ax.set_xlim(-2, z_end)
    r_in = min((e["r_in_m"] for e in geom.get("electrodes", [])), default=0.005) / units.MM
    ax.set_ylim(0, 2.0 * r_in)
    ax.set(xlabel="z from tip (mm)", ylabel="r (mm)", title="Tip and lens stack (bore region)")
    v_tip = (meta.get("comsol_params") or {}).get("v_tip", "?")
    try:
        v_tip = f"{float(str(v_tip).split('[')[0]):+.1f} V"
    except ValueError:
        pass
    ax.set_title(ax.get_title(loc="left"), loc="left", pad=36)
    ax.text(0, 1.105, f"labels: electrode, potential (V)  ·  gray: metal (model geometry)  ·  lines: 40 equipotentials  ·  model tip (z = 0) at "
                      f"{v_tip}, the potential after pre-acceleration", transform=ax.transAxes, fontsize=8, color=INK2)
    fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=SEQ), ax=ax, label="emission angle θ (deg)", pad=0.01, fraction=0.03)

    # numbers
    ax = fig.add_subplot(gs[1:, 2])
    ax.axis("off")
    ax.text(0, 1, _stats_text(job, cfg, metrics, meta, pots), transform=ax.transAxes, va="top", ha="left",
            family="monospace", fontsize=8.3, color=INK, linespacing=1.35)

    # axis potential
    ax = fig.add_subplot(gs[2, 0])
    if (d / FILES["axis_potential"]).is_file():
        ap = pd.read_csv(d / FILES["axis_potential"])
        ax.plot(ap["z_m"] / units.MM, ap["V_V"], color=BLUE)
        ax.set_yscale("symlog", linthresh=10)
    for e in geom.get("electrodes", []):
        ax.axvline(e["z_m"] / units.MM, color=MUTED, lw=0.5, ls=":")
    ax.axvline(geom["z_mcp_m"] / units.MM, color=INK, lw=1.0)
    ax.set_xlim(z_lo, z_hi)
    ax.set(xlabel="z from tip (mm)", ylabel="V on axis (V, symlog)", title="Axis potential")

    # mapping
    ax = fig.add_subplot(gs[2, 1])
    mp = metrics.get("mapping") or {}
    if mp.get("theta_deg"):
        th = np.array(mp["theta_deg"])
        r = np.array([np.nan if v is None else v for v in mp["r_mm"]])
        lf = np.array(mp.get("landed_frac") or [np.nan] * len(th))
        ax.plot(th, r, color=BLUE, marker="o", ms=3.5, label="landing radius r(θ)")
        ax.set_ylim(0, 1.25 * _r_active_mm(cfg))
        ax.axhline(_r_active_mm(cfg), color=INK2, lw=0.8, ls="--")
        ax.text(0.5, _r_active_mm(cfg), " MCP active edge", fontsize=7, color=INK2, va="bottom")
        lostth = th[lf < 0.5]
        if len(lostth):
            ax.plot(lostth, np.full(len(lostth), 0.3), ls="none", marker="x", color=RED, ms=5, label="lost")
        if mp.get("eval_theta_max_deg") is not None:
            ax.axvspan(mp["eval_theta_max_deg"], cfg.spec.launch.theta_max_deg, color=GRID, alpha=0.5, lw=0)
        ax.axvline(cfg.spec.launch.hwhm_deg, color=MUTED, lw=0.8, ls=":")
        ax.text(cfg.spec.launch.hwhm_deg, 0.02, " HWHM", transform=ax.get_xaxis_transform(), fontsize=7, color=INK2)
        ax.legend(loc="upper right", bbox_to_anchor=(1, 0.78))
    ax.set_xlim(0, cfg.spec.launch.theta_max_deg)
    ax.set(xlabel="emission angle θ (deg)", ylabel="r on MCP (mm)", title="Image mapping")

    fig.suptitle(f"Run {job.job_id[:12]}  ·  MCP {metrics.get('fates', {}).get('mcp_active', 0):.0%}  ·  "
                 f"score {metrics.get('score') if metrics.get('score') is None else round(metrics['score'], 2)}°",
                 x=0.01, ha="left", fontsize=13, fontweight="bold", color=INK)
    fig.savefig(out / "summary.png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return out / "summary.png"


def plot_study_history(rows: list[dict], out_png: Path, title: str, cap_deg: float) -> Path:
    """Optimization progress: score per trial with the best feasible so far, and MCP fraction per trial.

    rows: {trial, score, mcp, feasible, valid}. Scores above cap_deg (or missing) are drawn at the cap.
    """
    rows = sorted(rows, key=lambda r: r["trial"])
    t = np.array([r["trial"] for r in rows])
    sc = np.array([cap_deg if r["score"] is None or not math.isfinite(r["score"]) else min(r["score"], cap_deg)
                   for r in rows])
    feas = np.array([bool(r["feasible"]) for r in rows])
    valid = np.array([bool(r["valid"]) for r in rows])
    mcp = np.array([r["mcp"] or 0.0 for r in rows])
    best, b = [], math.inf
    for s_, f in zip(sc, feas):
        b = min(b, s_) if f else b
        best.append(b if math.isfinite(b) else np.nan)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(9, 5.6), sharex=True, gridspec_kw={"hspace": 0.35})
    a1.scatter(t[feas], sc[feas], s=22, color=BLUE, label="feasible", zorder=3)
    a1.scatter(t[~feas & valid], sc[~feas & valid], s=22, facecolors="none", edgecolors=MUTED, label="infeasible")
    a1.scatter(t[~valid], np.full((~valid).sum(), cap_deg), s=22, marker="x", color=RED, label="invalid / failed")
    a1.step(t, best, where="post", color=INK, lw=1.2, label="best feasible so far")
    a1.set_yscale("log")
    a1.set(ylabel="score = worst dθ (deg)", title=title)
    a1.legend(loc="upper right", ncol=2)
    _subtitle(a1, "lower is better")
    a2.bar(t, mcp, color=np.where(feas, BLUE, BLUE_LIGHT), width=0.8)
    a2.set_ylim(0, 1)
    a2.set(xlabel="trial", ylabel="fraction on the MCP", title="Transmission per trial")
    a2.grid(axis="x", visible=False)
    return _save(fig, out_png)


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
    if geom and metrics:
        made.append(plot_summary(d, out, cfg, job, geom, metrics))
    return [p for p in made if p is not None]
