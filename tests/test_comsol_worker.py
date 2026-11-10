"""End-to-end 2D job through queue + COMSOL worker + checker (needs COMSOL; run with -m comsol, ~1 min)."""
import json
from pathlib import Path

import pytest

from ionopt.backends import make_backend
from ionopt.checker import check
from ionopt.config import load_config
from ionopt.jobs import build_job

ROOT = Path(__file__).resolve().parent.parent
MM = 1e-3


@pytest.mark.comsol
def test_2d_job_end_to_end(tmp_path):
    cfg = load_config(ROOT / "config", override_files=[ROOT / "config" / "dev_overrides.yaml"],
                      overrides=["backend.backend=queue", "spec.launch.launch_offset_um=0.001",
                                 f"paths.queue_dir={(tmp_path / 'queue').as_posix()}",
                                 f"paths.results_dir={(tmp_path / 'results').as_posix()}",
                                 f"paths.db_path={(tmp_path / 'runlog.sqlite').as_posix()}",
                                 f"paths.models.2d={(ROOT / cfg_model()).as_posix()}"])
    from ionopt.worker.comsol_worker import run_worker

    job = build_job(cfg, cfg.b0_configs.get("example_einzel"), {"LV1": 100.0, "LV2": 60.0, "HV1": -10000.0,
                                                                "HV4": -1000.0},
                    {"lens_gap": 13.482 * MM, "z_mcp": 145.0 * MM, "mesh_gap": 12.7 * MM}, fidelity="2d")
    backend = make_backend(cfg)
    jid = backend.submit(job)
    assert run_worker(cfg, max_jobs=1, stop_when_empty=True) == 1
    b = backend.fetch(jid)
    assert b.status == "success", b.error
    meta = json.loads((Path(b.result_dir) / "meta.json").read_text())
    assert meta["n_ions"] == 78 and meta["comsol_params"]["z_mcp_c1"] == "250.0[mm]"
    m = check(b.result_dir, cfg)
    assert m.validity["potentials_match"] and m.validity["energy_conserved"] and m.validity["no_in_flight"]
    assert m.fate_counts["mcp_active"] > 30


def cfg_model() -> str:
    return load_config(ROOT / "config").paths.models["2d"]
