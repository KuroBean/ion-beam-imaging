"""Data schemas shared by backends, worker, checker and optimizer (plan 9.2).

Units: positions in metres, potentials in volts, kinetic energies in eV.
"""
from __future__ import annotations

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .config import LaunchConfig

Fidelity = Literal["2d", "3d"]
JobStatus = Literal["pending", "running", "done", "failed"]
FATES = ("mcp_active", "mcp_outside", "mesh_frame", "electrode", "wall", "in_flight")

# files in results/<job_id>/ (plan 9.2 table)
FILES = {
    "job": "job.json",
    "config_snapshot": "config_snapshot.yaml",
    "meta": "meta.json",
    "ions_launch": "ions_launch.csv",
    "ions_final": "ions_final.csv",
    "axis_potential": "axis_potential.csv",
    "cutplane_field": "cutplane_field.csv",
    "electrode_potentials": "electrode_potentials.csv",
    "traj": "traj.csv",
    "geometry": "geometry.json",
    "ions_derived": "ions_derived.csv",
    "metrics": "metrics.json",
}
# raw files every successful simulation must produce (traj is optional)
REQUIRED_RAW = ("ions_launch", "ions_final", "axis_potential", "cutplane_field",
                "electrode_potentials", "geometry", "meta")

# column contracts for the raw per-ion files
LAUNCH_COLUMNS = ["ion_id", "theta_deg", "theta_launch_deg", "phi_deg", "KE0_eV", "w_theta", "w_E", "w_phi", "weight",
                  "x_m", "y_m", "z_m", "vx_mps", "vy_mps", "vz_mps"]
FINAL_COLUMNS = ["ion_id", "x_m", "y_m", "z_m", "vx_mps", "vy_mps", "vz_mps", "KE_eV", "t_s",
                 "V_start_V", "V_end_V"]


def new_job_id() -> str:
    return uuid.uuid4().hex


class JobSpec(BaseModel):
    """One simulation request. Self-contained: carries the launch settings it uses."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(default_factory=new_job_id)
    fidelity: Fidelity = "2d"
    cfg: int
    wiring: dict[str, str] = {}                # tip / e<k> -> LV1..LV4 or GND; unlisted nodes are GND
    channels: dict[str, float]                 # V, e.g. {"LV1": 100, "LV2": 85, "HV1": -10000, "HV4": 0}
    positions: dict[str, float]                # m: lens_gap, z_mcp, mesh_gap (fixed lens stack)
    launch: LaunchConfig
    mesh_level: Literal["normal", "fine"] = "normal"
    ion_level: Literal["search", "convergence"] = "search"   # convergence = more ions
    tags: dict[str, str] = {}                  # study_id, config_id, purpose, mock_inject, ...


class RunMeta(BaseModel):
    """Run metadata written by the worker (meta.json). Extra keys are allowed."""

    model_config = ConfigDict(extra="allow")

    job_id: str
    status: Literal["success", "failed", "timeout"]
    error: str | None = None
    backend: str = ""
    worker_host: str = ""
    params: dict[str, Any] = {}                # resolved model parameters (registry names)
    model_file: str | None = None
    model_hash: str | None = None
    comsol_version: str | None = None
    mesh_elements: int | None = None
    solve_time_s: float | None = None
    git_commit: str | None = None
    config_hash: str | None = None
    started_at: str | None = None
    finished_at: str | None = None
    n_ions: int | None = None


class ResultBundle(BaseModel):
    """Describes the files in results/<job_id>/."""

    job_id: str
    status: Literal["success", "failed", "timeout"]
    error: str | None = None
    result_dir: str
    files: dict[str, str] = {}                 # key (see FILES) -> path
    meta: RunMeta | None = None


class Metrics(BaseModel):
    """Checker output (metrics.json)."""

    model_config = ConfigDict(extra="allow")

    job_id: str
    spec_hash: str
    valid: bool
    feasible: bool
    score: float | None = None                 # summary dtheta in degrees (lower is better)
    flags: list[str] = []                      # human-readable reasons for invalid/infeasible
    validity: dict[str, bool] = {}
    fates: dict[str, float] = {}               # weight fraction per fate (relative to all launched)
    fate_counts: dict[str, int] = {}
    spot: dict[str, float | None] = {}
    mapping: dict[str, Any] = {}
    requirements: dict[str, Any] = {}
