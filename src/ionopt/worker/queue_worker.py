"""Generic queue worker: claims jobs from queue/pending, runs them, files them as done/failed.

The runner decides what a job means: the mock simulator now, the COMSOL runner in task 9
(comsol_worker.py will reuse this loop). The worker owns pending -> running ->
done/failed moves and never leaves a job in running/ when it exits.
"""
from __future__ import annotations

import logging
import os
import time
from pathlib import Path

from ..results import Runner, execute, load_job, load_job_config, write_status_meta
from ..schemas import JobSpec
from ..backends.transports import ensure_queue

log = logging.getLogger(__name__)


class QueueWorker:
    def __init__(self, queue_dir: Path, runner: Runner, name: str, root_dir: Path | None = None,
                 poll_s: float = 1.0):
        self.q = ensure_queue(Path(queue_dir))
        self.runner = runner
        self.name = name
        self.root_dir = root_dir       # where this worker's repo/config lives (paths resolve here)
        self.poll_s = poll_s
        self.current: Path | None = None
        self.n_done = 0

    def claim_next(self) -> Path | None:
        pending = sorted((self.q / "pending").iterdir(), key=lambda p: p.stat().st_mtime)
        for p in pending:
            dst = self.q / "running" / p.name
            try:
                os.replace(p, dst)        # atomic claim; another worker may win the race
            except OSError:
                continue
            return dst
        return None

    def process(self, job_dir: Path) -> str:
        # self.current stays set if anything escapes, so run() can file the job as failed
        self.current = job_dir
        try:
            job = load_job(job_dir)
            cfg = load_job_config(job_dir, root_dir=self.root_dir)
        except Exception as e:  # noqa: BLE001
            stub = JobSpec.model_construct(job_id=job_dir.name)
            write_status_meta(stub, job_dir, "failed", f"cannot read job: {type(e).__name__}: {e}", self.name)
            status = "failed"
        else:
            status = execute(job, cfg, job_dir, self.runner, self.name).status
        target = "done" if status == "success" else "failed"
        os.replace(job_dir, self.q / target / job_dir.name)
        self.current = None
        self.n_done += 1
        log.info("job %s -> %s", job_dir.name, target)
        return target

    def run_once(self) -> bool:
        """Process one pending job if there is one; returns whether a job was processed."""
        job_dir = self.claim_next()
        if job_dir is None:
            return False
        self.process(job_dir)
        return True

    def run(self, max_jobs: int | None = None, stop_when_empty: bool = False, should_stop=lambda: False) -> int:
        """Main loop. Returns the number of jobs processed."""
        n = 0
        try:
            while not should_stop() and (max_jobs is None or n < max_jobs):
                if self.run_once():
                    n += 1
                elif stop_when_empty:
                    break
                else:
                    time.sleep(self.poll_s)
        finally:
            self._abandon_current()
        return n

    def _abandon_current(self) -> None:
        """Never leave a job in running/: file an interrupted job as failed."""
        d = self.current
        if d is not None and d.is_dir():
            stub = JobSpec.model_construct(job_id=d.name)
            write_status_meta(stub, d, "failed", "worker exited while running this job", self.name)
            os.replace(d, self.q / "failed" / d.name)
            self.current = None
