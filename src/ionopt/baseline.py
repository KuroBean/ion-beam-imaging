"""Baseline B0 (plan 9.10): the optimizer alone over a fixed list of configurations.

For each configuration in config/b0_configs.yaml (or the subset given), one 2D optimization study
with the same budget (optimize.optimize). Studies resume from the Optuna storage, so an
interrupted baseline can simply be started again. Afterwards:
  * results/report_<study_id>.html for every study (summary figure per trial + score history),
  * results/b0_<tag>.json and results/report_b0_<tag>.html comparing the configurations.

Promotion (plan 9.10) reruns the top-k feasible 2D results of a study in 3D with the same
parameters; it is off unless asked for (3D is impractical on the current machine).
"""
from __future__ import annotations

import json
import math
import time
from pathlib import Path

from .config import Config
from .optimize import StudyResult, optimize


def _study_dirs(cfg: Config, study_id: str) -> list[Path]:
    from .report import collect_runs
    return collect_runs(cfg.path("results_dir"), study=study_id)


def study_report(cfg: Config, study_id: str) -> Path | None:
    from .report import build_report, study_history

    res = cfg.path("results_dir")
    dirs = _study_dirs(cfg, study_id)
    if not dirs:
        return None
    dirs.sort(key=lambda d: _rank_key(d))
    hist = study_history(cfg, dirs, res / f"report_{study_id}_history.png", study_id)
    return build_report(cfg, dirs, res / f"report_{study_id}.html", title=f"Study {study_id}",
                        subtitle="Sorted: feasible runs first, then by score.", history_png=hist)


def _rank_key(d: Path):
    m = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
    s = m.get("score")
    return (not m.get("feasible"), s if s is not None and math.isfinite(s) else 1e9)


def _best_metrics(cfg: Config, job_id: str | None) -> dict:
    if not job_id:
        return {}
    f = cfg.path("results_dir") / job_id / "metrics.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def run_baseline(cfg: Config, config_ids: list[str] | None = None, budget: int | None = None,
                 tag: str | None = None, backend=None, log=None) -> dict:
    """Run (or resume) one 2D study per configuration; write the comparison and the reports."""
    from .backends import make_backend

    log = log or (lambda m: print(m, flush=True))
    ids = config_ids or [c.config_id for c in cfg.b0_configs.configurations]
    tag = tag or f"seed{cfg.optimizer.seed}"
    own_backend = backend is None
    backend = backend or make_backend(cfg)
    rows = []
    try:
        for cid in ids:
            t0 = time.time()
            log(f"== {cid}: {cfg.b0_configs.get(cid).description}")

            def progress(n, m, cid=cid):
                s = f"{m.score:.3g}" if m.score is not None and math.isfinite(m.score) else "n/a"
                log(f"  [{cid} {n}] valid={m.valid} feasible={m.feasible} score={s} "
                    f"mcp={m.fates.get('mcp_active', 0):.2f}")

            r: StudyResult = optimize(cfg, cid, budget, "2d", backend=backend,
                                      study_id=f"b0-{cid}-2d-{tag}", on_trial=progress)
            rep = study_report(cfg, r.study_id)
            bm = _best_metrics(cfg, r.best_job_id)
            rows.append({
                "config_id": cid, "study_id": r.study_id, "sampler": r.sampler, "n_trials": r.n_trials,
                "n_failed": r.n_failed, "n_feasible": r.n_feasible, "best_job_id": r.best_job_id,
                "best_score_deg": r.best_score, "best_mcp": (bm.get("fates") or {}).get("mcp_active"),
                "best_eta": (bm.get("requirements") or {}).get("eta"),
                "best_channels": r.best_channels,
                "best_positions_mm": {k: v * 1e3 for k, v in (r.best_positions or {}).items()} or None,
                "report": str(rep) if rep else None, "wall_time_s": round(time.time() - t0)})
            log(f"   best {r.best_job_id} score {r.best_score} ({r.n_feasible}/{r.n_trials} feasible)")
    finally:
        if own_backend and hasattr(backend, "close"):
            backend.close()
    out = {"tag": tag, "budget": budget or cfg.optimizer.default_budget, "studies": rows}
    res = cfg.path("results_dir")
    (res / f"b0_{tag}.json").write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    best_dirs = [res / r["best_job_id"] for r in rows if r["best_job_id"]]
    if best_dirs:
        from .report import build_report
        best_dirs.sort(key=_rank_key)
        build_report(cfg, best_dirs, res / f"report_b0_{tag}.html", title=f"Baseline B0 ({tag})",
                     subtitle="Best feasible run of each configuration.")
    log(f"wrote {res / f'b0_{tag}.json'}")
    return out


def promote(cfg: Config, study_id: str, top_k: int = 3, backend=None, log=None) -> list[dict]:
    """Rerun the top-k feasible 2D runs of a study in 3D (same channels, wiring, positions, launch)."""
    from .backends import make_backend
    from .checker import check
    from .results import load_job
    from .runlog import RunLog
    from .schemas import new_job_id

    log = log or (lambda m: print(m, flush=True))
    dirs = [d for d in _study_dirs(cfg, study_id)
            if json.loads((d / "metrics.json").read_text(encoding="utf-8")).get("feasible")]
    dirs.sort(key=_rank_key)
    backend = backend or make_backend(cfg)
    out = []
    with RunLog(cfg.path("db_path")) as rl:
        for d in dirs[:top_k]:
            j2 = load_job(d)
            j3 = j2.model_copy(update={"job_id": new_job_id(), "fidelity": "3d",
                                       "tags": {**(j2.tags or {}), "purpose": "promotion", "from_2d": j2.job_id}})
            b = backend.run(j3)
            rl.record_job(j3, b, cfg.config_hash(), backend=getattr(backend, "name", None))
            m2 = json.loads((d / "metrics.json").read_text(encoding="utf-8"))
            m3 = check(b.result_dir, cfg) if b.status == "success" else None
            if m3 is not None:
                rl.record_metrics(m3)
            rl.record_promotion(j2.job_id, j3.job_id, m2.get("score"), m3.score if m3 else None,
                                (m2.get("requirements") or {}).get("eta"), m3.requirements.get("eta") if m3 else None)
            out.append({"job_2d": j2.job_id, "job_3d": j3.job_id, "status": b.status,
                        "score_2d": m2.get("score"), "score_3d": m3.score if m3 else None})
            log(f"promoted {j2.job_id} -> {j3.job_id}: {b.status}")
    return out
