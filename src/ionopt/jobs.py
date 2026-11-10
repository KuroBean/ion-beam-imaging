"""Building JobSpecs from a structural configuration plus continuous variables."""
from __future__ import annotations

from .config import Config, ConfigurationDef
from .schemas import Fidelity, JobSpec


def build_job(cfg: Config, conf: ConfigurationDef, channels: dict[str, float], positions: dict[str, float],
              fidelity: Fidelity = "2d", mesh_level: str = "normal", ion_level: str = "search",
              tags: dict[str, str] | None = None, job_id: str | None = None) -> JobSpec:
    """JobSpec for a configuration (chamber setup, wiring).

    channels in V (LV channels used by the wiring, MCP-front and mesh HV ports);
    positions in metres (lens_gap, z_mcp, mesh_gap).
    The current spec.launch section is copied into the job so it is self-contained.
    """
    t = {"config_id": conf.config_id, **(tags or {})}
    kw = dict(fidelity=fidelity, cfg=conf.cfg, wiring=dict(conf.wiring), channels=dict(channels), positions=dict(positions),
              launch=cfg.spec.launch.model_copy(), mesh_level=mesh_level, ion_level=ion_level, tags=t)
    if job_id:
        kw["job_id"] = job_id
    return JobSpec(**kw)
