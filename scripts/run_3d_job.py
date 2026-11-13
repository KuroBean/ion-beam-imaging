"""One 3D job end to end through the real pipeline (same path as run_2d_job.py, 3D model).

The 3D worker refuses geometry changes (backend.worker.allow_3d_geometry_change = false), so the job
uses the geometry stored in the 3D model: cfg 3 (chambers joined), lens_gap 13.482 mm, mesh_gap
12.7 mm, MCP face at mcp_z - tip_z = 515.9 - 105 = 410.9 mm. Channels match the task 9 2D test job
(placeholder voltages from run_2d_job.py). The particle rtol is backend.worker.particle_rtol (1e-9).

Usage:  .venv\\Scripts\\python.exe scripts\\run_3d_job.py [--set key=value ...]
"""
from __future__ import annotations

import argparse
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
    "spec.launch.launch_offset_um=0.001",   # 1 nm in front of the apex, as for the 2D job
]
BASE_CONFIG_ID = "example_einzel"          # wiring tip -> LV1, e3 -> LV2; run in cfg 3 (the stored 3D geometry)
CFG = 3
CHANNELS = {"LV1": 100.0, "LV2": 60.0, "HV1": -10000.0, "HV4": -1000.0}
POSITIONS = {"lens_gap": 13.482 * MM, "z_mcp": 410.9 * MM, "mesh_gap": 12.7 * MM}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", action="append", default=[], help="config override key=value")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    cfg = load_config(ROOT / "config", overrides=OVERRIDES + a.set,
                      override_files=[ROOT / "config" / "dev_overrides.yaml"])
    conf = cfg.b0_configs.get(BASE_CONFIG_ID).model_copy(update={"cfg": CFG, "config_id": f"{BASE_CONFIG_ID}_cfg{CFG}"})
    job = build_job(cfg, conf, CHANNELS, POSITIONS, fidelity="3d", tags={"purpose": "3d_smoke_mesh_gap"})
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
          meta.model_extra.get("rebuilt_geometry"), "| particle rtol:", meta.model_extra.get("particle_rtol"))
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
