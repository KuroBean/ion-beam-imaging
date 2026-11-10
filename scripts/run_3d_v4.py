"""Mesh and solve the 3D model with the real lens assembly (lens8newMCP_ks_v4_lens_voltages.mph, edited in place).

Mesh budget goes where the ions fly; all selections are named/geometric so they survive geometry changes.
  fine
    * sel_apertures: L1..L9 faces reaching r < R_AP (apertures, inner rings, back faces, accelerator
      webs: they bound the gaps where the lens field reaches the axis) + deflector tubes -> H_AP
      (dropping the L1..L4 back faces made the energy error -0.6 -> -1.4 eV and killed transmission;
      including the deflector plate faces cost ~0.8M elements for nothing)
    * sel_needle_tip: needle cone + tip face                            -> H_TIP, slow growth (HGRAD_TIP)
      (the ions are slowest between tip and L1; coarse field there = spurious energy, v2: ~+13 eV)
    * MCP front face (geom1_sel3): -1 kV screen -> -10 kV MCP decides the landing position -> H_MCP
  coarse
    * all lens-assembly surfaces (H_ASM_BND, relaxed curvature): the many small holes/slots/pockets off
      the axis otherwise force ~0.7 mm elements through every plate and gap
    * inside the lens-assembly solids ('Size 5 lenses'): conductors, every boundary held at a fixed
      potential -> interior field irrelevant                           -> H_SOLID
    * needle shank                                                      -> H_SHANK

Stages (run in order):
  mesh       selections + size nodes, mesh, save
  es         solve Study 1 (electrostatics), save
  particles  particle tracing (Study 2) to T_END, save

Usage:  .venv\\Scripts\\python.exe scripts\\run_3d_v4.py mesh|es|particles
"""
import sys
import time

import jpype

from comsol_session import PROJECT_DIR, load, start

MODEL = PROJECT_DIR / "lens8newMCP_ks_v4_lens_voltages.mph"
R_AP = 7.0           # mm; L1..L9 faces reaching inside this radius (aperture r 5)
R_DEFL = 7.0         # mm; deflector faces lying entirely inside this radius (tubes r 5..6.5)
H_AP, HGRAD = "0.6", "1.3"
H_TIP, HGRAD_TIP = "0.15", "1.2"
H_TIPFACE, HGRAD_TIPFACE = "0.03", "1.15"   # the field drops ~58 V in the first mm: 0.15 mm there gave
                                            # -1.4..-4.6 eV energy error (mesh-dependent); 2D uses 0.02
H_SHANK = "0.5"
H_MCP = "1.0"
H_SOLID = {"hmax": "3", "hmin": "0.5", "hgrad": "1.6", "hcurve": "0.8", "hnarrow": "0.3"}
# all lens-assembly surfaces: the small off-axis holes/slots/pockets must not force fine elements
H_ASM_BND = {"hmax": "3", "hmin": "0.8", "hgrad": "1.5", "hcurve": "2", "hnarrow": "0.3"}
T_END = "250e-6"


def _sel(comp, tag, typ):
    if tag not in [str(t) for t in comp.selection().tags()]:
        comp.selection().create(tag, typ)
    return comp.selection(tag)


def _size(ft, tag, label, named, dim, **kw):
    if tag not in [str(t) for t in ft.feature().tags()]:
        ft.create(tag, "Size")
    z = ft.feature(tag)
    z.label(label)
    z.selection().geom("geom1", dim)
    z.selection().named(named)
    z.set("custom", "on")
    for k, v in kw.items():
        z.set(k, v)
        z.set(k + "active", True)
    return z


def stage_mesh(client):
    model = load(client, MODEL)
    j = model.java
    comp = j.component("comp1")
    par = j.param()
    tip = par.evaluate("tip_z") * 1e3
    z_end = (par.evaluate("tip_z") + par.evaluate("lens_gap")) * 1e3 + 136.165 + 1.0
    S = jpype.JArray(jpype.JString)

    # L1..L9: every face that reaches r < R_AP (apertures, inner rings, the back faces r 5..12 and the
    # accelerator webs that bound the inter-electrode gaps where the lens field reaches the axis).
    # Deflectors: only faces lying entirely inside R_DEFL (tubes), not the 65 mm plate faces.
    z_l9 = (par.evaluate("tip_z") + par.evaluate("lens_gap")) * 1e3 + 136.165 - 42.325 + 15.0 + 0.5
    c = _sel(comp, "cyl_beam", "Cylinder")
    c.label(f"Boundaries reaching r < {R_AP} mm (tip..end of L9)")
    c.set("entitydim", jpype.JInt(2))
    c.set("r", str(R_AP))
    c.set("bottom", f"{tip:.4f}")
    c.set("top", f"{z_l9:.4f}")
    c.set("condition", "intersects")
    cd = _sel(comp, "cyl_defl", "Cylinder")
    cd.label(f"Boundaries entirely within r < {R_DEFL} mm (deflector region)")
    cd.set("entitydim", jpype.JInt(2))
    cd.set("r", str(R_DEFL))
    cd.set("bottom", f"{z_l9 - 1.0:.4f}")
    cd.set("top", f"{z_end:.4f}")
    cd.set("condition", "inside")
    cu = _sel(comp, "cyl_beam_all", "Union")
    cu.label("Beam-region boundaries (lenses + deflector tubes)")
    cu.set("entitydim", jpype.JInt(2))
    cu.set("input", S(["cyl_beam", "cyl_defl"]))
    a = _sel(comp, "adj_asm", "Adjacent")
    a.label("Lens assembly boundaries")
    a.set("input", S(["geom1_uni6_dom"]))
    a.set("outputdim", jpype.JInt(2))
    s = _sel(comp, "sel_apertures", "Intersection")
    s.label("sel_apertures (lens assembly near the beam axis)")
    s.set("entitydim", jpype.JInt(2))
    s.set("input", S(["cyl_beam_all", "adj_asm"]))
    b = _sel(comp, "box_tip", "Box")
    b.label("Boundaries fully inside the needle cone/tip box")
    b.set("entitydim", jpype.JInt(2))
    for k, v in (("xmin", -1), ("xmax", 1), ("ymin", -1), ("ymax", 1), ("zmin", tip - 10.5), ("zmax", tip + 0.5)):
        b.set(k, str(v))
    b.set("condition", "inside")
    t = _sel(comp, "sel_needle_tip", "Intersection")
    t.label("sel_needle_tip (needle cone + tip face)")
    t.set("entitydim", jpype.JInt(2))
    t.set("input", S(["box_tip", "adj5"]))
    bf = _sel(comp, "box_tipface", "Box")
    bf.label("Boundaries fully inside a box around the tip face")
    bf.set("entitydim", jpype.JInt(2))
    for k, v in (("xmin", -0.15), ("xmax", 0.15), ("ymin", -0.15), ("ymax", 0.15),
                 ("zmin", tip - 0.01), ("zmax", tip + 0.01)):
        bf.set(k, str(v))
    bf.set("condition", "inside")
    tf = _sel(comp, "sel_tipface", "Intersection")
    tf.label("sel_tipface (needle tip face, particle release)")
    tf.set("entitydim", jpype.JInt(2))
    tf.set("input", S(["box_tipface", "adj5"]))

    ft = comp.mesh("mesh1").feature("ftet4")
    z5 = ft.feature("size5")                       # 'Size 5 lenses' (lens-assembly domains)
    z5.set("custom", "on")
    for k, v in H_SOLID.items():
        z5.set(k, v)
        z5.set(k + "active", True)
    _size(ft, "size_asm", "Lens assembly surfaces (coarse, ignore small off-axis features)", "adj_asm", 2,
          **H_ASM_BND)
    _size(ft, "size_ap", "Beam region: lens apertures", "sel_apertures", 2, hmax=H_AP, hgrad=HGRAD)
    order = [str(x) for x in ft.feature().tags()]           # later size nodes win: keep size_asm before size_ap
    if order.index("size_asm") > order.index("size_ap"):
        ft.feature().move("size_asm", order.index("size_ap"))
    _size(ft, "size_needle", "Needle shank", "adj5", 2, hmax=H_SHANK, hgrad=HGRAD)
    _size(ft, "size_tip", "Beam region: needle cone + tip", "sel_needle_tip", 2, hmax=H_TIP, hgrad=HGRAD_TIP)
    _size(ft, "size_tipface", "Beam region: needle tip face", "sel_tipface", 2, hmax=H_TIPFACE,
          hgrad=HGRAD_TIPFACE)
    _size(ft, "size_mcp", "Beam region: MCP front face", "geom1_sel3", 2, hmax=H_MCP, hgrad=HGRAD)

    t0 = time.time()
    comp.geom("geom1").run()
    for tag in ("sel_apertures", "sel_needle_tip", "sel_tipface", "geom1_sel3"):
        print(f"{tag}: {len(list(comp.selection(tag).entities(2)))} boundaries", flush=True)
    print(f"size nodes: {[str(x) for x in ft.feature().tags()]}", flush=True)
    t0 = time.time()
    mesh = comp.mesh("mesh1")
    mesh.run()
    print(f"mesh: {mesh.getNumElem()} elements, {mesh.getNumVertex()} vertices ({time.time()-t0:.0f} s)", flush=True)
    model.save(str(MODEL))
    print(f"saved {MODEL.name}", flush=True)


def stage_es(client):
    model = load(client, MODEL)
    t = time.time()
    model.java.study("std1").run()
    print(f"std1 (electrostatics) solved in {time.time()-t:.0f} s", flush=True)
    model.save(str(MODEL))
    print(f"saved {MODEL.name}", flush=True)


def stage_particles(client):
    model = load(client, MODEL)
    j = model.java
    j.study("std2").feature("time").set("tlist", f"range(0,0.5[us],{float(T_END)*1e6:g}[us])")
    j.sol("sol2").feature("t1").set("tlist", f"range(0,0.5e-6,{T_END})")
    t = time.time()
    j.sol("sol2").runAll()
    print(f"std2 (particles) solved in {time.time()-t:.0f} s", flush=True)
    model.save(str(MODEL))
    print(f"saved {MODEL.name}", flush=True)


if __name__ == "__main__":
    stage = sys.argv[1]
    c = start()
    {"mesh": stage_mesh, "es": stage_es, "particles": stage_particles}[stage](c)
    c.clear()
