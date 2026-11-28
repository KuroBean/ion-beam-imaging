"""Check the 2D part switches (L<k>_on, L<k>_dz, D<n>_on) of a rebuilt 2D model against a stored run.

1. reruns a stored job (made on the previous 2D model) on the new model, as built: results must match
2. runs the same settings with parts removed / moved: the worker cross-checks every present part's
   front face in the model against constraints.electrodes (with the offsets) and must not fail
3. reruns the as-built job: the switches must reset (no stale removed parts), same as 1

Usage (2D, ~2 min):
  .venv\\Scripts\\python.exe scripts\\verify_part_switches.py <stored job_id> --model lens8_axisym_v3.mph
      [--overrides config/dev_overrides.yaml] [--remove e2 d1] [--move e3=15]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ionopt import units  # noqa: E402
from ionopt.backends import make_backend  # noqa: E402
from ionopt.checker import check  # noqa: E402
from ionopt.config import load_config  # noqa: E402
from ionopt.electrodes import validate_job  # noqa: E402
from ionopt.schemas import FILES, JobSpec, new_job_id  # noqa: E402


def final(d: Path) -> pd.DataFrame:
    return pd.read_csv(d / FILES["ions_final"]).set_index("ion_id").sort_index()


def compare(a: Path, b: Path) -> dict:
    fa, fb = final(a), final(b)
    r = lambda f: np.hypot(f["x_m"], f["y_m"])  # noqa: E731
    both = fa["z_m"].notna() & fb["z_m"].notna()
    return {"n_ions": len(fa), "max_dr_um": float((r(fa) - r(fb))[both].abs().max() / units.UM),
            "max_dz_um": float((fa["z_m"] - fb["z_m"])[both].abs().max() / units.UM),
            "max_dKE_eV": float((fa["KE_eV"] - fb["KE_eV"])[both].abs().max())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("job_id")
    ap.add_argument("--model", default="lens8_axisym_v3.mph")
    ap.add_argument("--overrides", action="append", default=[], type=Path)
    ap.add_argument("--remove", nargs="*", default=["e2", "d1"])
    ap.add_argument("--move", nargs="*", default=["e3=15"], help="plate=front offset from E1 (mm)")
    a = ap.parse_args()

    cfg = load_config(ROOT / "config", [f"paths.models.2d={a.model}", "backend.backend=comsol",
                                        "constraints.electrical.max_field_kV_per_mm=null"], a.overrides)
    rd = cfg.path("results_dir")
    base = JobSpec.model_validate_json((rd / a.job_id / FILES["job"]).read_text(encoding="utf-8"))
    tags = {**base.tags, "purpose": "verify_part_switches", "model": a.model}

    def variant(removed=(), moved=None):
        pos = dict(base.positions)
        pos.update({f"{k}_offset": float(v) * units.MM for k, v in (moved or {}).items()})
        return base.model_copy(update={"job_id": new_job_id(), "removed": list(removed), "positions": pos,
                                       "tags": tags})

    moved = dict(m.split("=") for m in a.move)
    jobs = [("as built", variant()), ("switched", variant(a.remove, moved)), ("as built again", variant())]
    out = {"stored_job": a.job_id, "model": a.model, "runs": []}
    backend = make_backend(cfg)
    try:
        for name, job in jobs:
            validate_job(job, cfg)
            res = backend.run(job, cfg.backend.job_timeout_s)
            meta = json.loads((Path(res.result_dir) / FILES["meta"]).read_text(encoding="utf-8"))
            row = {"name": name, "job_id": job.job_id, "status": res.status, "error": res.error,
                   "removed": job.removed, "moved_mm": moved if name == "switched" else {},
                   "rebuilt_geometry": meta.get("rebuilt_geometry"), "mesh_elements": meta.get("mesh_elements")}
            if res.status == "success":
                m = check(Path(res.result_dir), cfg, write=False)
                row.update(valid=m.valid, score=m.score, eta=(m.requirements or {}).get("eta"),
                           flags=m.flags, boxes=json.loads((Path(res.result_dir) / FILES["geometry"]).read_text())
                           ["model_boxes"])
                if name != "switched":
                    row["vs_stored"] = compare(rd / a.job_id, Path(res.result_dir))
            out["runs"].append(row)
            print(json.dumps({k: v for k, v in row.items() if k != "boxes"}, indent=1, default=str), flush=True)
    finally:
        if hasattr(backend, "close"):
            backend.close()
    log = ROOT / "logs" / "verify_part_switches.json"
    log.write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    print(f"written: {log}")
    ok = all(r["status"] == "success" for r in out["runs"])
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
