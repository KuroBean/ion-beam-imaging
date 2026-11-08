"""QueueBackend: submits job folders through a Transport and waits for a worker (plan 9.3)."""
from __future__ import annotations

import time
from pathlib import Path

from ..config import Config
from ..results import prepare_job_dir, read_bundle, write_status_meta
from ..schemas import JobSpec, ResultBundle
from .transports import Transport


class QueueBackend:
    name = "queue"

    def __init__(self, cfg: Config, transport: Transport, poll_interval_s: float | None = None):
        self.cfg = cfg
        self.transport = transport
        self.results_dir = cfg.path("results_dir")
        self.poll = poll_interval_s if poll_interval_s is not None else cfg.backend.poll_interval_s

    def submit(self, job: JobSpec) -> str:
        d = prepare_job_dir(job, self.cfg, self.results_dir / job.job_id)
        self.transport.put_job(job.job_id, d)
        return job.job_id

    def status(self, job_id: str) -> str:
        s = self.transport.state(job_id)
        return "failed" if s == "unknown" else s

    def fetch(self, job_id: str) -> ResultBundle:
        dest = self.results_dir / job_id
        self.transport.get_results(job_id, dest)
        return read_bundle(dest)

    def wait(self, job_id: str, timeout_s: float) -> str:
        t_end = time.monotonic() + timeout_s
        while True:
            s = self.transport.state(job_id)
            if s in ("done", "failed", "unknown") or time.monotonic() >= t_end:
                return s
            time.sleep(self.poll)

    def run(self, job: JobSpec, timeout_s: float | None = None) -> ResultBundle:
        self.submit(job)
        s = self.wait(job.job_id, timeout_s if timeout_s is not None else self.cfg.backend.job_timeout_s)
        if s in ("done", "failed"):
            return self.fetch(job.job_id)
        d = self.results_dir / job.job_id
        msg = "job vanished from the queue" if s == "unknown" else f"no result after waiting (queue state: {s})"
        write_status_meta(job, d, "timeout" if s != "unknown" else "failed", msg, self.name)
        return read_bundle(d)
