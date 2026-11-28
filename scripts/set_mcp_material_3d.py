"""Make the 3D MCP plate lead glass and save the model WITH a built mesh (one-off edit, author OK 2026-11-12).

After the author's mesh_gap GUI edit, the 'dom_holder' selection (geom1_sel12_dom, material ULTEM)
also covers the MCP plate (via uni7 'mcp and holder'), so the plate became ULTEM. This script:
  * adds a geometric Box selection sel_mcp_plate (domains inside r <= 20.5 mm, mcp_z..mcp_z+5.9 mm),
  * adds a Difference selection sel_holder_noplate = geom1_sel12_dom minus sel_mcp_plate and moves
    mat6 (ULTEM) onto it,
  * puts mat3 'Leaded 1' (eps_r 8, otherwise unused) on sel_mcp_plate,
  * builds geometry and mesh, checks the effective materials, and saves.

Material precedence: the last material in the tree wins; mat1 (304L default) is before mat3, mat6
no longer contains the plate, mat7/mat8 (Al2O3) do not touch it.

Usage:  .venv\\Scripts\\python.exe scripts\\set_mcp_material_3d.py [model.mph] [--out other.mph]
        (default: models.3d, saved IN PLACE as agreed with the author; copy it first)
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from introspect_models import setup_mph, tags  # noqa: E402
from ionopt.config import load_config  # noqa: E402

PLATE_SEL, HOLDER_SEL, HOLDER_SRC = "sel_mcp_plate", "sel_holder_noplate", "geom1_sel12_dom"
MAT_GLASS, MAT_ULTEM = "mat3", "mat6"
PLATE_THICK_MM = 5.9           # MCP front face (mcp_z) to back face, measured: 515.9 -> 521.8 mm


def effective(comp, dom: int) -> str:
    who = None
    for mt in tags(comp.material()):
        if dom in {int(e) for e in comp.material(mt).selection().entities(3)}:
            who = mt
    return who


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model", nargs="?")
    ap.add_argument("--out")
    a = ap.parse_args()
    cfg = load_config(ROOT / "config")
    src = Path(a.model) if a.model else cfg.path("models.3d")
    out = Path(a.out) if a.out else src
    mph = setup_mph(cfg.paths.comsol_root)
    client = mph.start()
    t = time.time()
    model = client.load(str(src))
    print(f"loaded {src.name} in {time.time() - t:.0f} s", flush=True)
    j = model.java
    comp = j.component("comp1")

    # ---- checks
    m3, m6 = comp.material(MAT_GLASS), comp.material(MAT_ULTEM)
    eps3 = [str(x) for x in m3.propertyGroup("def").getStringArray("relpermittivity")]
    if "Leaded" not in str(m3.label()) or eps3 != ["8"]:
        sys.exit(f"ABORT: {MAT_GLASS} is '{m3.label()}' eps {eps3}, expected Leaded glass eps 8")
    if "ULTEM" not in str(m6.label()) or str(m6.selection().named()) != HOLDER_SRC:
        sys.exit(f"ABORT: {MAT_ULTEM} is '{m6.label()}' on {m6.selection().named()!r}, expected ULTEM on {HOLDER_SRC}")
    existing = tags(comp.selection())
    if PLATE_SEL in existing or HOLDER_SEL in existing:
        sys.exit(f"ABORT: {PLATE_SEL} or {HOLDER_SEL} already exists")

    t = time.time()
    comp.geom("geom1").run()
    print(f"geometry built in {time.time() - t:.0f} s: {comp.geom('geom1').getNDomains()} domains", flush=True)

    # ---- edits
    b = comp.selection().create(PLATE_SEL, "Box")
    b.label("MCP plate (geometric box)")
    b.set("entitydim", "3")
    b.set("condition", "inside")
    for k, v in (("xmin", "-20.5[mm]"), ("xmax", "20.5[mm]"), ("ymin", "-20.5[mm]"), ("ymax", "20.5[mm]"),
                 ("zmin", "mcp_z-0.05[mm]"), ("zmax", f"mcp_z+{PLATE_THICK_MM + 0.05}[mm]")):
        b.set(k, v)
    plate = [int(e) for e in b.entities(3)]
    if len(plate) != 1:
        sys.exit(f"ABORT: {PLATE_SEL} selects {plate}, expected exactly one domain (the MCP plate)")
    d = comp.selection().create(HOLDER_SEL, "Difference")
    d.label("MCP holder without the plate")
    d.set("entitydim", "3")
    import jpype
    d.set("add", jpype.JArray(jpype.JString)([HOLDER_SRC]))
    d.set("subtract", jpype.JArray(jpype.JString)([PLATE_SEL]))
    holder = [int(e) for e in d.entities(3)]
    m6.selection().named(HOLDER_SEL)
    m3.selection().named(PLATE_SEL)
    print(f"plate domain {plate}; ULTEM now on {HOLDER_SEL} {holder}", flush=True)

    t = time.time()
    comp.mesh("mesh1").run()
    print(f"mesh built in {time.time() - t:.0f} s: {comp.mesh('mesh1').getNumElem()} elements", flush=True)

    # ---- verify effective materials
    eff_plate = effective(comp, plate[0])
    eff_holder = {dom: effective(comp, dom) for dom in holder}
    print(f"effective: plate -> {eff_plate}; holder domains -> {eff_holder}", flush=True)
    if eff_plate != MAT_GLASS:
        sys.exit(f"ABORT (not saved): the plate's effective material is {eff_plate}")

    t = time.time()
    model.save(str(out))
    print(f"saved {out.name} in {time.time() - t:.0f} s", flush=True)
    client.remove(model)


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Total {time.time() - t0:.0f} s")
