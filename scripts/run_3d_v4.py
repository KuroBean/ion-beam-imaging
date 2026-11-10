"""Mesh and solve the 3D model with the real lens assembly (lens8newMCP_ks_v4_lens_voltages.mph, edited in place).

Same refinement idea as touchup_3d.py, but on selections that survive geometry changes:
  * sel_apertures: lens-assembly boundaries within r < R_AP of the beam axis (apertures, inner rings,
    accelerator webs, deflector tubes) -> hmax H_AP
  * needle (adj5 'sel_needle') -> hmax H_NEEDLE
Without this the coarse field near the axis makes the particle tracer gain spurious energy (v2: ~+13 eV).

Stages (run in order):
  mesh       add selections + size nodes, mesh, save
  es         solve Study 1 (electrostatics), save
  particles  particle tracing (Study 2) to T_END, save

Usage:  .venv\\Scripts\\python.exe scripts\\run_3d_v4.py mesh|es|particles
"""
import sys
import time

import jpype

from comsol_session import PROJECT_DIR, load, start

MODEL = PROJECT_DIR / "lens8newMCP_ks_v4_lens_voltages.mph"
R_AP = 7.0           # mm; aperture radius is 5 mm, deflector tube 5..6.5 mm
H_AP, H_NEEDLE, HGRAD = "0.6", "0.15", "1.3"
T_END = "250e-6"


def stage_mesh(client):
    model = load(client, MODEL)
    j = model.java
    comp = j.component("comp1")
    par = j.param()
    tip = par.evaluate("tip_z") * 1e3
    z_end = (par.evaluate("tip_z") + par.evaluate("lens_gap")) * 1e3 + 136.165 + 1.0
    sel = comp.selection()
    tags = [str(t) for t in sel.tags()]
    if "cyl_beam" not in tags:
        sel.create("cyl_beam", "Cylinder")
    c = comp.selection("cyl_beam")
    c.label(f"Boundaries within r < {R_AP} mm of the axis (tip..assembly end)")
    c.set("entitydim", jpype.JInt(2))
    c.set("r", str(R_AP))
    c.set("bottom", f"{tip:.4f}")
    c.set("top", f"{z_end:.4f}")
    c.set("condition", "intersects")
    if "adj_asm" not in tags:
        sel.create("adj_asm", "Adjacent")
    a = comp.selection("adj_asm")
    a.label("Lens assembly boundaries")
    a.set("input", jpype.JArray(jpype.JString)(["geom1_uni6_dom"]))
    a.set("outputdim", jpype.JInt(2))
    if "sel_apertures" not in tags:
        sel.create("sel_apertures", "Intersection")
    s = comp.selection("sel_apertures")
    s.label("sel_apertures (lens assembly near the beam axis)")
    s.set("entitydim", jpype.JInt(2))
    s.set("input", jpype.JArray(jpype.JString)(["cyl_beam", "adj_asm"]))

    ft = comp.mesh("mesh1").feature("ftet4")
    for tag, named, h, label in (("size_ap", "sel_apertures", H_AP, "Beam region: lens apertures"),
                                 ("size_needle", "adj5", H_NEEDLE, "Beam region: needle")):
        if tag not in [str(t) for t in ft.feature().tags()]:
            ft.create(tag, "Size")
        z = ft.feature(tag)
        z.label(label)
        z.selection().geom("geom1", 2)
        z.selection().named(named)
        z.set("custom", "on")
        z.set("hmax", h)
        z.set("hmaxactive", True)
        z.set("hgrad", HGRAD)
        z.set("hgradactive", True)

    t = time.time()
    comp.geom("geom1").run()
    n_ap = len(list(comp.selection("sel_apertures").entities(2)))
    print(f"geometry rebuilt ({time.time()-t:.0f} s); sel_apertures: {n_ap} boundaries", flush=True)
    t = time.time()
    mesh = comp.mesh("mesh1")
    mesh.run()
    print(f"mesh: {mesh.getNumElem()} elements, {mesh.getNumVertex()} vertices ({time.time()-t:.0f} s)", flush=True)
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
