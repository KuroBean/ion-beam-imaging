from __future__ import annotations

from pathlib import Path

import pytest

from ionopt.config import load_config

REPO = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO / "config"
DEV_OVERRIDES = CONFIG_DIR / "dev_overrides.yaml"


@pytest.fixture
def cfg():
    """Repo config with the mock-development placeholder values filled in."""
    return load_config(CONFIG_DIR, override_files=[DEV_OVERRIDES])


@pytest.fixture
def cfg_tmp(cfg, tmp_path):
    """Like cfg, but every output path points into tmp_path."""
    return cfg.with_overrides([
        f"paths.results_dir={(tmp_path / 'results').as_posix()}",
        f"paths.queue_dir={(tmp_path / 'queue').as_posix()}",
        f"paths.db_path={(tmp_path / 'runlog.sqlite').as_posix()}",
        f"paths.optuna_db_path={(tmp_path / 'optuna.sqlite').as_posix()}",
    ])
