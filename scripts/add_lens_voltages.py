"""Finish the physics for the imported lens assembly in the 3D model (one-off edit, saved to a NEW file).

Adds to the user's GUI-edited v2 model:
  * parameters L1_v..L9_v, D1a_v..D2b_v (values = what the potential nodes had), and lens_gap
  * Electric Potential nodes for L1..L9 / deflectors use those parameters
  * particle Freeze walls for every electrode (L1..L3 already existed), the rods and the bracket
  * Ground on the rods + bracket (grounded in the real assembly)
  * Move of the lens assembly: new z = tip_z + lens_gap (was tip_z+13.482)

Usage:  .venv\\Scripts\\python.exe scripts\\add_lens_voltages.py [out.mph]
"""
import sys

import jpype

from comsol_session import MODEL_FILE, PROJECT_DIR, load, start

OUT_FILE = PROJECT_DIR / "lens8newMCP_ks_v4_lens_voltages.mph"

# label, import selection index (imp8 Imported1_k), potential node, existing wall node (or None), default value
ELECTRODES = [
    ("L1", 8, "pot3", "wall2", "-120[V]"),
    ("L2", 6, "pot9", "wall4", "-40[V]"),
    ("L3", 7, "pot10", "wall9", "-40[V]"),
    ("L4", 9, "pot11", None, "-40[V]"),
    ("L5", 1, "pot12", None, "-40[V]"),
    ("L6", 4, "pot13", None, "-40[V]"),
    ("L7", 2, "pot14", None, "-40[V]"),
    ("L8", 5, "pot15", None, "-40[V]"),
    ("L9", 3, "pot16", None, "0[V]"),
    ("D1a", 14, "pot17", None, "0[V]"),
    ("D1b", 17, "pot18", None, "0[V]"),
    ("D2a", 16, "pot19", None, "0[V]"),
    ("D2b", 15, "pot20", None, "0[V]"),
]
BRACKET = 18


def bnd(k):
    return f"geom1_imp8_Imported1_{k}_bnd"


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else str(OUT_FILE)
    client = start()
    model = load(client, MODEL_FILE)
    j = model.java
    comp = j.component("comp1")
    es, cpt = comp.physics("es"), comp.physics("cpt")
    par = j.param()

    # --- lens gap ---
    par.set("lens_gap", "13.482[mm]", "needle tip to L1 entrance face (front plane closest to the tip)")
    mov = comp.geom("geom1").feature("mov7")
    old = mov.getString("newposz")
    mov.set("newposz", "tip_z+lens_gap")
    print(f"mov7 newposz: {old} -> tip_z+lens_gap")

    # --- voltages + walls ---
    for name, k, pot, wall, default in ELECTRODES:
        p = f"{name}_v"
        f = es.feature(pot)
        assert str(f.selection().named()) == bnd(k), (pot, f.selection().named())
        cur = str(f.getString("V0"))
        if p == "L1_v":   # already a parameter in the user's model; keep its value
            default = par.get("L1_v")
        par.set(p, default, f"{name} potential")
        f.set("V0", p)
        print(f"{pot:6s} {name:4s} V0: {cur} -> {p} = {par.get(p)}")
        wtag = wall or f"wall_{name}"
        if wall is None:
            w = cpt.create(wtag, "Wall", 2)
            w.label(f"{name} Walls")
            w.selection().named(bnd(k))
        w = cpt.feature(wtag)
        w.set("WallCondition", "Freeze")
        assert str(w.selection().named()) == bnd(k)

    # --- rods + bracket: grounded conductors ---
    sel = comp.selection()
    if "adj_rods" not in [str(t) for t in sel.tags()]:
        a = sel.create("adj_rods", "Adjacent")
    a = comp.selection("adj_rods")
    a.label("sel_rods (boundaries)")
    a.set("input", jpype.JArray(jpype.JString)(["geom1_unisel2"]))
    a.set("outputdim", jpype.JInt(2))
    if "sel_asm_gnd" not in [str(t) for t in sel.tags()]:
        sel.create("sel_asm_gnd", "Union")
    u = comp.selection("sel_asm_gnd")
    u.label("sel_rods_bracket (grounded)")
    u.set("entitydim", jpype.JInt(2))
    u.set("input", jpype.JArray(jpype.JString)(["adj_rods", bnd(BRACKET)]))
    g = es.create("gnd_asm", "Ground", 2)
    g.label("Ground rods and bracket")
    g.selection().named("sel_asm_gnd")
    w = cpt.create("wall_asm", "Wall", 2)
    w.label("Rods and bracket Walls")
    w.selection().named("sel_asm_gnd")
    w.set("WallCondition", "Freeze")
    # L9's potential must win on any face it shares with the bracket (L9 is insulated in reality):
    # features lower in the list override, so move pot16 below the new ground.
    es.feature().move("pot16", len(list(es.feature().tags())) - 1)

    # --- checks ---
    geom = comp.geom("geom1")
    geom.run()
    print(f"geometry: {geom.getNDomains()} domains, {geom.getNBoundaries()} boundaries")
    print("mov7 newposz evaluates to", par.evaluate("tip_z+lens_gap") * 1e3, "mm")
    for name, k, *_ in ELECTRODES:
        n = len(list(comp.selection(bnd(k)).entities(2)))
        print(f"  {name:4s} {bnd(k)}: {n} boundaries")
    rods = set(comp.selection("adj_rods").entities(2))
    brk = set(comp.selection(bnd(BRACKET)).entities(2))
    l9 = set(comp.selection(bnd(3)).entities(2))
    print(f"  rods {len(rods)} bnd, bracket {len(brk)} bnd, ground total {len(comp.selection('sel_asm_gnd').entities(2))}")
    print(f"  faces shared bracket/L9: {sorted(brk & l9)}; rods touching electrodes: "
          f"{sorted(rods & set().union(*(set(comp.selection(bnd(k)).entities(2)) for _, k, *_ in ELECTRODES)))}")
    ccn = es.feature("ccn1")
    try:
        print("ccn1 permittivity source:", ccn.getString("epsilonr_mat"))
    except Exception as e:
        print("ccn1 permittivity source: ?", e)
    covered = set()
    for t in comp.material().tags():
        covered |= set(comp.material(t).selection().entities(3))
    alld = set(range(1, geom.getNDomains() + 1))
    print(f"domains without a material: {sorted(alld - covered)}")
    print("es features:", [str(t) for t in es.feature().tags()])
    model.save(out)
    print(f"saved {out}")
    client.clear()


if __name__ == "__main__":
    main()


