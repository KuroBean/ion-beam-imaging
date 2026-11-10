"""Task 9: one 2D job end to end through the real pipeline.

JobSpec -> QueueBackend.submit -> queue/pending -> COMSOL worker (ModelAdapter on the 2D model) ->
queue/done -> fetch -> checker -> plots. Uses config/dev_overrides.yaml for the values still TBD
(placeholders, not physical decisions) plus the job values below.

Usage:  .venv\\Scripts\\python.exe scripts\\run_2d_job.py
Then:   .venv\\Scripts\\python.exe scripts\\reference_run_2d.py results\\<job_id>
"""
from __future__ import annotations

import json
import logging
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ionopt.backends import make_backend  # noqa: E402
from ionopt.checker import check  # noqa: E402
from ionopt.config import load_config  # noqa: E402
from ionopt.jobs import build_job  # noqa: E402
from ionopt.plots import make_plots  # noqa: E402
from ionopt.worker.comsol_worker import run_worker  # noqa: E402

MM = 1e-3
OVERRIDES = [
    "backend.backend=queue",
    "spec.launch.launch_offset_um=0.001",   # 1 nm in front of the apex, as verified for the release file
]
# test job (placeholder voltages): tip +100 V on LV1, E3 at +60 V on LV2 (Einzel-like), rest grounded
CONFIG_ID = "example_einzel"
CHANNELS = {"LV1": 100.0, "LV2": 60.0, "HV1": -10000.0, "HV4": -1000.0}
POSITIONS = {"lens_gap": 13.482 * MM, "z_mcp": 145.0 * MM, "mesh_gap": 12.7 * MM}


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    cfg = load_config(ROOT / "config", overrides=OVERRIDES, override_files=[ROOT / "config" / "dev_overrides.yaml"])
    job = build_job(cfg, cfg.b0_configs.get(CONFIG_ID), CHANNELS, POSITIONS, fidelity="2d",
                    tags={"purpose": "task9_end_to_end"})
    backend = make_backend(cfg)
    t = time.time()
    jid = backend.submit(job)
    print(f"submitted {jid} ({backend.name}); running the COMSOL worker ...", flush=True)
    n = run_worker(cfg, max_jobs=1, stop_when_empty=True)
    print(f"worker processed {n} job(s) in {time.time() - t:.0f} s", flush=True)
    bundle = backend.fetch(jid)
    print(f"status {bundle.status}" + (f": {bundle.error}" if bundle.error else ""))
    if bundle.status != "success":
        sys.exit(1)
    meta = bundle.meta
    print("timings (s):", json.dumps(meta.model_extra.get("timings_s")))
    print("mesh elements:", meta.mesh_elements, "| ions:", meta.n_ions, "| rebuilt geometry:",
          meta.model_extra.get("rebuilt_geometry"))
    print("comsol params:", meta.model_extra.get("comsol_params"))
    m = check(bundle.result_dir, cfg)
    print(f"checker: valid={m.valid} feasible={m.feasible} score={m.score} flags={m.flags}")
    print("fates:", {k: round(v, 3) for k, v in m.fates.items()}, "counts:", m.fate_counts)
    print("validity:", m.validity)
    plots = make_plots(bundle.result_dir, cfg)
    print("plots:", [p.name for p in plots if p])
    print(f"result dir: {bundle.result_dir}")


if __name__ == "__main__":
    main()
