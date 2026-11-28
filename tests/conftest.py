from __future__ import annotations

from pathlib import Path

import pytest

from ionopt.config import load_config

REPO = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO / "config"
DEV_OVERRIDES = CONFIG_DIR / "dev_overrides.yaml"
TEST_PINS = [   # values the analytic tests were written for (not the physical spec values)
    "spec.detector.sigma_mcp_um=80", "spec.detector.mesh_open_fraction=0.8", "spec.launch.preaccel=false",
    "spec.launch.n_theta=26", "spec.launch.n_E=3", "spec.launch.dE_eV=2", "spec.launch.n_phi=8",
    "spec.launch.launch_offset_um=0.0", "spec.launch.t_end_us=100",
    "spec.tolerances.energy_conservation_rel=0.01", "spec.tolerances.energy_conservation_abs_eV=0",
    "spec.tolerances.potential_match_V=1.0", "spec.tolerances.monotonic_tol_um=1.0",
    "spec.tolerances.convergence_rel=0.05", "spec.tolerances.fate_position_tol_um=50",
    "optimizer.write_plots=false",                 # plots have their own tests; keeps the optimizer tests fast
    "spec.requirements.eta_min=0.3", "constraints.supplies.mesh_V=[-1000, 500]",   # the mock optimizer tests' ranges
    "spec.requirements.impact_threshold_mps=null", "spec.requirements.impact_threshold_eV_per_charge=1000",
]
# cfg 1 as the tests' generic chamber (the old dev_overrides placeholders): MCP fixed, held by the chamber.
# The real cfg 1 (MCP on the rods, author 2026-11-22) has its own tests.
CFG1_PINS = [
    "constraints.chamber_setups.1.z_mcp_mm=[145, 145]", "constraints.chamber_setups.1.mesh_gap_mm=[12.7, 12.7]",
    "constraints.chamber_setups.1.lens_gap_mm=[5, 15]", "constraints.chamber_setups.1.mcp_rod_margin_mm=null",
]
TEST_PINS += CFG1_PINS


@pytest.fixture
def cfg():
    """Repo config with the mock-development placeholder values filled in.

    TEST_PINS fix the values the analytic checker tests were written for, independent of the
    physical values in config/spec.yaml; pre-acceleration has its own tests.
    """
    return load_config(CONFIG_DIR, overrides=TEST_PINS, override_files=[DEV_OVERRIDES])


@pytest.fixture
def cfg_tmp(cfg, tmp_path):
    """Like cfg, but every output path points into tmp_path."""
    return cfg.with_overrides([
        f"paths.results_dir={(tmp_path / 'results').as_posix()}",
        f"paths.queue_dir={(tmp_path / 'queue').as_posix()}",
        f"paths.db_path={(tmp_path / 'runlog.sqlite').as_posix()}",
        f"paths.optuna_db_path={(tmp_path / 'optuna.sqlite').as_posix()}",
    ])
