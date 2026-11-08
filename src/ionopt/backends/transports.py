"""Transports move job folders between the submitting side and a worker's queue (plan 9.3).

Queue layout (owned by the worker after submission):
    queue/incoming/<job_id>/   being written by the transport (invisible to workers)
    queue/pending/<job_id>/    ready; a worker claims it by renaming into running/
    queue/running/<job_id>/
    queue/done/<job_id>/       finished (meta.json status success)
    queue/failed/<job_id>/     failed or timed out
Each job folder holds job.json + config_snapshot.yaml, plus the outputs once run.
"""
from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Literal, Protocol

QueueState = Literal["pending", "running", "done", "failed", "unknown"]
QUEUE_DIRS = ("incoming", "pending", "running", "done", "failed")


class Transport(Protocol):
    def put_job(self, job_id: str, src_dir: Path) -> None: ...
    def state(self, job_id: str) -> QueueState: ...
    def list_done(self) -> list[str]: ...
    def get_results(self, job_id: str, dest_dir: Path) -> None: ...


def ensure_queue(queue_dir: Path) -> Path:
    for d in QUEUE_DIRS:
        (queue_dir / d).mkdir(parents=True, exist_ok=True)
    return queue_dir


class LocalFSTransport:
    """Queue on a local (or mounted) file system."""

    def __init__(self, queue_dir: Path):
        self.q = ensure_queue(Path(queue_dir))

    def put_job(self, job_id: str, src_dir: Path) -> None:
        tmp = self.q / "incoming" / job_id
        if tmp.exists():
            shutil.rmtree(tmp)
        shutil.copytree(src_dir, tmp)
        os.replace(tmp, self.q / "pending" / job_id)       # atomic: workers never see a partial job

    def state(self, job_id: str) -> QueueState:
        for s in ("done", "failed", "running", "pending"):
            if (self.q / s / job_id).is_dir():
                return s  # type: ignore[return-value]
        return "unknown"

    def list_done(self) -> list[str]:
        return sorted(p.name for s in ("done", "failed") for p in (self.q / s).iterdir() if p.is_dir())

    def get_results(self, job_id: str, dest_dir: Path) -> None:
        st = self.state(job_id)
        if st not in ("done", "failed"):
            raise FileNotFoundError(f"job {job_id} is not finished (state: {st})")
        shutil.copytree(self.q / st / job_id, dest_dir, dirs_exist_ok=True)


class SSHTransport:
    """Stub for the lab machine (plan task 12). Same interface as LocalFSTransport.

    Host alias and remote queue directory come from environment variables named in
    backend.yaml (ssh.host_env_var, ssh.remote_queue_dir_env_var); never from the repo.
    """

    def __init__(self, host_env_var: str, remote_queue_dir_env_var: str):
        self.host = os.environ.get(host_env_var)
        self.remote_dir = os.environ.get(remote_queue_dir_env_var)

    def _todo(self, *_a, **_k):
        raise NotImplementedError("SSHTransport is a Phase 1 stub (plan task 12)")

    put_job = state = list_done = get_results = _todo
