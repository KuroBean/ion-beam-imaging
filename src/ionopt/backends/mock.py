"""Mock simulator and backend: analytic toy optics, same file formats as the worker (plan 9.4).

Toy optics for an ion launched at angle theta with energy KE0:
    rho(theta) = z_mcp * f0 * tan(theta)          (folded above fold_theta_deg if set)
    r_land     = rho + chroma * (KE0 - E0 - preacceleration)
    chroma     = chroma_min + chroma_coeff * (((V_lens - lens_opt)/lens_scale)^2
                                              + ((V_mesh - mesh_opt)/mesh_scale)^2)
V_lens is the voltage of backend.mock.lens_channel (0 if the wiring does not use it),
V_mesh the HV mesh port. The resolution score is therefore best at the known optimum
(lens_opt, mesh_opt). Fates: mesh_frame if (z_mcp - mesh_gap) f0 tan(theta) exceeds the
mesh opening radius, mcp_outside if |r_land| exceeds the active radius, in_flight if the
estimated flight time exceeds t_end. Landing energy from KE0 + q (V_start - V_end).

Failure injection: job.tags["mock_inject"] in {fail, timeout, missing_file, in_flight,
potential_mismatch, energy_error}, or random with the backend.mock *_rate settings.
"""
from __future__ import annotations

import hashlib
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .. import units
from ..config import Config
from ..electrodes import (expand, expected_potentials, geometry_electrodes, hv_potentials, job_launch,
                          model_tip_potential, node_potentials, used_lv_channels, validate_job)
from ..results import JobTimeout, execute, prepare_job_dir, read_bundle
from ..schemas import FILES, FINAL_COLUMNS, JobSpec, ResultBundle
from ..utils import write_json

INJECTIONS = ("fail", "timeout", "missing_file", "in_flight", "potential_mismatch", "energy_error")


class MockFailure(RuntimeError):
    pass


def _rng(cfg: Config, job: JobSpec) -> np.random.Generator:
    h = int(hashlib.sha256(f"{cfg.backend.mock.seed}:{job.job_id}".encode()).hexdigest()[:16], 16)
    return np.random.default_rng(h)


def mock_geometry(job: JobSpec, cfg: Config) -> dict:
    """geometry.json content (plan coordinates, SI) from the job and constraints."""
    spec = cfg.spec
    z_mcp = job.positions["z_mcp"]
    z_mesh = z_mcp - job.positions["mesh_gap"]
    r_mesh = cfg.require("spec.detector.mesh_opening_diameter_mm") / 2 * units.MM
    return {
        "source": "mock",
        "fidelity": job.fidelity,
        "cfg": job.cfg,
        "z_tip_m": 0.0,
        "z_launch_m": (job.launch.launch_offset_um or 0.0) * units.UM,
        "z_mcp_m": z_mcp,
        "r_mcp_active_m": spec.detector.mcp_active_diameter_mm / 2 * units.MM,
        "z_mesh_m": z_mesh,
        "r_mesh_open_m": r_mesh,
        "mesh_frame_z_m": [z_mesh, z_mesh],
        "mesh_frame_r_m": [r_mesh, None],
        "electrodes": geometry_electrodes(job, cfg),
        "t_end_s": job.launch.t_end_us * units.US if job.launch.t_end_us else None,
    }


def run_mock(job: JobSpec, cfg: Config, out_dir: Path) -> dict:
    """Runner: simulate a job with the toy optics and write all raw files into out_dir."""
    t0 = time.time()
    m = cfg.backend.mock
    validate_job(job, cfg)
    rng = _rng(cfg, job)
    inject = job.tags.get("mock_inject")
    if inject is not None and inject not in INJECTIONS:
        raise ValueError(f"unknown mock_inject '{inject}'; use one of {INJECTIONS}")
    if inject is None:
        u = rng.random()
        if u < m.failure_rate:
            inject = "fail"
        elif u < m.failure_rate + m.timeout_rate:
            inject = "timeout"
        elif u < m.failure_rate + m.timeout_rate + m.missing_file_rate:
            inject = "missing_file"
    if inject == "fail":
        raise MockFailure("injected failure")
    if inject == "timeout":
        raise JobTimeout("injected timeout")

    launch = job.launch
    if launch.t_end_us is None:
        from ..config import TBDError
        raise TBDError("spec.launch.t_end_us")
    t_end = launch.t_end_us * units.US
    q = launch.charge
    mass = launch.mass_Da * units.DALTON
    ions, pre_rec = job_launch(job, cfg)
    pre = pre_rec["preaccel_eV"]
    ions.to_csv(out_dir / FILES["ions_launch"], index=False)
    geom = mock_geometry(job, cfg)
    write_json(out_dir / FILES["geometry"], geom)

    pots = node_potentials(job, cfg)
    hv = hv_potentials(job, cfg)
    v_lens = job.channels[m.lens_channel] if m.lens_channel in used_lv_channels(cfg, job.wiring) else 0.0
    chroma = m.chroma_min_m_per_eV + m.chroma_coeff_m_per_eV * (
        ((v_lens - m.lens_opt_V) / m.lens_scale_V) ** 2 + ((hv["mesh"] - m.mesh_opt_V) / m.mesh_scale_V) ** 2)

    th = np.radians(ions["theta_launch_deg"].to_numpy())
    phi = np.radians(ions["phi_deg"].to_numpy())
    ke0 = ions["KE0_eV"].to_numpy()
    z_mcp, z_mesh = geom["z_mcp_m"], geom["z_mesh_m"]
    z0 = geom["z_launch_m"]
    tan = np.tan(th)
    if m.fold_theta_deg is not None:
        tf = math.tan(math.radians(m.fold_theta_deg))
        tan = np.where(tan > tf, 2 * tf - tan, tan)
    rho = z_mcp * m.f0 * tan
    r_land = rho + chroma * (ke0 - launch.E0_eV - pre) + rng.normal(0, m.noise_r_um * units.UM, len(th))
    rho_mesh = z_mesh * m.f0 * tan

    n = len(ions)
    z_end = np.full(n, z_mcp)
    r_end = r_land.copy()
    v_end_pot = np.full(n, hv["mcp_front"])
    at_mesh = np.abs(rho_mesh) > geom["r_mesh_open_m"]
    z_end[at_mesh] = z_mesh
    r_end[at_mesh] = rho_mesh[at_mesh]
    v_end_pot[at_mesh] = hv["mesh"]
    v_start = np.full(n, model_tip_potential(job, cfg))

    ke_end = ke0 + q * (v_start - v_end_pot)
    reflected = ke_end <= 0                    # cannot reach the surface: falls back onto the tip
    z_end[reflected] = 0.0
    r_end[reflected] = 0.0
    v_end_pot[reflected] = v_start[reflected]
    ke_end[reflected] = ke0[reflected]
    ke_end = ke_end + rng.normal(0, m.energy_noise_eV, n) if m.energy_noise_eV else ke_end
    if inject == "energy_error":
        ke_end = ke_end * 1.1

    v0 = units.ke_eV_to_speed(ke0, mass)
    v1 = units.ke_eV_to_speed(np.maximum(ke_end, 0), mass)
    path = np.hypot(z_end - z0, r_end)
    tof = np.where(reflected, 2 * z0 / np.maximum(v0, 1e-30) + 1e-9, path / (0.5 * (v0 + v1)))
    in_flight = (tof > t_end) & ~reflected
    if inject == "in_flight":
        in_flight[: max(1, n // 10)] = True
    # in-flight ions: stop part-way along the path at t_end
    frac = np.clip(t_end / np.maximum(tof, 1e-30), 0, 1)
    z_end = np.where(in_flight, z0 + (z_end - z0) * np.minimum(frac, 0.5), z_end)
    r_end = np.where(in_flight, r_end * np.minimum(frac, 0.5), r_end)
    tof = np.where(in_flight, t_end, tof)
    v_end_pot = np.where(in_flight, np.interp(z_end, *_axis_nodes(job, cfg, geom)), v_end_pot)
    ke_end = np.where(in_flight, ke0 + q * (v_start - v_end_pot), ke_end)
    v1 = units.ke_eV_to_speed(np.maximum(ke_end, 0), mass)

    alpha = np.arctan2(np.abs(r_end), np.maximum(z_end - z0, 1e-12))   # direction ~ straight line from source
    sgn = np.sign(r_end)
    sgn[sgn == 0] = 1
    if job.fidelity == "2d":
        x, y = np.abs(r_end), np.zeros(n)
        vx, vy = v1 * np.sin(alpha), np.zeros(n)
    else:
        x, y = r_end * np.cos(phi), r_end * np.sin(phi)
        vx, vy = sgn * v1 * np.sin(alpha) * np.cos(phi), sgn * v1 * np.sin(alpha) * np.sin(phi)
    vz = np.where(reflected, -v0, v1 * np.cos(alpha))
    final = pd.DataFrame({
        "ion_id": ions["ion_id"], "x_m": x, "y_m": y, "z_m": z_end, "vx_mps": vx, "vy_mps": vy, "vz_mps": vz,
        "KE_eV": ke_end, "t_s": tof, "V_start_V": v_start, "V_end_V": v_end_pot,
    })[FINAL_COLUMNS]
    final = final.sample(frac=1, random_state=int(rng.integers(1 << 31)))  # COMSOL order is not ion order
    if inject != "missing_file":
        final.to_csv(out_dir / FILES["ions_final"], index=False)
    # toy trajectories (straight lines, phi = 0 ions only) so trajectory plots can be developed
    sel = np.where(ions["phi_deg"].to_numpy() == 0)[0]
    s = np.linspace(0, 1, 12)
    pd.DataFrame({
        "ion_id": np.repeat(ions["ion_id"].to_numpy()[sel], len(s)),
        "t_s": (tof[sel, None] * s).ravel(),
        "x_m": (x[sel, None] * s).ravel(), "y_m": (y[sel, None] * s).ravel(),
        "z_m": (z0 + (z_end[sel, None] - z0) * s).ravel(),
    }).to_csv(out_dir / FILES["traj"], index=False)

    _write_fields(job, cfg, geom, out_dir)
    ep = expected_potentials(job, cfg)
    if inject == "potential_mismatch":
        ep["sel_tip"] += 10.0
    pd.DataFrame({"selection": list(ep), "V_mean_V": list(ep.values())}).to_csv(
        out_dir / FILES["electrode_potentials"], index=False)
    return {"params": expand(job, cfg), "n_ions": n, "model_file": "mock", "mesh_elements": 0,
            "mock_chroma_m_per_eV": chroma, "mock_runtime_s": round(time.time() - t0, 4)}


def _axis_nodes(job: JobSpec, cfg: Config, geom: dict) -> tuple[np.ndarray, np.ndarray]:
    """Piecewise-linear toy axis potential through tip, electrodes, mesh and MCP."""
    ep = expected_potentials(job, cfg)
    hv = hv_potentials(job, cfg)
    pts = [(0.0, ep["sel_tip"])] + [(e["z_m"], ep[e["selection"]]) for e in geom["electrodes"]] + \
          [(geom["z_mesh_m"], hv["mesh"]), (geom["z_mcp_m"], hv["mcp_front"])]
    z, v = map(np.array, zip(*sorted(pts)))
    return z, v


def _write_fields(job: JobSpec, cfg: Config, geom: dict, out_dir: Path) -> None:
    zn, vn = _axis_nodes(job, cfg, geom)
    z = np.linspace(0, geom["z_mcp_m"], 600)
    v = np.interp(z, zn, vn)
    ez = -np.gradient(v, z)
    pd.DataFrame({"z_m": z, "V_V": v, "Ez_Vpm": ez}).to_csv(out_dir / FILES["axis_potential"], index=False)
    r_max = max(geom["r_mcp_active_m"], *(e["r_out_m"] or 0 for e in geom["electrodes"])) * 1.5
    rr, zz = np.meshgrid(np.linspace(0, r_max, 30), np.linspace(0, geom["z_mcp_m"], 200))
    vv = np.interp(zz, zn, vn)
    ee = np.abs(np.interp(zz, z, ez))
    pd.DataFrame({"r_m": rr.ravel(), "z_m": zz.ravel(), "V_V": vv.ravel(), "Emag_Vpm": ee.ravel()}).to_csv(
        out_dir / FILES["cutplane_field"], index=False)


class MockBackend:
    """Synchronous backend: each submit runs the toy simulator immediately."""

    name = "mock"

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.results_dir = cfg.path("results_dir")

    def submit(self, job: JobSpec) -> str:
        d = prepare_job_dir(job, self.cfg, self.results_dir / job.job_id)
        execute(job, self.cfg, d, run_mock, self.name)
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
