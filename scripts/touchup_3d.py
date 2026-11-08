"""Touch up the 3D model (saved to a NEW file; the original is never written).

Changes
  * MCP holder (domain 9) -> Ultem 1000 (eps_r = 3.15) instead of 304L
  * L_dom fixed so the domain contains chamber 2 also for cfg = 2
    (value for cfg = 3 is unchanged)
  * local mesh refinement on the lens-aperture surfaces and the needle so the
    field near the beam axis is resolved (the coarse field made the particle
    tracer gain ~+13 eV of spurious energy)
  * particle tracing extended to 250 us (with correct energy the ions reach
    the MCP at ~210-220 us)

Stages (run in order; each loads the output of the previous one):
  mesh       apply model changes, remesh, save
  es         solve Study 1 (electrostatics), save
  ptest      100-particle / 10-us energy-conservation test (not saved)
  particles  full particle tracing (Study 2), save

Usage:  .venv\\Scripts\\python.exe scripts\\touchup_3d.py mesh|es|ptest|particles
"""
import sys
import time

import jpype
import numpy as np

from comsol_session import MODEL_FILE, PROJECT_DIR, load, start

OUT_FILE = PROJECT_DIR / "lens8newMCP_ks_v3_touchup.mph"

HOLDER_DOMAIN = 9
LENS_APERTURE_BNDS = [490, 491, 492, 493, 494, 495, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523,
                      524, 525, 530, 531, 532, 533, 534, 535, 558, 559, 560, 561, 754, 755, 756, 757, 758, 759,
                      760, 761, 769, 770, 775, 776, 784, 785, 786, 787, 788, 789, 790, 791]
NEEDLE_BNDS = [574, 575, 576, 577, 578, 615, 771, 772, 773, 774]
H_LENS, H_NEEDLE, HGRAD = "0.5", "0.15", "1.25"
T_END = "250e-6"


def iarr(v):
    return jpype.JArray(jpype.JInt)([int(x) for x in v])


def stage_mesh(client):
    model = load(client, MODEL_FILE)
    j = model.java
    comp = j.component("comp1")

    # --- Ultem holder ---
    mat1 = comp.material("mat1")
    mat1.selection().remove(iarr([HOLDER_DOMAIN]))
    if "mat_ultem" not in [str(t) for t in comp.material().tags()]:
        mu = comp.material().create("mat_ultem", "Common")
    mu = comp.material("mat_ultem")
    mu.label("Ultem 1000 (PEI) - MCP holder")
    mu.propertyGroup("def").set("relpermittivity",
                                jpype.JArray(jpype.JString)(["3.15", "0", "0", "0", "3.15", "0", "0", "0", "3.15"]))
    mu.selection().set(iarr([HOLDER_DOMAIN]))
    print("holder material -> Ultem (eps_r 3.15)", flush=True)

    # --- L_dom fix (cfg 2 domain too short) ---
    old = j.param().get("L_dom")
    j.param().set("L_dom", "if(cfg==1,L_c1,z_c2+2*z_c2_center)+0.1[m]",
                  "domain length (fixed so chamber 2 fits for cfg 2)")
    print(f"L_dom: '{old}' -> '{j.param().get('L_dom')}'", flush=True)

    # --- local mesh refinement ---
    ft = comp.mesh("mesh1").feature("ftet4")
    for tag, bnds, h, label in (("size_lensap", LENS_APERTURE_BNDS, H_LENS, "Beam region: lens apertures"),
                                ("size_needle", NEEDLE_BNDS, H_NEEDLE, "Beam region: needle")):
        if tag not in [str(t) for t in ft.feature().tags()]:
            ft.create(tag, "Size")
        s = ft.feature(tag)
        s.label(label)
        s.selection().geom("geom1", 2)
        s.selection().set(iarr(bnds))
        s.set("custom", "on")
        s.set("hmax", h)
        s.set("hmaxactive", True)
        s.set("hgrad", HGRAD)
        s.set("hgradactive", True)

    t = time.time()
    geom = comp.geom("geom1")
    geom.run()
    nb = geom.getNBoundaries()
    print(f"geometry rebuilt: {geom.getNDomains()} domains, {nb} boundaries ({time.time()-t:.0f} s)", flush=True)
    # sanity check: boundary numbering unchanged -> refinement targets are still lens/needle faces
    pot3 = set(int(b) for b in comp.physics("es").feature("pot3").selection().entities(2))
    pot4 = set(int(b) for b in comp.physics("es").feature("pot4").selection().entities(2))
    gnd2 = set(int(b) for b in comp.physics("es").feature("gnd2").selection().entities(2))
    assert nb == 1521, "boundary count changed - check refinement selections"
    assert set(LENS_APERTURE_BNDS) <= (pot3 | pot4) and set(NEEDLE_BNDS) <= gnd2, "selection mismatch"

    t = time.time()
    mesh = comp.mesh("mesh1")
    mesh.run()
    print(f"mesh: {mesh.getNumElem()} elements, {mesh.getNumVertex()} vertices ({time.time()-t:.0f} s)", flush=True)
    model.save(str(OUT_FILE))
    print(f"saved {OUT_FILE.name}", flush=True)


def stage_es(client):
    model = load(client, OUT_FILE)
    t = time.time()
    model.java.study("std1").run()
    print(f"std1 (electrostatics) solved in {time.time()-t:.0f} s", flush=True)
    model.save(str(OUT_FILE))
    print(f"saved {OUT_FILE.name}", flush=True)


def stage_ptest(client):
    from tune_3d_timestepping import energy_report
    model = load(client, OUT_FILE)
    j = model.java
    j.component("comp1").physics("cpt").feature("pbeam1").set("N", "100")
    j.sol("sol2").feature("t1").set("tlist", "range(0,0.5e-6,10e-6)")
    t = time.time()
    j.sol("sol2").runAll()
    energy_report(model, "refined mesh", time.time() - t)


def stage_particles(client):
    model = load(client, OUT_FILE)
    j = model.java
    j.study("std2").feature("time").set("tlist", f"range(0,0.5[us],{float(T_END)*1e6:g}[us])")
    j.sol("sol2").feature("t1").set("tlist", f"range(0,0.5e-6,{T_END})")
    t = time.time()
    j.sol("sol2").runAll()
    print(f"std2 (particles) solved in {time.time()-t:.0f} s", flush=True)
    model.save(str(OUT_FILE))
    print(f"saved {OUT_FILE.name}", flush=True)


if __name__ == "__main__":
    stage = sys.argv[1]
    c = start()
    {"mesh": stage_mesh, "es": stage_es, "ptest": stage_ptest, "particles": stage_particles}[stage](c)
    c.clear()
