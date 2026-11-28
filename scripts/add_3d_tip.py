"""Give the 3D model a tip potential parameter v_tip (one-off edit, saved to a NEW file).

v5 grounds the needle (es/gnd2 'Ground needle' on selection adj5). This adds the global parameter
v_tip = 0[V] (same name as the 2D model), a new ElectricPotential es/pot_tip on the same named
selection with V0 = v_tip, and disables gnd2. With v_tip = 0 the physics is unchanged, so the
stored mesh and solutions stay valid. The input is never saved; an existing output is never
overwritten.

Usage:  .venv\\Scripts\\python.exe scripts\\add_3d_tip.py [in.mph] [out.mph]
        (defaults: models.3d from config/paths.yaml -> lens8newMCP_ks_v6_tip.mph next to it)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from introspect_models import setup_mph, tags  # noqa: E402
from ionopt.config import load_config  # noqa: E402

NEEDLE_SEL = "adj5"


def main():
    cfg = load_config(ROOT / "config")
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else cfg.path("models.3d")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name("lens8newMCP_ks_v6_tip.mph")
    if out.resolve() == src.resolve() or out.exists():
        sys.exit(f"refusing to overwrite {out}")
    mph = setup_mph(cfg.paths.comsol_root)
    client = mph.start()
    t = time.time()
    model = client.load(str(src))
    print(f"loaded {src.name} in {time.time() - t:.0f} s", flush=True)
    j = model.java
    es = j.component("comp1").physics("es")

    # ---- checks
    if "v_tip" in [str(n) for n in j.param().varnames()]:
        sys.exit("ABORT: parameter v_tip already exists")
    if "pot_tip" in tags(es.feature()):
        sys.exit("ABORT: es/pot_tip already exists")
    g = es.feature("gnd2")
    if str(g.getType()) != "Ground" or "needle" not in str(g.label()).lower() or str(g.selection().named()) != NEEDLE_SEL:
        sys.exit(f"ABORT: es/gnd2 is {g.getType()} '{g.label()}' on {g.selection().named()!r}, expected Ground needle on {NEEDLE_SEL}")
    lab = str(j.component("comp1").selection(NEEDLE_SEL).label())
    print(f"check ok  es/gnd2 '{g.label()}' on {NEEDLE_SEL} ('{lab}'), active={g.isActive()}", flush=True)

    # ---- edits
    j.param().set("v_tip", "0[V]", "tip (needle) potential")
    p = es.create("pot_tip", "ElectricPotential", 2)
    p.label("Needle (tip) potential")
    p.selection().named(NEEDLE_SEL)
    p.set("V0", "v_tip")
    g.active(False)

    # ---- verify
    assert str(p.selection().named()) == NEEDLE_SEL and str(p.getString("V0")) == "v_tip"
    assert float(j.param().evaluate("v_tip")) == 0.0 and not g.isActive()
    print(f"set       es/pot_tip on {NEEDLE_SEL}, V0 = v_tip (0 V); es/gnd2 disabled", flush=True)
    t = time.time()
    model.save(str(out))
    print(f"saved {out.name} in {time.time() - t:.0f} s (input {src.name} not saved)", flush=True)
    client.remove(model)


if __name__ == "__main__":
    main()
