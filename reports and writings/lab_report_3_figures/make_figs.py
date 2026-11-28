"""Figures for Lab Report 3 (draft). Reads the run log and stored results; writes PNGs."""
import json, sqlite3, sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path(sys.argv[1])
OUT = Path(sys.argv[2]); OUT.mkdir(parents=True, exist_ok=True)
SPEC = "3096a6d355e234ef625fea76da5fce2d0a4764848fbfe4dce7815d36fcffc5a6"  # current spec
BEST = "69da2f2d6e4843ac8205a1a141e19d51"

BLUE, ORANGE, AQUA, GRAY = "#2a78d6", "#eb6834", "#1baf7a", "#a3a29c"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "legend.frameon": False, "savefig.dpi": 220, "figure.facecolor": "white",
})

# ---- Fig: best B0 design, cropped from the run's stored summary.png ----
im = Image.open(ROOT / "results" / BEST / "plots" / "summary.png")
from PIL import ImageDraw
cr = im.crop((0, 85, 1540, 755)); ImageDraw.Draw(cr).rectangle((1105, 345, 1540, 670), fill=im.getpixel((5, 5)))
cr.save(OUT / "fig_best_b0_beam.png")

# ---- Fig: image mapping r(theta) and resolution dtheta(theta) of the best design ----
m = json.load(open(ROOT / "results" / BEST / "metrics.json"))
mp = m["mapping"]
th = [t for t, r in zip(mp["theta_deg"], mp["r_mm"]) if r is not None]
r = [x for x in mp["r_mm"] if x is not None]
dt = [x for x in mp["dtheta_deg"] if x is not None]
lost = [t for t, r_ in zip(mp["theta_deg"], mp["r_mm"]) if r_ is None]
fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 2.4), constrained_layout=True)
a.plot(th, r, color=BLUE, lw=2, marker="o", ms=4)
a.plot(lost, [0] * len(lost), ls="none", marker="x", ms=5, color="#e34948")
a.axvline(20, color=INK2, lw=0.8, ls=":"); a.text(20.5, 2.25, "HWHM 20°", color=INK2, fontsize=8)
a.text(31, 0.25, "lost on electrodes", color="#e34948", fontsize=8)
a.set_xlabel("emission angle θ at the meniscus (deg)"); a.set_ylabel("landing radius on MCP (mm)")
a.set_xlim(0, 50); a.set_ylim(0, 2.6)
a.set_title("(a) image mapping r(θ): monotonic", loc="left", fontsize=9, color=INK)
b.plot(th, dt, color=BLUE, lw=2, marker="o", ms=4)
b.axhline(max(dt), color=INK2, lw=0.8, ls="--"); b.text(1, max(dt) + 0.03, f"score = worst δθ = {max(dt):.2f}°", color=INK2, fontsize=8)
b.set_xlabel("emission angle θ (deg)"); b.set_ylabel("angular resolution δθ (deg)")
b.set_xlim(0, 24); b.set_ylim(0, 1.3)
b.set_title("(b) resolution δθ(θ), σ_MCP = 70 µm", loc="left", fontsize=9, color=INK)
fig.savefig(OUT / "fig_best_b0_mapping.png"); plt.close(fig)

# ---- Fig: B0 dev3 trade-off and convergence ----
c = sqlite3.connect(ROOT / "results" / "runlog.sqlite")
rows = c.execute("""select j.config_id, j.created_at, m.valid, m.feasible, m.score, m.eta, m.metrics_json
  from jobs j join metrics m on j.job_id=m.job_id
  where j.study_id like 'b0-%-2d-dev3' and m.spec_hash=? order by j.created_at""", (SPEC,)).fetchall()
COL = {"c3_einzel_accel": BLUE, "c3_einzel_split": ORANGE, "c3_extractor": AQUA}
LAB = {"c3_einzel_accel": "Einzel + accel. stage", "c3_einzel_split": "split Einzel", "c3_extractor": "extractor only"}
fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 3.0), constrained_layout=True)
other = [(row[4], row[5]) for row in rows if row[0] not in COL and row[4] is not None]
a.scatter([s for s, e in other], [e for s, e in other], s=14, color=GRAY, alpha=0.6, lw=0,
          label="Einzel / grounded tip (0 feasible)")
for cid, col in COL.items():
    pts = [(row[4], row[5], row[3]) for row in rows if row[0] == cid and row[4] is not None]
    f = [(s, e) for s, e, ok in pts if ok]; nf = [(s, e) for s, e, ok in pts if not ok]
    a.scatter([s for s, e in nf], [e for s, e in nf], s=16, facecolor="none", edgecolor=col, lw=0.9)
    a.scatter([s for s, e in f], [e for s, e in f], s=18, color=col, lw=0, label=LAB[cid])
a.axhline(0.4, color=INK2, lw=0.8, ls="--"); a.text(900, 0.37, "η_min = 0.4", color=INK2, fontsize=8, ha="right", va="top")
a.set_xscale("log"); a.set_xlabel("score: worst δθ (deg, lower is better)"); a.set_ylabel("collection efficiency η")
a.set_ylim(0, 0.75)
a.set_title("(a) all 298 B0 trials (filled = feasible)", loc="left", fontsize=9, color=INK)
fig.legend(*a.get_legend_handles_labels(), fontsize=7, loc="outside lower center", ncol=4, handletextpad=0.2)
for cid, col in COL.items():
    best, xs, ys = None, [], []
    for i, row in enumerate([row for row in rows if row[0] == cid]):
        if row[3] and (best is None or row[4] < best):
            best = row[4]
        xs.append(i); ys.append(best)
    b.step(xs, ys, where="post", color=col, lw=2, label=LAB[cid])
    b.text(xs[-1] + 0.5, ys[-1], f"{ys[-1]:.2f}°", color=INK, fontsize=8, va="center")
b.set_yscale("log"); b.set_xlim(0, 66); b.set_xlabel("trial (2D solve)"); b.set_ylabel("best feasible δθ so far (deg)")
b.set_title("(b) TPE convergence, 60 trials per config.", loc="left", fontsize=9, color=INK)
fig.savefig(OUT / "fig_b0_tradeoff.png"); plt.close(fig)

# ---- Fig: 2D vs 3D fidelity check (task 10) ----
d = json.load(open(ROOT / "logs" / "fidelity_20261113_task10.json"))
names = [f"S{i+1}" for i in range(len(d["pairs"]))]
t2 = [p["fates_2d"]["mcp_active"] * 100 for p in d["pairs"]]
t3 = [p["fates_3d"]["mcp_active"] * 100 for p in d["pairs"]]
ratio = [1 + p["mapping"]["dtheta_rel_median"] for p in d["pairs"]]
fig, (a, b) = plt.subplots(1, 2, figsize=(6.6, 2.3), constrained_layout=True)
x = range(len(names)); w = 0.38
a.bar([i - w / 2 - 0.01 for i in x], t2, w, color=BLUE, label="2D axisymmetric")
a.bar([i + w / 2 + 0.01 for i in x], t3, w, color=ORANGE, label="3D")
a.set_xticks(list(x), names); a.set_ylabel("ions reaching MCP (%)"); a.set_ylim(0, 45)
a.set_title("(a) transmission: 2D within +1 to +5 pts", loc="left", fontsize=9, color=INK)
a.legend(fontsize=7, loc="upper right", ncol=2)
b.bar(list(x), ratio, 0.55, color=ORANGE)
b.axhline(1, color=INK2, lw=0.8, ls="--"); b.text(4.35, 1.15, "2D = 3D", color=INK2, fontsize=8, ha="right")
for i, v in enumerate(ratio):
    b.text(i, v + 0.1, f"{v:.1f}×", ha="center", fontsize=8, color=INK)
b.set_xticks(list(x), names); b.set_ylabel("median δθ, 3D / 2D"); b.set_ylim(0, 7.5)
b.set_title("(b) resolution: 3D δθ is 4–6.5× the 2D value", loc="left", fontsize=9, color=INK)
fig.savefig(OUT / "fig_fidelity.png"); plt.close(fig)
print("ok", sorted(p.name for p in OUT.glob("*.png")))
