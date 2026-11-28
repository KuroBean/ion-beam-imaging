"""Synchronous COMSOL backend: runs each job in this process (backend.backend = comsol).

For optimization studies on one machine. One COMSOL client and the loaded model stay open across
jobs (ComsolRunner reloads after backend.worker.restart_after_jobs). Results go to
results/<job_id>/ exactly as with the queue worker. Call close() (or use it as a context manager)
to shut COMSOL down.
"""
from __future__ import annotations

from ..config import Config
from ..results import execute, prepare_job_dir, read_bundle
from ..schemas import FILES, JobSpec, ResultBundle


class LocalComsolBackend:
    name = "comsol"

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.results_dir = cfg.path("results_dir")
        self._runner = None

    @property
    def runner(self):
        if self._runner is None:
            from ..worker.comsol_worker import ComsolRunner
            self._runner = ComsolRunner(self.cfg)
        return self._runner

    def submit(self, job: JobSpec) -> str:
        d = prepare_job_dir(job, self.cfg, self.results_dir / job.job_id)
        execute(job, self.cfg, d, self.runner, self.name)
        return job.job_id

    def status(self, job_id: str) -> str:
        d = self.results_dir / job_id
        if not (d / FILES["meta"]).is_file():
            return "pending" if d.is_dir() else "failed"
        return "done" if read_bundle(d).status == "success" else "failed"

    def fetch(self, job_id: str) -> ResultBundle:
        return read_bundle(self.results_dir / job_id)

    def run(self, job: JobSpec, timeout_s: float | None = None) -> ResultBundle:
        return self.fetch(self.submit(job))

    def close(self) -> None:
        if self._runner is not None:
            self._runner.close()
            self._runner = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
