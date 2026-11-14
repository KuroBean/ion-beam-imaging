"""Browsable index of runs: one static HTML page per selection of result folders.

Each row: the run's summary figure (plots/summary.png, made if missing), the headline numbers
(MCP fraction, collected fraction, score, monotonic, spot size), the voltages and positions, and
flags. Click a column header to sort. For an optimization study the page also shows the score and
transmission per trial (plots/history.png in the study's report folder).

The page links to the figures by relative path, so it lives in results/ next to the run folders
and can be opened straight from disk.
"""
from __future__ import annotations

import html
import json
import math
from pathlib import Path

from .config import Config
from .schemas import FILES
from .utils import read_json

SORT_JS = """
<script>
document.querySelectorAll('th[data-k]').forEach((th, i) => th.addEventListener('click', () => {
  const tb = th.closest('table').tBodies[0], rows = [...tb.rows], dir = th.dataset.dir === 'asc' ? -1 : 1;
  th.dataset.dir = dir === 1 ? 'asc' : 'desc';
  const v = r => { const c = r.cells[th.cellIndex].dataset.v; const n = parseFloat(c); return isNaN(n) ? c : n; };
  rows.sort((a, b) => { const x = v(a), y = v(b); return (x > y ? 1 : x < y ? -1 : 0) * dir; });
  rows.forEach(r => tb.appendChild(r));
}));
</script>
"""

CSS = """
<style>
:root { --bg:#fcfcfb; --ink:#0b0b0b; --ink2:#52514e; --muted:#898781; --grid:#e1e0d9; --bad:#b3261e; --ok:#1c5cab; }
body { background:var(--bg); color:var(--ink); font:14px/1.4 system-ui, sans-serif; margin:16px; }
h1 { font-size:20px; margin:0 0 4px; } .sub { color:var(--ink2); margin:0 0 14px; }
table { border-collapse:collapse; width:100%; } th, td { border-bottom:1px solid var(--grid); padding:6px 8px;
  text-align:left; vertical-align:top; } th { cursor:pointer; color:var(--ink2); font-weight:600; position:sticky; top:0;
  background:var(--bg); } th:hover { color:var(--ink); }
td.num { font-variant-numeric:tabular-nums; text-align:right; white-space:nowrap; }
td.small { font-size:12px; color:var(--ink2); } img.thumb { width:340px; border:1px solid var(--grid); }
.bad { color:var(--bad); } .ok { color:var(--ok); } .mono { font-family:ui-monospace, monospace; font-size:12px; }
.history { max-width:900px; width:100%; border:1px solid var(--grid); margin-bottom:14px; }
</style>
"""


def _fmt(v, f="{:.3g}"):
    if v is None or (isinstance(v, float) and not math.isfinite(v)):
        return "–", ""
    return f.format(v), v


def collect_runs(results_dir: Path, study: str | None = None, purpose: str | None = None,
                 last: int | None = None) -> list[Path]:
    """Result folders with metrics.json, newest first, optionally filtered by tags."""
    dirs = [d for d in Path(results_dir).iterdir() if d.is_dir() and (d / FILES["metrics"]).is_file()
            and (d / FILES["job"]).is_file()]
    dirs.sort(key=lambda d: (d / FILES["metrics"]).stat().st_mtime, reverse=True)
    out = []
    for d in dirs:
        tags = json.loads((d / FILES["job"]).read_text(encoding="utf-8")).get("tags") or {}
        if study and tags.get("study_id") != study:
            continue
        if purpose and tags.get("purpose") != purpose:
            continue
        out.append(d)
        if last and len(out) >= last:
            break
    return out


def _row(d: Path, cfg: Config, make_missing: bool) -> str:
    from .plots import make_plots

    job = json.loads((d / FILES["job"]).read_text(encoding="utf-8"))
    m = read_json(d / FILES["metrics"])
    summary = d / "plots" / "summary.png"
    if make_missing and not summary.is_file():
        try:
            make_plots(d, cfg)
        except Exception as e:  # noqa: BLE001 - a broken run must not stop the index
            (d / "plots").mkdir(exist_ok=True)
            (d / "plots" / "error.txt").write_text(f"{type(e).__name__}: {e}", encoding="utf-8")
    f = m.get("fates") or {}
    mp = m.get("mapping") or {}
    sp = m.get("spot") or {}
    tags = job.get("tags") or {}
    rel = f"{d.name}/plots/summary.png"
    img = f'<a href="{rel}"><img class="thumb" src="{rel}" loading="lazy"></a>' if summary.is_file() else "no figure"
    cells = [f"<td>{img}</td>"]

    def num(v, f="{:.3g}", cls="num"):
        s, k = _fmt(v, f)
        cells.append(f'<td class="{cls}" data-v="{k}">{s}</td>')

    created = (read_json(d / FILES["meta"]).get("finished_at") or "")[:19] if (d / FILES["meta"]).is_file() else ""
    who = " ".join(f"{k}={html.escape(str(v))}" for k, v in tags.items() if k in ("study_id", "trial", "purpose", "setting"))
    cells.append(f'<td class="small" data-v="{created}"><span class="mono">{d.name[:12]}</span><br>{created}<br>'
                 f'{job.get("fidelity", "").upper()} cfg {job.get("cfg")}<br>{who}</td>')
    num(f.get("mcp_active"), "{:.1%}")
    num((m.get("requirements") or {}).get("eta"), "{:.1%}")
    num(m.get("score"), "{:.3g}°")
    mono = mp.get("monotonic")
    cells.append(f'<td data-v="{int(bool(mono))}" class="{"ok" if mono else "bad"}">{"yes" if mono else "no"}'
                 f'<br><span class="small">0–{mp.get("eval_theta_max_deg")}°</span></td>')
    num(sp.get("rms_axis_mm"), "{:.2f} mm")
    ch = job.get("channels") or {}
    wiring = job.get("wiring") or {}
    volts = "<br>".join(f"{k} {v:+.0f}" for k, v in ch.items())
    wires = " ".join(f"{k}:{v}" for k, v in wiring.items())
    pos = "<br>".join(f"{k} {v * 1e3:.1f}" for k, v in (job.get("positions") or {}).items())
    cells.append(f'<td class="small mono" data-v="{ch.get("LV1", 0)}">{volts}<br><br>{html.escape(wires)}</td>')
    cells.append(f'<td class="small mono">{pos}</td>')
    valid, feas = m.get("valid"), m.get("feasible")
    flags = "<br>".join(html.escape(x) for x in (m.get("flags") or [])[:4])
    cells.append(f'<td class="small" data-v="{int(bool(valid)) + int(bool(feas))}">'
                 f'<span class="{"ok" if valid else "bad"}">valid {valid}</span><br>'
                 f'<span class="{"ok" if feas else "bad"}">feasible {feas}</span><br>{flags}</td>')
    return "<tr>" + "".join(cells) + "</tr>"


def build_report(cfg: Config, dirs: list[Path], out_html: Path, title: str, subtitle: str = "",
                 history_png: Path | None = None, make_missing: bool = True) -> Path:
    head = ["", "run", "MCP", "collected", "score (worst dθ)", "monotonic", "spot rms", "voltages (V) and wiring",
            "positions (mm)", "status"]
    th = "".join(f'<th data-k="{i}">{h}</th>' if h else "<th></th>" for i, h in enumerate(head))
    rows = "\n".join(_row(d, cfg, make_missing) for d in dirs)
    hist = ""
    if history_png is not None and history_png.is_file():
        rel = history_png.relative_to(out_html.parent).as_posix()
        hist = f'<img class="history" src="{rel}">'
    page = (f"<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
            f"<title>{html.escape(title)}</title>{CSS}</head><body><h1>{html.escape(title)}</h1>"
            f"<p class='sub'>{html.escape(subtitle)} {len(dirs)} runs. Click a column to sort; click a figure to open it."
            f"</p>{hist}<table><thead><tr>{th}</tr></thead><tbody>{rows}</tbody></table>{SORT_JS}</body></html>")
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(page, encoding="utf-8")
    return out_html


def study_history(cfg: Config, dirs: list[Path], out_png: Path, study: str) -> Path:
    from .plots import plot_study_history

    rows = []
    for d in dirs:
        job = json.loads((d / FILES["job"]).read_text(encoding="utf-8"))
        m = read_json(d / FILES["metrics"])
        tr = (job.get("tags") or {}).get("trial")
        if tr is None:
            continue
        rows.append({"trial": int(tr), "score": m.get("score"), "mcp": (m.get("fates") or {}).get("mcp_active"),
                     "feasible": m.get("feasible"), "valid": m.get("valid")})
    return plot_study_history(rows, out_png, f"Study {study}", cfg.optimizer.nonevaluable_score_deg)
