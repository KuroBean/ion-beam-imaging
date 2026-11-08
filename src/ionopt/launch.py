"""Deterministic launch grid and weights (plan 9.1).

The grid describes ions at the simulated launch point (``launch_offset_um`` in front of
the model tip apex, on the axis), not at the real emission site.

Weights for each ion:
    w_theta = exp(-theta^2 / (2 sigma^2)) * sin(theta) * dtheta   (trapezoid quadrature)
    w_E     = energy_weight(KE) * dE_bin                           (uniform by default)
    w_phi   = dphi = 2 pi / n_phi  (3D)   or 2 pi  (2D: one meridional ray per theta)
    weight  = w_theta * w_E * w_phi, normalized to sum to 1.
The separate factors are stored so the checker can weight within a theta group.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from . import units
from .config import LaunchConfig, TBDError
from .schemas import Fidelity, LAUNCH_COLUMNS

EnergyWeight = Callable[[np.ndarray], np.ndarray]


def _req(launch: LaunchConfig, field: str):
    v = getattr(launch, field)
    if v is None:
        raise TBDError(f"spec.launch.{field}")
    return v


def theta_grid(n_theta: int, theta_max_rad: float, sigma_rad: float) -> tuple[np.ndarray, np.ndarray]:
    """Theta nodes from 0 to theta_max and their weights exp(-t^2/2s^2) sin(t) dtheta."""
    theta = np.linspace(0.0, theta_max_rad, n_theta)
    dtheta = np.full(n_theta, theta_max_rad / (n_theta - 1))
    dtheta[[0, -1]] *= 0.5
    w = np.exp(-theta**2 / (2 * sigma_rad**2)) * np.sin(theta) * dtheta
    return theta, w


def energy_grid(E0_eV: float, dE_eV: float, n_E: int,
                energy_weight: EnergyWeight | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Energies at the midpoints of n_E equal bins across [E0 - dE/2, E0 + dE/2]."""
    if n_E == 1 or dE_eV == 0:
        return np.array([E0_eV]), np.array([1.0])
    edges = np.linspace(E0_eV - dE_eV / 2, E0_eV + dE_eV / 2, n_E + 1)
    ke = 0.5 * (edges[:-1] + edges[1:])
    w = np.diff(edges) * (np.ones_like(ke) if energy_weight is None else np.asarray(energy_weight(ke), float))
    if np.any(w < 0) or w.sum() <= 0:
        raise ValueError("energy weight function must be non-negative and not all zero")
    return ke, w / w.sum()


def make_launch(launch: LaunchConfig, fidelity: Fidelity, ion_level: str = "search",
                energy_weight: EnergyWeight | None = None) -> pd.DataFrame:
    """Ion table with columns LAUNCH_COLUMNS (SI positions/velocities, plan coordinates)."""
    n_theta = _req(launch, "n_theta")
    n_E = _req(launch, "n_E")
    E0 = _req(launch, "E0_eV")
    mass_kg = _req(launch, "mass_Da") * units.DALTON
    z0 = _req(launch, "launch_offset_um") * units.UM
    if ion_level == "convergence":
        n_theta = (n_theta - 1) * launch.convergence_ion_factor + 1   # keeps the search grid points
    elif ion_level != "search":
        raise ValueError(f"unknown ion_level '{ion_level}'")

    theta, w_theta = theta_grid(n_theta, launch.theta_max_deg * units.DEG, launch.sigma_rad)
    ke, w_E = energy_grid(E0, launch.dE_eV, n_E, energy_weight)

    rows = []
    if fidelity == "2d":
        phis = [(0.0, 2 * math.pi)]
    elif fidelity == "3d":
        n_phi = _req(launch, "n_phi")
        phis = [(2 * math.pi * j / n_phi, 2 * math.pi / n_phi) for j in range(n_phi)]
    else:
        raise ValueError(f"unknown fidelity '{fidelity}'")
    for i, (t, wt) in enumerate(zip(theta, w_theta)):
        # theta = 0 is the same ray for every phi: launch it once, representing the full ring
        phi_list = [(0.0, 2 * math.pi)] if i == 0 else phis
        for phi, wp in phi_list:
            for e, we in zip(ke, w_E):
                rows.append((t, phi, e, wt, we, wp))
    a = np.array(rows)
    t, phi, e, wt, we, wp = a.T
    speed = units.ke_eV_to_speed(e, mass_kg)
    w = wt * we * wp
    df = pd.DataFrame({
        "ion_id": np.arange(len(a)),
        "theta_deg": np.degrees(t),
        "phi_deg": np.degrees(phi),
        "KE0_eV": e,
        "w_theta": wt, "w_E": we, "w_phi": wp,
        "weight": w / w.sum(),
        "x_m": 0.0, "y_m": 0.0, "z_m": z0,
        "vx_mps": speed * np.sin(t) * np.cos(phi),
        "vy_mps": speed * np.sin(t) * np.sin(phi),
        "vz_mps": speed * np.cos(t),
    })
    return df[LAUNCH_COLUMNS]


def write_release_file(df: pd.DataFrame, path: Path | str, fidelity: Fidelity, z_shift_m: float = 0.0,
                       axis_offset_m: float = 0.0) -> None:
    """Write a COMSOL 'release from data file' table, one row per ion in ion_id order.

    z_shift_m converts plan coordinates (origin at tip apex) to model coordinates
    (z_model = z + z_shift); the adapter passes the model's tip_z.
    2D (verified in COMSOL 5.5): columns r[mm] z[mm] vr vz [m/s]; r >= axis_offset.
    3D (format NOT yet verified, task 8): columns x y z [mm] vx vy vz [m/s].
    """
    d = df.sort_values("ion_id")
    z_mm = (d["z_m"].to_numpy() + z_shift_m) / units.MM
    if fidelity == "2d":
        r = np.maximum(np.hypot(d["x_m"], d["y_m"]).to_numpy(), axis_offset_m) / units.MM
        vr = np.hypot(d["vx_mps"], d["vy_mps"]).to_numpy()
        out = np.c_[r, z_mm, vr, d["vz_mps"].to_numpy()]
        header = "2D-axisymmetric release: r[mm] z[mm] vr vz [m/s]; row i = ion_id i"
    else:
        out = np.c_[d["x_m"].to_numpy() / units.MM, d["y_m"].to_numpy() / units.MM, z_mm,
                    d[["vx_mps", "vy_mps", "vz_mps"]].to_numpy()]
        header = "3D release: x[mm] y[mm] z[mm] vx vy vz [m/s]; row i = ion_id i"
    np.savetxt(path, out, fmt="%.10g", comments="% ", header=header)
