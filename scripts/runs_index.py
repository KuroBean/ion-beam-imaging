"""Browsable overview of the agent runs: what each run and each round tested, and what came out.

    python scripts/runs_index.py                      # every run in the run log
    python scripts/runs_index.py --runs run-3-cfg1    # one run's page, then the cross-run index
    python scripts/runs_index.py --study-reports      # also build missing results/report_<study>.html

Writes (all under results/, which is git-ignored; nothing is moved, job folders stay results/<job_id>):
  results/index.html                       every run: goal, best result, thumbnail; links to everything else
  results/runs/<run_id>/report/index.html  one row per round: what was tried, why, result, critic, best-run figure
  results/runs/<run_id>/report/rounds.png  score and eta per round, running best
  results/best/<run_id>_r<NN>_<score>deg_<plot>.png (+ _best.json, README.md)  each real run's best figures
Reads only: results/runlog.sqlite, results/runs/<run_id>/ (summary.json, run_config.json), job folders,
variant manifests, logs/<run_id>-goal.txt.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import shutil
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from ionopt.config import load_config  # noqa: E402
from ionopt.report import SORT_JS  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
BEST_PLOTS = ("summary", "trajectories", "r_theta", "dtheta", "fates")
ALL_PARTS = [f"e{i}" for i in range(1, 10)] + ["d1", "d2"]

# dataviz reference palette (light), as in scripts/agent_run_report.py
BLUE, ORANGE, INK, INK2, MUTED, GRID, SURFACE = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"

CSS = """
<style>
:root { --bg:#fcfcfb; --card:#ffffff; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781; --grid:#e1e0d9;
  --bad:#b3261e; --ok:#1c5cab; --star:#b26a00; --hl:#fff6e0; }
@media (prefers-color-scheme: dark) { :root { --bg:#151514; --card:#1d1d1c; --ink:#ededeb; --ink2:#b9b8b3;
  --muted:#8b8a85; --grid:#33332f; --bad:#f08a80; --ok:#8db8f0; --star:#f0b350; --hl:#2b2618; } }
body { background:var(--bg); color:var(--ink); font:14px/1.45 system-ui, sans-serif; margin:16px; max-width:1500px; }
h1 { font-size:21px; margin:0 0 4px; } h2 { font-size:17px; margin:26px 0 8px; } .sub { color:var(--ink2); margin:0 0 12px; }
a { color:var(--ok); } table { border-collapse:collapse; width:100%; }
th, td { border-bottom:1px solid var(--grid); padding:7px 8px; text-align:left; vertical-align:top; }
th { cursor:pointer; color:var(--ink2); font-weight:600; position:sticky; top:0; background:var(--bg); }
td.num { font-variant-numeric:tabular-nums; white-space:nowrap; } .small { font-size:12px; color:var(--ink2); }
.mono { font-family:ui-monospace, monospace; font-size:12px; } .bad { color:var(--bad); } .ok { color:var(--ok); }
.star { color:var(--star); font-weight:700; } tr.best td { background:var(--hl); }
img.thumb { width:300px; border:1px solid var(--grid); } img.big { max-width:900px; width:100%; border:1px solid var(--grid); }
img.wide { max-width:900px; width:100%; }
.card { background:var(--card); border:1px solid var(--grid); border-radius:6px; padding:12px 14px; margin:10px 0; }
.goal { white-space:pre-wrap; } details summary { cursor:pointer; color:var(--ink2); }
.kv { display:grid; grid-template-columns:max-content 1fr; gap:2px 14px; } .kv b { color:var(--ink2); font-weight:600; }
ul.tight { margin:4px 0; padding-left:18px; } .score { font-size:16px; font-weight:700; }
@media (max-width: 700px) { img.thumb { width:200px; } body { margin:12px; } }
</style>
"""


# --------------------------------------------------------------------------- data helpers


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}


def esc(x) -> str:
    return html.escape("" if x is None else str(x))


def run_config(base_cfg, run_dir: Path):
    """The config the run used (its stored overrides), as cli_agents does on resume."""
    stored = load_json(run_dir / "run_config.json").get("overrides") or []
    files = [o[len("@file:"):] for o in stored if o.startswith("@file:")]
    files = [f if Path(f).is_file() else str(base_cfg.root_dir / f) for f in files]
    sets = [o for o in stored if not o.startswith("@file:")]
    try:
        return load_config(None, sets, files)
    except Exception as e:  # noqa: BLE001 - an old override that no longer validates: fall back
        print(f"  {run_dir.name}: cannot load its overrides ({e}); using the default config")
        return base_cfg


def sentences(text: str | None, n: int) -> str:
    t = re.sub(r"\s+", " ", text or "").strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", t)
    return " ".join(parts[:n])


def goal_text(run_id: str, summary: dict, con) -> str | None:
    f = REPO / "logs" / f"{run_id}-goal.txt"
    if f.is_file():
        return f.read_text(encoding="utf-8").strip()
    assumptions = summary.get("assumptions")
    if assumptions is None:
        r = con.execute("select assumptions_json from agent_runs where run_id = ?", (run_id,)).fetchone()
        assumptions = json.loads(r[0] or "[]") if r else []
    return next((x.split(": ", 1)[1] for x in assumptions if x.startswith("author goal")), None)


def variant_chain(results: Path, vid: str | None) -> list[dict]:
    out, seen = [], set()
    while vid and vid not in seen and vid != "base":
        seen.add(vid)
        m = load_json(results / "variants" / vid / "variant.json")
        if not m:
            break
        out.append(m)
        vid = m.get("parent")
    return out


def mesh_state(results: Path, conf: dict | None) -> str:
    items = {i for m in variant_chain(results, (conf or {}).get("variant_id")) for i in m.get("inventory_items", [])}
    if "no_screen_mesh" in items:
        return "no screen mesh"
    if "screen_mesh_wide" in items:
        return "wide screen mesh"
    return "screen mesh"


def part_label(p: str) -> str:
    return p.upper()


def compress(parts: list[str]) -> str:
    """e5 e6 e7 e8 e9 d1 d2 -> E5-E9, D1, D2"""
    out, i = [], 0
    while i < len(parts):
        j = i
        while (j + 1 < len(parts) and parts[j + 1][0] == parts[i][0]
               and int(parts[j + 1][1:]) == int(parts[j][1:]) + 1):
            j += 1
        out.append(part_label(parts[i]) + (f"–{part_label(parts[j])}" if j > i + 1 else
                                           f", {part_label(parts[j])}" if j == i + 1 else ""))
        i = j + 1
    return ", ".join(out)


def structure(results: Path, conf: dict | None) -> dict:
    """Short human-readable description of a configuration."""
    if not conf:
        return {"lens": "-", "removed": "", "mesh": "", "moved": "", "cfg": None}
    cfgn = conf.get("cfg")
    parts = [p for p in ALL_PARTS if cfgn == 3 or not p.startswith("d")]
    removed = [p for p in parts if p in set(conf.get("removed") or [])]
    wiring = conf.get("wiring") or {}
    present = [p for p in parts if p not in removed]
    lens = " ".join(f"{part_label(p)}:{wiring.get(p, 'gnd')}" for p in present)
    if "tip" in wiring:
        lens = f"tip:{wiring['tip']} " + lens
    moved = conf.get("moved") or []
    return {"lens": lens or "-", "removed": compress(removed), "mesh": mesh_state(results, conf),
            "moved": ", ".join(str(m) for m in moved), "cfg": cfgn, "variant": conf.get("variant_id") or "base"}


def job_info(results: Path, job_id: str | None) -> dict:
    return load_json(results / job_id / "job.json") if job_id else {}


def volts_str(job: dict) -> str:
    ch = job.get("channels") or {}
    return ", ".join(f"{k} {v:+.0f} V" for k, v in ch.items())


def pos_str(job: dict) -> str:
    pos = job.get("positions") or {}
    return ", ".join(f"{k} {v * 1e3:.1f} mm" for k, v in pos.items() if isinstance(v, (int, float)))


def fmt_bounds(b: dict | None) -> str:
    if not b:
        return "full usable ranges"
    return ", ".join(f"{k} [{v['lo']:g}, {v['hi']:g}]" for k, v in b.items())


def fnum(v, f="{:.3g}") -> str:
    return f.format(v) if isinstance(v, (int, float)) and math.isfinite(v) else "–"


def load_run(con, results: Path, run_id: str) -> dict:
    run_dir = results / "runs" / run_id
    r = con.execute("select method, started_at, finished_at, stop_reason, best_job_id, best_score, solves_used "
                    "from agent_runs where run_id = ?", (run_id,)).fetchone()
    summary = load_json(run_dir / "summary.json")
    rounds = []
    for rnd, action, diag, study, n, best, score, eta, feas, verdict, counted, rec in con.execute(
            "select round, action, diagnosis, study_id, n_solves, best_job_id, score, eta, feasible, critic_verdict, "
            "counted, record_json from agent_rounds where run_id = ? order by round", (run_id,)):
        rec = json.loads(rec or "{}")
        rounds.append({"round": rnd, "action": action, "diagnosis": diag, "study_id": study, "n_solves": n,
                       "best_job_id": best, "score": score, "eta": eta, "feasible": feas, "critic": verdict,
                       "counted": counted, "proposal": rec.get("proposal") or {}, "critic_out": rec.get("critic") or {},
                       "metrics": rec.get("metrics") or {}, "note": rec.get("note")})
    cost = con.execute("select sum(cost_usd), count(*) from agent_calls where run_id = ?", (run_id,)).fetchone()
    best = summary.get("best") or {}
    if not best and r and r[4]:
        best = {"job_id": r[4], "score": r[5]}
        best.update(next(({"round": x["round"], "eta": x["eta"]} for x in rounds if x["best_job_id"] == r[4]), {}))
    return {"run_id": run_id, "dir": run_dir, "row": r, "summary": summary, "rounds": rounds, "best": best,
            "cost": cost[0] or 0.0, "n_calls": cost[1], "goal": goal_text(run_id, summary, con),
            "run_config": load_json(run_dir / "run_config.json")}


def is_real(run_id: str) -> bool:
    return run_id.startswith("run-") and not run_id.endswith("prompt-check")


def overrides_short(rc: dict) -> str:
    keep = []
    for o in rc.get("overrides") or []:
        if o.startswith("@file:"):
            keep.append(Path(o[6:]).name)
        elif o.startswith("backend."):
            continue
        else:
            k, _, v = o.partition("=")
            keep.append(f"{k.split('.')[-1]}={v}")
    rr = (rc.get("loop") or {}).get("require_removed")
    if rr:
        keep.append("require_removed=" + ",".join(rr))
    return "; ".join(keep)


# --------------------------------------------------------------------------- figure


def rounds_figure(run: dict, out: Path, eta_min: float | None) -> Path | None:
    rows = [r for r in run["rounds"] if isinstance(r["score"], (int, float)) and r["score"] > 0]
    if not rows:
        return None
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "font.family": "DejaVu Sans"})
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(8.0, 5.2), facecolor=SURFACE,
                                   gridspec_kw={"height_ratios": [1.4, 1], "hspace": 0.08})
    for ax in (ax1, ax2):
        ax.set_facecolor(SURFACE)
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    good = [r for r in rows if r["feasible"] and r["counted"]]
    bad = [r for r in rows if not (r["feasible"] and r["counted"])]
    ax1.scatter([r["round"] for r in good], [r["score"] for r in good], s=46, color=BLUE, zorder=3,
                label="feasible, counted")
    ax1.scatter([r["round"] for r in bad], [r["score"] for r in bad], s=46, facecolors="none", edgecolors=ORANGE,
                linewidths=1.5, zorder=3, label="infeasible or critic-rejected (not counted)")
    xs, ys, cur = [], [], None
    for r in sorted(rows, key=lambda r: r["round"]):
        if r in good and (cur is None or r["score"] < cur):
            cur = r["score"]
        if cur is not None:
            xs.append(r["round"])
            ys.append(cur)
    if xs:
        ax1.step(xs, ys, where="post", color=INK, linewidth=1.2, zorder=2, label="best so far")
    bj = run["best"].get("job_id")
    br = next((r for r in rows if r["best_job_id"] == bj), None)
    if br:
        ax1.scatter([br["round"]], [br["score"]], s=200, facecolors="none", edgecolors=INK, linewidths=1.2, zorder=4)
        ax1.annotate(f"run best {br['score']:.3g}°", (br["round"], br["score"]), xytext=(0, 13), ha="center",
                     textcoords="offset points", fontsize=9, color=INK)
    ax1.set_yscale("log")
    ax1.set_ylabel("worst-case dθ (deg, log)\nlower is better")
    ax2.scatter([r["round"] for r in good], [r["eta"] for r in good], s=30, color=BLUE, zorder=3)
    ax2.scatter([r["round"] for r in bad], [r["eta"] for r in bad], s=30, facecolors="none", edgecolors=ORANGE,
                linewidths=1.4, zorder=3)
    if eta_min is not None:
        ax2.axhline(eta_min, color=INK2, linewidth=1.1, linestyle=(0, (4, 3)))
        ax2.annotate(f"eta_min {eta_min:g}", (1.0, eta_min), xycoords=("axes fraction", "data"), xytext=(0, 3),
                     textcoords="offset points", ha="right", va="bottom", fontsize=8.5, color=INK2)
    ax2.set_ylim(0, 1.0)
    ax2.set_ylabel("collection η")
    ax2.set_xlabel("round (each round = one optimizer study of the planner's proposal; dot = its best run)")
    ax2.set_xticks([r["round"] for r in rows])
    ax1.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncol=3, frameon=False, fontsize=8.5, labelcolor=INK2)
    ax1.set_title(f"{run['run_id']}: best run of each round", loc="left", fontsize=10.5, color=INK, pad=24)
    f = out / "rounds.png"
    fig.savefig(f, dpi=150, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return f


# --------------------------------------------------------------------------- per-run page


def claim_marks(critic: dict) -> str:
    sym = {"supported": "✓", "contradicted": "✗"}
    return " ".join(f"{esc(c.get('claim_id'))}{sym.get(c.get('status'), '?')}" for c in critic.get("claim_checks") or [])


def round_row(run: dict, r: dict, results: Path, best_job: str | None) -> str:
    p, c, m = r["proposal"], r["critic_out"], r["metrics"]
    conf = p.get("configuration")
    st = structure(results, conf)
    job = job_info(results, r["best_job_id"])
    is_best = r["best_job_id"] and r["best_job_id"] == best_job
    # what was tried
    tried = [f"<b>{esc(st['lens'])}</b>"]
    if st["removed"]:
        tried.append(f"removed {esc(st['removed'])}")
    tried.append(esc(st["mesh"]) + (f"; moved {esc(st['moved'])}" if st["moved"] else ""))
    if p.get("edit_request"):
        e = p["edit_request"]
        tried.append(f"<span class='star'>model edit</span>: {esc(sentences(e.get('description'), 1))}")
    tried_html = "<br>".join(tried)
    tried_html += (f"<details><summary>bounds, budget</summary><span class='mono'>{esc(fmt_bounds(p.get('bounds')))}"
                   f"</span><br>solve budget {esc(p.get('solve_budget'))}; variant {esc(st.get('variant'))}</details>")
    # why
    why = esc(sentences(p.get("rationale"), 2))
    claims = "".join(f"<li><b>{esc(x.get('id'))}</b> {esc(x.get('statement'))}</li>" for x in p.get("claims") or [])
    why += (f"<details><summary>full reasoning</summary><p><i>Diagnosis ({esc(r['diagnosis'])}):</i> "
            f"{esc(p.get('diagnosis_evidence'))}</p><p><i>Rationale:</i> {esc(p.get('rationale'))}</p>"
            f"<p><i>Claims for the critic:</i></p><ul class='tight'>{claims}</ul></details>")
    # result
    ok = r["feasible"] and r["counted"]
    sp = m.get("spot") or {}
    res = (f"<span class='score {'ok' if ok else 'bad'}'>{fnum(r['score'])}°</span>"
           + (" <span class='star'>★ run best</span>" if is_best else "")
           + f"<br>η {fnum(r['eta'], '{:.3f}')}<br>"
           + ("feasible" if r["feasible"] else "<span class='bad'>infeasible</span>")
           + ("" if r["counted"] else "<br><span class='bad'>not counted (critic rejected)</span>")
           + f"<br><span class='small'>{esc(r['n_solves'])} solves<br>r_max {fnum(sp.get('r_max_mm'), '{:.1f}')} mm, "
           f"fill {fnum(sp.get('fill_fraction'), '{:.2f}')}<br>θ evaluated to {esc(m.get('eval_theta_max_deg'))}°</span>")
    flags = m.get("flags") or []
    if flags:
        res += "<br><span class='small bad'>" + "<br>".join(esc(f) for f in flags[:3]) + "</span>"
    if job:
        res += (f"<details><summary>voltages, positions</summary><span class='mono'>{esc(volts_str(job))}<br>"
                f"{esc(pos_str(job))}</span></details>")
    # critic
    fm = c.get("observed_failure_modes") or []
    verdict = (c.get("verdict") or r["critic"] or "-").lower()
    vcls = "ok" if verdict == "accept" else "bad" if verdict == "reject" else ""
    crit = (f"<b class='{vcls}'>{esc(verdict)}</b> <span class='mono'>{claim_marks(c)}</span>"
            f"<br>{esc(fm[0]) if fm else esc(sentences(c.get('reasons'), 2))}")
    rest = "".join(f"<li>{esc(x)}</li>" for x in fm[1:])
    sugg = "".join(f"<li>{esc(x)}</li>" for x in c.get("suggestions") or [])
    if c:
        crit += (f"<details><summary>full critique</summary><p>{esc(c.get('reasons'))}</p>"
                 + (f"<p><i>Other failure modes:</i></p><ul class='tight'>{rest}</ul>" if rest else "")
                 + (f"<p><i>Suggestions:</i></p><ul class='tight'>{sugg}</ul>" if sugg else "") + "</details>")
    if r.get("note"):
        crit += f"<br><span class='small'>note: {esc(r['note'])}</span>"
    # figure + links
    bj = r["best_job_id"]
    links = []
    if bj and (results / bj / "plots" / "summary.png").is_file():
        rel = f"../../../{bj}/plots/summary.png"
        fig = f"<a href='{rel}'><img class='thumb' src='{rel}' loading='lazy'></a>"
        links.append(f"<a href='../../../{bj}/plots/'>all plots</a>")
    else:
        fig = "<span class='small'>no figure</span>"
    if r["study_id"] and (results / f"report_{r['study_id']}.html").is_file():
        links.append(f"<a href='../../../report_{esc(r['study_id'])}.html'>every run of this round</a>")
    links.append(f"<a href='../calls/'>agent calls</a>")
    fig += "<br><span class='small'>" + " · ".join(links) + f"<br><span class='mono'>{esc((bj or '')[:12])}</span></span>"
    return (f"<tr class='{'best' if is_best else ''}'><td class='num' data-v='{r['round']}'><b>{r['round']}</b>"
            f"<br><span class='small'>{esc(r['action'])}<br>{esc(r['diagnosis'])}</span></td>"
            f"<td>{tried_html}</td><td>{why}</td>"
            f"<td class='num' data-v='{r['score'] if ok and r['score'] is not None else 99}'>{res}</td>"
            f"<td>{crit}</td><td>{fig}</td></tr>")


def best_card(run: dict, results: Path, prefix: str) -> str:
    b = run["best"]
    bj = b.get("job_id")
    if not bj:
        return "<div class='card'>No best result recorded.</div>"
    job = job_info(results, bj)
    conf = b.get("configuration") or next((r["proposal"].get("configuration") for r in run["rounds"]
                                           if r["best_job_id"] == bj), None)
    st = structure(results, conf)
    img = f"{prefix}{bj}/plots/summary.png"
    return (f"<div class='card'><div class='kv'><b>score (worst dθ)</b><span class='score'>{fnum(b.get('score'))}°</span>"
            f"<b>collection η</b><span>{fnum(b.get('eta'), '{:.3f}')}</span><b>round</b><span>{esc(b.get('round'))}</span>"
            f"<b>layout</b><span>cfg {esc(st['cfg'])}; {esc(st['lens'])}"
            + (f"; removed {esc(st['removed'])}" if st["removed"] else "") + f"; {esc(st['mesh'])}"
            + (f"; moved {esc(st['moved'])}" if st["moved"] else "") + "</span>"
            f"<b>voltages</b><span class='mono'>{esc(volts_str(job))}</span>"
            f"<b>positions</b><span class='mono'>{esc(pos_str(job))}</span>"
            f"<b>job</b><span class='mono'><a href='{prefix}{bj}/plots/'>{esc(bj)}</a></span></div>"
            f"<p><a href='{img}'><img class='big' src='{img}' loading='lazy'></a></p></div>")


def run_page(run: dict, results: Path, eta_min: float | None) -> Path:
    out = run["dir"] / "report"
    out.mkdir(parents=True, exist_ok=True)
    fig = rounds_figure(run, out, eta_min)
    row = run["row"] or (None,) * 7
    goal = run["goal"]
    first = goal.split("\n\n", 1)[0] if goal else "(no goal recorded)"
    best_job = run["best"].get("job_id")
    rows = "\n".join(round_row(run, r, results, best_job) for r in run["rounds"])
    head = ["round", "what was tried (layout: part:channel)", "why (planner)", "result (best run of the round)",
            "critic", "best run's figure"]
    th = "".join(f'<th data-k="{i}">{h}</th>' for i, h in enumerate(head))
    links = [f"<a href='transcript.md'>transcript.md</a> (everything, in order)" if (out / "transcript.md").is_file()
             else "", "<a href='../trace.md'>trace.md</a>", "<a href='../summary.json'>summary.json</a>",
             "<a href='../../../index.html'>all runs</a>"]
    page = (f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
            f"<title>{esc(run['run_id'])}</title>{CSS}</head><body>"
            f"<h1>Agent run {esc(run['run_id'])}</h1>"
            f"<p class='sub'>{esc((row[1] or '')[:16])} → {esc((row[2] or '')[:16])} UTC · stop: {esc(row[3])} · "
            f"{len(run['rounds'])} rounds · {esc(row[6])} solves · {run['n_calls']} agent calls, ~${run['cost']:.2f} · "
            f"settings: {esc(overrides_short(run['run_config']))}<br>{' · '.join(x for x in links if x)}</p>"
            f"<h2>What this run tested</h2><div class='card goal'>{esc(first)}"
            + (f"<details><summary>full goal given to the planner</summary><div class='goal'>{esc(goal)}</div></details>"
               if goal and goal != first else "") + "</div>"
            f"<h2>Best result</h2>{best_card(run, results, '../../../')}"
            + (f"<h2>Round by round</h2><img class='wide' src='{fig.name}'>" if fig else "<h2>Round by round</h2>")
            + "<p class='sub'>Each round the planner proposes a layout and voltage ranges, the optimizer runs a study "
              "(the listed solves), and the critic checks the study's best run against the planner's claims "
              "(✓ supported, ✗ contradicted). Click a column header to sort.</p>"
            f"<table><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table>{SORT_JS}</body></html>")
    f = out / "index.html"
    f.write_text(page, encoding="utf-8")
    return f


# --------------------------------------------------------------------------- best gallery


def best_gallery(runs: list[dict], results: Path) -> Path:
    out = results / "best"
    out.mkdir(exist_ok=True)
    lines = ["# Best result of each agent run", "", "Generated by `scripts/runs_index.py`; copies of the job folders' "
             "plots (the originals stay in `results/<job_id>/plots/`).", "",
             "| run | round | worst dθ (deg) | η | job | files |", "|---|---|---|---|---|---|"]
    for run in runs:
        b = run["best"]
        bj = b.get("job_id")
        if not bj or not (results / bj).is_dir():
            continue
        for old in out.glob(f"{run['run_id']}_*"):
            old.unlink()
        rnd = b.get("round")
        stem = f"{run['run_id']}_r{int(rnd):02d}_{b.get('score', 0):.3g}deg" if rnd else f"{run['run_id']}_best"
        files = []
        for p in BEST_PLOTS:
            src = results / bj / "plots" / f"{p}.png"
            if src.is_file():
                dst = out / f"{stem}_{p}.png"
                shutil.copy2(src, dst)
                files.append(dst.name)
        job = job_info(results, bj)
        info = {"run_id": run["run_id"], "round": rnd, "score_deg": b.get("score"), "eta": b.get("eta"), "job_id": bj,
                "job_folder": f"results/{bj}", "configuration": b.get("configuration"),
                "channels_V": job.get("channels"), "positions_m": job.get("positions"),
                "goal": (run["goal"] or "").split("\n\n", 1)[0]}
        (out / f"{run['run_id']}_best.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
        lines.append(f"| {run['run_id']} | {rnd} | {fnum(b.get('score'))} | {fnum(b.get('eta'), '{:.3f}')} | `{bj}` | "
                     + ", ".join(f"[{p}]({f})" for p, f in zip(BEST_PLOTS, files)) + f", [{run['run_id']}_best.json]"
                     f"({run['run_id']}_best.json) |")
    (out / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out


# --------------------------------------------------------------------------- cross-run index


def index_page(runs: list[dict], dev: list[str], results: Path) -> Path:
    rows = []
    for run in sorted(runs, key=lambda r: (r["row"] or ("",) * 3)[1] or "", reverse=True):
        b, row = run["best"], run["row"] or (None,) * 7
        bj = b.get("job_id")
        conf = b.get("configuration") or next((r["proposal"].get("configuration") for r in run["rounds"]
                                               if r["best_job_id"] == bj), None)
        st = structure(results, conf)
        first = sentences((run["goal"] or "").split("\n\n", 1)[0], 3)
        page = f"runs/{run['run_id']}/report/index.html"
        img = f"{bj}/plots/summary.png" if bj else ""
        thumb = (f"<a href='{page}'><img class='thumb' src='{img}' loading='lazy'></a>"
                 if bj and (results / img).is_file() else "")
        rows.append(
            f"<tr><td><a href='{page}'><b>{esc(run['run_id'])}</b></a><br><span class='small'>"
            f"{esc((row[1] or '')[:10])}<br>{len(run['rounds'])} rounds, {esc(row[6])} solves<br>stop: {esc(row[3])}"
            f"<br>{esc(overrides_short(run['run_config']))}</span></td>"
            f"<td>{esc(first)}</td>"
            f"<td class='num' data-v='{b.get('score') if b.get('score') is not None else 99}'>"
            f"<span class='score'>{fnum(b.get('score'))}°</span><br>η {fnum(b.get('eta'), '{:.3f}')}<br>"
            f"<span class='small'>round {esc(b.get('round'))}</span></td>"
            f"<td><span class='small'>cfg {esc(st['cfg'])}</span><br>{esc(st['lens'])}"
            + (f"<br><span class='small'>removed {esc(st['removed'])}</span>" if st["removed"] else "")
            + f"<br><span class='small'>{esc(st['mesh'])}</span><br><span class='mono small'>"
            f"{esc(volts_str(job_info(results, bj)))}</span></td>"
            f"<td>{thumb}<br><span class='small'><a href='{page}'>round by round</a>"
            + (f" · <a href='runs/{run['run_id']}/report/transcript.md'>transcript</a>"
               if (run["dir"] / "report" / "transcript.md").is_file() else "")
            + (f" · <a href='{bj}/plots/'>best job plots</a>" if bj else "") + "</span></td></tr>")
    head = ["run", "what it tested (goal, first sentences)", "best", "best layout (part:channel) and voltages",
            "best run's figure"]
    th = "".join(f'<th data-k="{i}">{h}</th>' for i, h in enumerate(head))
    agent_ids = {r["run_id"] for r in runs} | set(dev)
    studies = sorted(p for p in results.glob("report_*.html")
                     if not any(p.stem.startswith(f"report_{a}") for a in agent_ids))
    groups: dict[str, list[Path]] = {}
    for p in studies:
        s = p.stem[len("report_"):]
        key = "Baseline B0 (fixed hand-made layouts, optimizer only)" if s.startswith("b0") else \
            "Development checks" if s.startswith(("devtest", "plot_dev", "latest")) else "Standalone studies"
        groups.setdefault(key, []).append(p)
    other = "".join(f"<h3>{esc(k)}</h3><ul class='tight'>" + "".join(
        f"<li><a href='{p.name}'>{esc(p.stem[len('report_'):])}</a></li>" for p in v) + "</ul>"
                    for k, v in sorted(groups.items()))
    devl = "".join(f"<li><a href='runs/{esc(d)}/'>{esc(d)}</a></li>" for d in dev)
    legend = """
<details><summary>What the files are</summary><ul class='tight'>
<li><b>results/runs/&lt;run&gt;/report/index.html</b>: this overview for one run (round by round).</li>
<li><b>results/runs/&lt;run&gt;/report/transcript.md</b>: the full story: every planner and critic answer in order.</li>
<li><b>results/runs/&lt;run&gt;/summary.json</b>: the run's best job and layout; <b>trace.md</b>: one-line-per-round table.</li>
<li><b>results/runs/&lt;run&gt;/calls/rNN_planner_0/output.json</b>, <b>rNN_critic_0/output.json</b>: the agents' answers
 (prompt_0.md, response_0.json, schema.json, system.md are the raw inputs/outputs; checkpoints.sqlite and trace.json are
 machine state).</li>
<li><b>results/&lt;32-hex job id&gt;/</b>: one COMSOL solve each. <b>plots/summary.png</b> is the one-page overview;
 trajectories, r_theta, dtheta, fates, field_map, axis_potential, landing are the details; metrics.json the numbers,
 job.json the voltages and positions.</li>
<li><b>results/report_&lt;study&gt;.html</b>: every run of one optimizer study (one round), sortable.</li>
<li><b>results/best/</b>: copies of each run's best figures with readable names.</li>
<li><b>logs/&lt;run&gt;-goal.txt</b>: the goal written for the run.</li></ul></details>"""
    page = (f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
            f"<title>Agent runs</title>{CSS}</head><body><h1>Agent runs</h1>"
            "<p class='sub'>Score = worst-case angular resolution dθ over the accepted cone (lower is better); η = "
            "fraction of the emitted beam collected on the active MCP. Newest first; click a column to sort. "
            "<a href='best/README.md'>Best figures of every run</a>.</p>"
            f"{legend}<table><thead><tr>{th}</tr></thead><tbody>{''.join(rows)}</tbody></table>"
            f"<h2>Baselines and other studies</h2>{other}"
            f"<h2>Development and demo runs</h2><details><summary>{len(dev)} runs</summary><ul class='tight'>{devl}"
            f"</ul></details>{SORT_JS}</body></html>")
    f = results / "index.html"
    f.write_text(page, encoding="utf-8")
    return f


# --------------------------------------------------------------------------- main


def build(run_ids: list[str] | None = None, study_reports: bool = False) -> list[Path]:
    base = load_config()
    results = base.path("results_dir")
    con = sqlite3.connect(str(base.path("db_path")))
    known = [r[0] for r in con.execute("select run_id from agent_runs order by started_at")]
    folders = sorted(p.name for p in (results / "runs").iterdir() if p.is_dir()) if (results / "runs").is_dir() else []
    real_ids = [r for r in known if is_real(r)]
    dev = [r for r in dict.fromkeys(known + folders) if not is_real(r)]
    written = []
    all_runs = []
    for rid in real_ids:
        run = load_run(con, results, rid)
        all_runs.append(run)
        if run_ids and rid not in run_ids:
            continue
        rcfg = run_config(base, run["dir"])
        if study_reports:
            from ionopt.baseline import study_report
            for r in run["rounds"]:
                sid = r["study_id"]
                if sid and sid != "None" and not (results / f"report_{sid}.html").is_file():
                    p = study_report(rcfg, sid)
                    if p:
                        print(f"  written: {p}")
        written.append(run_page(run, results, rcfg.spec.requirements.eta_min))
        print(f"written: {written[-1]}")
    written.append(best_gallery(all_runs, results))
    written.append(index_page(all_runs, dev, results))
    print(f"written: {written[-2]}\nwritten: {written[-1]}")
    return written


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--runs", nargs="*", default=None, help="only rebuild these runs' pages (index always rebuilt)")
    ap.add_argument("--study-reports", action="store_true",
                    help="also build results/report_<study>.html for rounds that have none")
    a = ap.parse_args()
    build(a.runs, a.study_reports)
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
