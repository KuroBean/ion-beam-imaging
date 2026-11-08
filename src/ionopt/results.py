"""Result folders: preparing job inputs, executing a runner, reading bundles (plan 9.2).

A *runner* is any callable ``runner(job, cfg, out_dir) -> dict`` that writes the raw
files into out_dir and returns extra metadata (e.g. mesh element count, COMSOL
version). :func:`execute` wraps it with timing, error capture and meta.json, so the mock
backend, the queue worker and the COMSOL worker all behave the same way.
"""
from __future__ import annotations

import json
import time
import traceback
from pathlib import Path
from typing import Any, Callable

from .config import Config, load_snapshot, write_snapshot
from .schemas import FILES, JobSpec, ResultBundle, RunMeta
from .utils import git_commit, hostname, now_iso, read_json, write_json

Runner = Callable[[JobSpec, Config, Path], dict]


class JobTimeout(Exception):
    """Raised by a runner when a job exceeds its time limit."""


def prepare_job_dir(job: JobSpec, cfg: Config, out_dir: Path) -> Path:
    """Write job.json and config_snapshot.yaml into out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / FILES["job"]).write_text(job.model_dump_json(indent=2), encoding="utf-8")
    write_snapshot(cfg, out_dir / FILES["config_snapshot"])
    return out_dir


def load_job(job_dir: Path) -> JobSpec:
    return JobSpec.model_validate_json((job_dir / FILES["job"]).read_text(encoding="utf-8"))


def load_job_config(job_dir: Path, root_dir: Path | None = None) -> Config:
    return load_snapshot(job_dir / FILES["config_snapshot"], root_dir=root_dir)


def execute(job: JobSpec, cfg: Config, out_dir: Path, runner: Runner, backend: str) -> RunMeta:
    """Run one job with error capture; always writes meta.json and returns it."""
    started = now_iso()
    t0 = time.time()
    status, error, extra = "success", None, {}
    try:
        extra = runner(job, cfg, out_dir) or {}
    except JobTimeout as e:
        status, error = "timeout", f"timeout: {e}"
    except Exception as e:  # noqa: BLE001 - every failure must be recorded, never raised past the worker
        status, error = "failed", f"{type(e).__name__}: {e}"
        (out_dir / "error.txt").write_text(traceback.format_exc(), encoding="utf-8")
    meta = RunMeta(job_id=job.job_id, status=status, error=error, backend=backend, worker_host=hostname(),
                   git_commit=git_commit(cfg.root_dir), config_hash=cfg.config_hash(), started_at=started,
                   finished_at=now_iso(), solve_time_s=round(time.time() - t0, 3), **extra)
    write_json(out_dir / FILES["meta"], meta.model_dump())
    return meta


def read_bundle(job_dir: Path) -> ResultBundle:
    """ResultBundle describing the files present in a result folder."""
    files = {k: str(job_dir / f) for k, f in FILES.items() if (job_dir / f).is_file()}
    meta = None
    if (job_dir / FILES["meta"]).is_file():
        try:
            meta = RunMeta.model_validate(read_json(job_dir / FILES["meta"]))
        except (json.JSONDecodeError, ValueError) as e:
            return ResultBundle(job_id=job_dir.name, status="failed", error=f"unreadable meta.json: {e}",
                                result_dir=str(job_dir), files=files)
    if meta is None:
        return ResultBundle(job_id=job_dir.name, status="failed", error="meta.json missing",
                            result_dir=str(job_dir), files=files)
    return ResultBundle(job_id=meta.job_id, status=meta.status, error=meta.error, result_dir=str(job_dir),
                        files=files, meta=meta)


def write_status_meta(job: JobSpec, out_dir: Path, status: str, error: str, backend: str,
                      **extra: Any) -> RunMeta:
    """meta.json for a job that never produced one (e.g. backend-side timeout)."""
    meta = RunMeta(job_id=job.job_id, status=status, error=error, backend=backend, finished_at=now_iso(), **extra)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / FILES["meta"], meta.model_dump())
    return meta
