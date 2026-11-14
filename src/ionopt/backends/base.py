"""SimulationBackend interface and factory (plan 9.3). Agents and the optimizer only see this."""
from __future__ import annotations

from typing import Literal, Protocol

from ..config import Config
from ..schemas import JobSpec, ResultBundle


class SimulationBackend(Protocol):
    name: str

    def submit(self, job: JobSpec) -> str: ...
    def status(self, job_id: str) -> Literal["pending", "running", "done", "failed"]: ...
    def fetch(self, job_id: str) -> ResultBundle: ...
    def run(self, job: JobSpec, timeout_s: float | None = None) -> ResultBundle: ...


def make_transport(cfg: Config):
    from .transports import LocalFSTransport, SSHTransport

    if cfg.backend.transport == "local":
        return LocalFSTransport(cfg.path("queue_dir"))
    return SSHTransport(cfg.backend.ssh.host_env_var, cfg.backend.ssh.remote_queue_dir_env_var)


def make_backend(cfg: Config) -> SimulationBackend:
    """Backend selected by backend.yaml."""
    if cfg.backend.backend == "mock":
        from .mock import MockBackend

        return MockBackend(cfg)
    if cfg.backend.backend == "comsol":
        from .local_comsol import LocalComsolBackend

        return LocalComsolBackend(cfg)
    from .queue import QueueBackend

    return QueueBackend(cfg, make_transport(cfg))
