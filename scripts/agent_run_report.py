"""Report material for one agent run: a readable transcript and variant-variable scatter plots.

    python scripts/agent_run_report.py demo-1 [--overrides config/dev_overrides.yaml]

Writes results/runs/<run_id>/report/:
  transcript.md          every agent call in order (inputs the agent was given, its JSON answer in words),
                         the author's interventions, each round's study and best-run summary plot
  fig_<variable>.png     score and collection efficiency of every real (non-mock) run of the agent's
                         studies against each swept variant variable (one per variable)
Reads only: the run log (results/runlog.sqlite), the call folders, the variant manifests, job folders.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from ionopt.agents.cli_agents import trace  # noqa: E402
from ionopt.config import load_config  # noqa: E402

# dataviz reference palette (light): categorical slots in fixed order, ink, gridline, surface
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, INK2, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#fcfcfb"


# --------------------------------------------------------------------------- data


def load_json(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def section(md: str, title: str) -> str | None:
    """Body of the '# <title>...' section of a prompt (up to the next top-level heading)."""
    m = re.search(rf"^# {re.escape(title)}[^\n]*\n(.*?)(?=^# |\Z)", md, flags=re.S | re.M)
    return m.group(1).strip() if m else None


def study_jobs(con: sqlite3.Connection, study_id: str, spec_hash: str) -> list[dict]:
    rows = con.execute(
        "select j.job_id, j.backend, j.config_json, m.valid, m.feasible, m.score, m.eta, m.spec_hash "
        "from jobs j left join metrics m on m.job_id = j.job_id where j.study_id = ?", (study_id,)).fetchall()
    best: dict[str, dict] = {}
    for jid, backend, cj, valid, feas, score, eta, sh in rows:
        if jid in best and best[jid]["spec_hash"] == spec_hash:
            continue                                      # keep the metrics of the current spec
        best[jid] = {"job_id": jid, "backend": backend, "config": json.loads(cj or "{}"), "valid": valid,
                     "feasible": feas, "score": score, "eta": eta, "spec_hash": sh}
    return list(best.values())


def b0_reference(con: sqlite3.Connection, spec_hash: str) -> tuple[float, str, str] | None:
    """Best feasible B0 run under the current spec: (score, config_id, job_id)."""
    r = con.execute(
        "select m.score, j.config_id, j.job_id from metrics m join jobs j on j.job_id = m.job_id "
        "where j.study_id like 'b0-%' and m.feasible = 1 and m.spec_hash = ? and j.backend = 'comsol' "
        "order by m.score limit 1", (spec_hash,)).fetchone()
    return (r[0], r[1], r[2]) if r else None


# --------------------------------------------------------------------------- figure


def variant_figure(out: Path, var: dict, points: list[dict], rounds: dict[int, dict], b0, eta_min: float | None,
                   run_id: str) -> Path:
    """Two stacked panels sharing x (no dual axis): worst-case dtheta and eta against one variant variable."""
    name, as_built = var["name"], var["as_built"]
    plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "font.family": "DejaVu Sans"})
    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True, figsize=(7.2, 6.4), facecolor=SURFACE,
                                   gridspec_kw={"height_ratios": [1.25, 1], "hspace": 0.08})
    rnds = sorted({p["round"] for p in points})
    for ax in (ax1, ax2):
        ax.set_facecolor(SURFACE)
        ax.grid(True, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.axvline(as_built, color=MUTED, linewidth=1.2, linestyle=(0, (4, 3)), zorder=1)
    scores = [p["score"] for p in points if p["score"] is not None and p["score"] > 0]
    bests: list[str] = []
    for i, rnd in enumerate(rnds):
        col = SERIES[i]
        pts = [p for p in points if p["round"] == rnd]
        for feas in (True, False):
            sel = [p for p in pts if bool(p["feasible"]) == feas]
            if not sel:
                continue
            kw = dict(s=52, linewidths=1.6 if not feas else 0.8, zorder=3,
                      facecolors=col if feas else "none", edgecolors=col if not feas else SURFACE)
            lab = f"round {rnd}, " + ("feasible" if feas else "infeasible")
            sc = [p for p in sel if p["score"] is not None and p["score"] > 0]
            ax1.scatter([p["x"] for p in sc], [p["score"] for p in sc], label=lab, **kw)
            ax2.scatter([p["x"] for p in sel], [p["eta"] for p in sel], **kw)
        best = rounds.get(rnd, {}).get("best_job_id")
        bp = next((p for p in pts if p["job_id"] == best), None)
        if bp is not None and bp["score"] is not None:
            for ax, y in ((ax1, bp["score"]), (ax2, bp["eta"])):
                ax.scatter([bp["x"]], [y], s=190, facecolors="none", edgecolors=INK, linewidths=1.1, zorder=4)
            bests.append(f"r{rnd} {bp['score']:.2f}° at {bp['x']:.1f} mm")
    ax1.set_yscale("log")
    lo = min(scores + ([b0[0]] if b0 else [])) / 1.8
    ax1.set_ylim(lo, max(scores) * 1.8)
    if b0 is not None:
        ax1.axhline(b0[0], color=INK2, linewidth=1.2, zorder=2,
                    label=f"B0 best on the as-built mesh: {b0[0]:.2f}° ({b0[1]})")
    if eta_min is not None:
        ax2.axhline(eta_min, color=INK2, linewidth=1.2, zorder=2)
        ax2.annotate(f"eta_min {eta_min:g}", (1.0, eta_min), xycoords=("axes fraction", "data"), xytext=(0, 4),
                     textcoords="offset points", ha="right", va="bottom", fontsize=8.5, color=INK2)
    ax1.annotate(f"as built {as_built:g} mm", (as_built, 1.0), xycoords=("data", "axes fraction"), xytext=(4, -12),
                 textcoords="offset points", fontsize=8.5, color=MUTED)
    ax1.set_ylabel("worst-case dθ (deg, log; lower is better)")
    ax2.set_ylabel("collection efficiency η")
    ax2.set_ylim(0, 1.0)
    ax2.set_xlabel(f"{name} (mm)   [variant {var['variant_id']}, inventory item {var['inventory_item']}]")
    h, l = ax1.get_legend_handles_labels()
    if bests:
        h.append(Line2D([], [], linestyle="none", marker="o", markersize=12, markerfacecolor="none",
                        markeredgecolor=INK, markeredgewidth=1.1))
        l.append("round best: " + "; ".join(bests))
    fig.legend(h, l, loc="lower center", bbox_to_anchor=(0.5, -0.075), ncol=2,
               frameon=False, fontsize=8.5, labelcolor=INK2, handletextpad=0.3, columnspacing=1.4)
    ax1.set_title(f"Agent run {run_id}: every COMSOL run of the variant studies (filled = feasible, "
                  "ringed = round best)", loc="left", fontsize=10, color=INK)
    f = out / f"fig_{name}.png"
    fig.savefig(f, dpi=200, bbox_inches="tight", facecolor=SURFACE)
    plt.close(fig)
    return f


# --------------------------------------------------------------------------- transcript


def fmt_bounds(b: dict | None) -> str:
    if not b:
        return "(none: full usable ranges)"
    return ", ".join(f"{k} [{v['lo']:g}, {v['hi']:g}]" for k, v in b.items())


def fmt_conf(c: dict | None) -> str:
    if not c:
        return "-"
    w = ", ".join(f"{k}:{v}" for k, v in sorted(c.get("wiring", {}).items()))
    bits = [f"cfg {c.get('cfg')}", f"wiring [{w}]", f"variant {c.get('variant_id', 'base')}"]
    if c.get("removed"):
        bits.append(f"removed {c['removed']}")
    if c.get("moved"):
        bits.append(f"moved {c['moved']}")
    return "; ".join(bits)


def quote(text: str) -> str:
    return "\n".join("> " + ln if ln else ">" for ln in text.strip().splitlines())


def planner_md(cdir: Path, first: bool) -> list[str]:
    o = load_json(cdir / "output.json")
    prompt = (cdir / "prompt_0.md").read_text(encoding="utf-8")
    out = []
    if first:
        out += ["**Input** (the full prompt the planner received; role instructions in "
                f"`{cdir.name}/system.md`):", "", "```markdown", prompt.strip(), "```", ""]
    else:
        fb = section(prompt, "Feedback on your previous proposal")
        if fb:
            out += ["**What the planner was told before this call:**", "", quote(fb), ""]
    out += [f"**Decision:** `{o['action']}`" + (f", diagnosis `{o['diagnosis']}`" if o.get("diagnosis") else ""), ""]
    if o.get("diagnosis_evidence"):
        out += ["*Evidence:*", "", quote(o["diagnosis_evidence"]), ""]
    if o.get("configuration"):
        out += [f"- configuration: {fmt_conf(o['configuration'])}", f"- bounds: {fmt_bounds(o.get('bounds'))}",
                f"- solve budget: {o.get('solve_budget')}"]
    if o.get("edit_request"):
        e = o["edit_request"]
        out += [f"- edit request: items {e['inventory_items']}", "", quote(e["description"]), "",
                "  *reason:* " + e.get("reason", "")]
    if o.get("escalation"):
        out += ["", "*Question to the author:*", "", quote(o["escalation"])]
    if o.get("claims"):
        out += ["", "*Claims for the critic to check:*", ""]
        out += [f"{i}. **{c['id']}**: {c['statement']} *(evidence: {c['evidence_needed']})*"
                for i, c in enumerate(o["claims"], 1)]
    out += ["", "*Rationale:*", "", quote(o.get("rationale", "")), ""]
    return out


def editor_md(cfg, cdir: Path, run_dir: Path) -> list[str]:
    o = load_json(cdir / "output.json")
    res_f = next(run_dir.glob("edits/*/edit_result.json"), None)
    res = load_json(res_f) if res_f else {}
    out = ["**Request** (from the planner): see the round's planner decision above; the editor gets it with the "
           f"build script, its parent copy and API notes (`{cdir.name}/prompt_0.md`).", "",
           "**Editor's report:**", "", quote(o.get("summary", "")), ""]
    for p in o.get("parameters", []):
        out.append(f"- new parameter `{p['comsol_name']}` = optimizer variable **{p['name']}** "
                   f"({p['role']}, as built {p['as_built']:g} mm, inventory {p['inventory_item']}.{p['inventory_param']})")
    if o.get("notes"):
        out += ["", "*Notes for the author:*", "", quote(o["notes"])]
    vid = res.get("variant_id")
    if vid:
        vdir = cfg.path("results_dir") / "variants" / vid
        man = load_json(vdir / "variant.json")
        ch = {k: v for k, v in man["checks"].items() if isinstance(v, bool)}
        eq = json.loads(man["checks"].get("equivalence_detail") or "{}")
        out += ["", f"**Automatic checks on variant `{vid}`:** " + ", ".join(f"{k} {'pass' if v else 'FAIL'}"
                                                                            for k, v in ch.items())]
        if eq:
            out.append(f"(equivalence at the as-built value vs a stored parent run: {eq.get('n_ions')} ions, "
                       f"max dr {eq.get('max_dr_um')} µm, max dKE {eq.get('max_dKE_eV')} eV)")
        diff = vdir / "edit.diff"
        if diff.is_file():
            out += ["", "**The code change** (`edit.diff`):", "", "```diff", diff.read_text(encoding="utf-8").strip(),
                    "```"]
        out += ["", f"**Author:** {'approved' if man.get('approved') else 'did not approve'} the variant"
                + (f" ({man['approved_at']})" if man.get("approved_at") else "") + "."]
    return out + [""]


def critic_md(cdir: Path) -> list[str]:
    o = load_json(cdir / "output.json")
    out = [f"**Verdict: {o['verdict'].upper()}**", "", quote(o.get("reasons", "")), ""]
    if o.get("claim_checks"):
        out += ["| claim | status | evidence |", "|---|---|---|"]
        out += [f"| {c['claim_id']} | {c['status']} | {c['evidence'].replace('|', '/').replace(chr(10), ' ')} |"
                for c in o["claim_checks"]]
        out.append("")
    if o.get("observed_failure_modes"):
        out += ["*Failure modes observed:*", ""] + [f"- {x}" for x in o["observed_failure_modes"]] + [""]
    if o.get("suggestions"):
        out += ["*Suggestions (non-binding):*", ""] + [f"- {x}" for x in o["suggestions"]] + [""]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("run_id")
    ap.add_argument("--overrides", action="append", default=[], help="config override files (as the run used)")
    ap.add_argument("--set", action="append", default=[])
    a = ap.parse_args()

    cfg = load_config(None, a.set, a.overrides)
    run_dir = cfg.path("results_dir") / "runs" / a.run_id
    out = run_dir / "report"
    out.mkdir(parents=True, exist_ok=True)
    spec_hash = cfg.spec_hash()
    con = sqlite3.connect(str(cfg.path("db_path")))
    con.row_factory = None
    _, trace_md = trace(cfg, a.run_id)

    rounds = {r[0]: {"study_id": r[1], "n_solves": r[2], "best_job_id": r[3], "score": r[4], "eta": r[5],
                     "feasible": r[6], "critic": r[7], "counted": r[8]}
              for r in con.execute("select round, study_id, n_solves, best_job_id, score, eta, feasible, "
                                   "critic_verdict, counted from agent_rounds where run_id = ?", (a.run_id,))}
    calls = con.execute("select call_id, role, round, cost_usd, duration_s, created_at from agent_calls "
                        "where run_id = ? order by created_at", (a.run_id,)).fetchall()
    run = con.execute("select assumptions_json from agent_runs where run_id = ?", (a.run_id,)).fetchone()
    summary = load_json(run_dir / "summary.json") if (run_dir / "summary.json").is_file() else {}
    goal = next((x.split(": ", 1)[1] for x in summary.get("assumptions", json.loads(run[0] or "[]") if run else [])
                 if x.startswith("author goal")), None)

    # ---- figure(s): every job of the run's studies on a real backend, per variant variable
    eta_min = cfg.spec.requirements.eta_min
    b0 = b0_reference(con, spec_hash)
    figs = []
    jobs = []
    for rnd, r in rounds.items():
        if r["study_id"] and r["study_id"] != "None":
            for j in study_jobs(con, r["study_id"], spec_hash):
                j["round"] = rnd
                jobs.append(j)
    for j in jobs:                                        # the run log's config_json has no variant id: use job.json
        jf = cfg.path("results_dir") / j["job_id"] / "job.json"
        if jf.is_file():
            jd = load_json(jf)
            j["config"] = {**j["config"], "variant_id": jd.get("variant_id"), "positions": jd.get("positions", {})}
    real = [j for j in jobs if j["backend"] != "mock" and j["valid"]]
    variants = {j["config"].get("variant_id") for j in real} - {None, "base"}
    for vid in sorted(variants):
        man = load_json(cfg.path("results_dir") / "variants" / vid / "variant.json")
        for p in man["parameters"]:
            if p["role"] != "variable":
                continue
            pts = [{**j, "x": j["config"]["positions"][p["name"]] * 1e3} for j in real
                   if j["config"].get("variant_id") == vid and p["name"] in j["config"].get("positions", {})]
            if pts:
                figs.append(variant_figure(out, {**p, "variant_id": vid}, pts, rounds, b0, eta_min, a.run_id))

    # ---- transcript
    md = [f"# Agent run `{a.run_id}`: transcript", ""]
    if goal:
        md += ["**Author's goal** (shown to the planner every round):", "", quote(goal), ""]
    md += ["Generated by `scripts/agent_run_report.py` from the run log and call folders. Paths are relative to "
           "this file; call folders are under `../calls/`.", "", "## Overview", "",
           trace_md.split("\n", 2)[2].strip(), ""]
    for f in figs:
        md += [f"![{f.stem}]({f.name})", ""]
    if b0:
        md += [f"Reference: best B0 baseline under the current spec, {b0[0]:.3f}° ({b0[1]}, job `{b0[2]}`), "
               f"[summary plot](../../../{b0[2]}/plots/summary.png).", ""]

    planner_seen = False
    cur_round = None
    for call_id, role, rnd, cost, dur, created in calls:
        cdir = run_dir / "calls" / call_id.split("/", 1)[1]
        if rnd != cur_round:
            cur_round = rnd
            md += [f"## Round {rnd}", ""]
        md += [f"### {role.capitalize()} (`{cdir.name}`, {dur:.0f} s, ${cost or 0:.3f}, {created})", ""]
        if role == "planner":
            md += planner_md(cdir, first=not planner_seen)
            planner_seen = True
        elif role == "editor":
            md += editor_md(cfg, cdir, run_dir)
        elif role == "critic":
            r = rounds.get(rnd, {})
            backends = sorted({j["backend"] for j in jobs if j["round"] == rnd})
            sid, best = r.get("study_id"), r.get("best_job_id")
            md += [f"**Study `{sid}`:** {r.get('n_solves')} solves on backend {', '.join(backends) or '-'}; best "
                   f"job `{best}`: score {r.get('score') or float('nan'):.3f}°, eta {r.get('eta') or float('nan'):.3f}, "
                   f"{'feasible' if r.get('feasible') else 'not feasible'}"
                   + ("" if r.get("counted") else "; **excluded** (critic rejected it)") + ".", ""]
            if best and (cfg.path("results_dir") / best / "plots" / "summary.png").is_file():
                md += [f"![round {rnd} best](../../../{best}/plots/summary.png)", "",
                       f"Plots the critic could open: `results/{best}/plots/` (trajectories, field map, r(θ), dθ(θ), "
                       "fates, axis potential, landing, summary).", ""]
            md += critic_md(cdir)
    if summary:
        b = summary.get("best") or {}
        md += ["## End of run", "", f"- stop reason: {summary.get('stop_reason')}; rounds {summary.get('rounds')}; "
               f"solves used {summary.get('solves_used')}",
               f"- best: {b.get('score')}° (eta {b.get('eta')}), job `{b.get('job_id')}`, round {b.get('round')}, "
               f"{fmt_conf(b.get('configuration'))}", ""]
    (out / "transcript.md").write_text("\n".join(md), encoding="utf-8")
    print(f"written: {out / 'transcript.md'}")
    for f in figs:
        print(f"written: {f}")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    raise SystemExit(main())
