"""COMSOL worker (plan 9.5): a persistent process that runs queued jobs with MPh.

One mph client per worker; each base model (2d / 3d, from config/paths.yaml) is loaded once and reused,
because every job sets every registry parameter explicitly. The client is restarted after
backend.worker.restart_after_jobs jobs, and after any job that failed inside COMSOL (its state is
then unknown). Jobs are claimed and filed by QueueWorker, which never leaves a job in running/.

Timeouts are checked between stages (parameters, geometry/mesh, release, es solve, particle solve,
export): a single COMSOL call cannot be interrupted from Python.

Run:  ionopt worker --runner comsol [--max-jobs N] [--stop-when-empty]
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from ..config import Config
from ..electrodes import expand, launch_preaccel, validate_job
from ..launch import make_launch
from ..schemas import JobSpec
from .model_adapter import AdapterError, ModelAdapter

log = logging.getLogger(__name__)


def _mph(cfg: Config):
    """Import mph with the COMSOL-bundled JRE on PATH (COMSOL 5.5 ships Java 8; jpype1 < 1.6)."""
    root = cfg.paths.comsol_root
    if root:
        jre = Path(root) / "java" / "win64" / "jre" / "bin"
        if jre.is_dir() and str(jre) not in os.environ.get("PATH", ""):
            os.environ["PATH"] = str(jre) + os.pathsep + os.environ.get("PATH", "")
    import mph  # noqa: PLC0415
    return mph


class ComsolRunner:
    """Runner (results.Runner protocol): runner(job, cfg, out_dir) -> metadata dict."""

    def __init__(self, cfg: Config, cores: int | None = None):
        self.cfg = cfg
        self.cores = cores
        self.client = None
        self.adapters: dict[str, ModelAdapter] = {}
        self.jobs_since_start = 0
        self.dirty = False

    # ---- client lifecycle
    def _start(self):
        mph = _mph(self.cfg)
        t = time.time()
        self.client = mph.start(cores=self.cores)
        log.info("COMSOL %s started in %.0f s", self.client.version, time.time() - t)
        self.adapters = {}
        self.jobs_since_start = 0
        self.dirty = False

    def restart(self):
        self.close()
        self._start()

    def close(self):
        if self.client is not None:
            try:
                self.client.clear()
            except Exception:  # noqa: BLE001
                pass
            # mph.start() runs a stand-alone in-process client: it cannot be restarted in the same
            # process, so a "restart" clears all models and reloads them.
        self.adapters = {}

    def adapter(self, fidelity: str) -> ModelAdapter:
        if self.client is None:
            self._start()
        if fidelity not in self.adapters:
            a = ModelAdapter(self.client, self.cfg, fidelity)
            a.load()
            self.adapters[fidelity] = a
        return self.adapters[fidelity]

    # ---- one job
    def __call__(self, job: JobSpec, cfg: Config, out_dir: Path) -> dict:
        self.cfg = cfg   # the job's own config snapshot
        if self.dirty or self.jobs_since_start >= cfg.backend.worker.restart_after_jobs:
            log.info("reloading models (dirty=%s, jobs=%d)", self.dirty, self.jobs_since_start)
            self.close()
            self.jobs_since_start = 0
            self.dirty = False
        if job.mesh_level != "normal":
            raise AdapterError(f"mesh_level '{job.mesh_level}' is not implemented in the COMSOL runner yet")
        warnings = validate_job(job, cfg)
        params = expand(job, cfg)
        pre = launch_preaccel(job, cfg)
        ions = make_launch(job.launch, job.fidelity, job.ion_level, preaccel_eV=pre["preaccel_eV"])
        deadline = time.time() + cfg.backend.job_timeout_s
        ad = self.adapter(job.fidelity)
        self.jobs_since_start += 1
        try:
            meta = ad.run(job, params, ions, out_dir, deadline=deadline)
        except AdapterError:
            raise                      # model untouched beyond parameters: no reload needed
        except Exception:
            self.dirty = True          # COMSOL state unknown: reload before the next job
            raise
        meta["validation_warnings"] = warnings
        meta["preacceleration"] = pre
        return meta


def run_worker(cfg: Config, max_jobs: int | None = None, stop_when_empty: bool = False, name: str = "comsol-worker") -> int:
    from .queue_worker import QueueWorker

    runner = ComsolRunner(cfg)
    w = QueueWorker(cfg.path("queue_dir"), runner, name, root_dir=cfg.root_dir, poll_s=cfg.backend.poll_interval_s)
    try:
        return w.run(max_jobs=max_jobs, stop_when_empty=stop_when_empty)
    finally:
        runner.close()
