"""Build a 2D axisymmetric (r, z) version of the 3D ion-beam lens model.

The z axis is the beam axis.  Dimensions come from the 3D model
(see logs/boundary_table.csv produced by boundary_table.py):

  * needle, MCP plate/holder, screen-mesh disc: taken directly (axisymmetric in 3D)
  * lens assembly (L1..L9 = 4 lens + 5 accelerator plates, deflector pairs D1/D2): r-z
    profiles of the real STEP parts, positioned by lens_gap; the deflectors are
    deleted for cfg 1 and 2 (If node), as in the 3D model
  * chamber 1 (tube) and chamber 2 (sphere): idealised as bodies of revolution
    with the 3D inner/outer radii; side ports and small flange features dropped
  * NOT representable in 2D-axisymmetry (omitted): screen-mesh cross arms,
    four polyimide posts, small holder tabs/bosses, chamber side ports,
    lens-assembly rods and bracket (grounded), the split of each deflector into halves

Conductors are domains excluded from the physics (their edges carry the
potential / ground); the MCP plate, its Ultem holder and the polyimide ring are
kept as dielectric domains.  The screen mesh is an idealised transparent
-1 kV disc (mesh resolution unknown).

Usage:
  .venv\\Scripts\\python.exe scripts\\build_axisym.py [--solve] [--particles] [--out file.mph]
"""
import argparse
import time

import jpype

from comsol_session import PROJECT_DIR, start

OUT_DEFAULT = PROJECT_DIR / "lens8_axisym.mph"
RELEASE_FILE = PROJECT_DIR / "data" / "release_from_3d.txt"

PARAMS = [
    # name, expression, description  (same names as the 3D model where possible)
    ("cfg", "3", "1: tube chamber only, 2: sphere chamber only, 3: tube + sphere"),
    ("L_c1", "300[mm]", "chamber 1 (tube) reference length"),
    ("z_c2", "if(cfg==3,L_c1,0[mm])", "z of chamber 2 input flange face"),
    ("z_c2_center", "215.9[mm]", "chamber 2 sphere centre, relative to its flange face"),
    ("z_mcp_c1", "250[mm]", "MCP face z for cfg 1"),
    ("mcp_z", "if(cfg==1,z_mcp_c1,z_c2+z_c2_center)", "z coord of MCP front face"),
    ("z_end", "if(cfg==1,L_c1,z_c2+2*z_c2_center)", "z of last chamber flange face"),
    ("z_dom0", "-50[mm]", "domain start z"),
    ("z_dom1", "z_end+50[mm]", "domain end z"),
    ("r_dom", "175[mm]", "domain radius (3D bounding cylinder)"),
    # source
    ("tip_z", "105[mm]", "needle tip z (particle release)"),
    ("tip_base_z", "65[mm]", "needle base z"),
    ("r_needle", "0.5[mm]", "needle shank radius"),
    ("r_tip", "0.1[mm]", "needle tip flat radius"),
    ("L_cone", "10[mm]", "needle cone length"),
    # lens assembly (real part, "lens assembly stripped with rods.STEP"; same names as the 3D model)
    ("lens_gap", "13.482[mm]", "needle tip to L1 entrance face (front plane closest to the tip)"),
    ("z_asm", "tip_z+lens_gap+136.165[mm]", "model z of the assembly CAD origin (L1 front is at CAD z = -136.165 mm)"),
    ("L1_v", "-120[V]", "L1 potential"),
    ("L2_v", "-40[V]", "L2 potential"),
    ("L3_v", "-40[V]", "L3 potential"),
    ("L4_v", "-40[V]", "L4 potential"),
    ("L5_v", "-40[V]", "L5 potential"),
    ("L6_v", "-40[V]", "L6 potential"),
    ("L7_v", "-40[V]", "L7 potential"),
    ("L8_v", "-40[V]", "L8 potential"),
    ("L9_v", "0[V]", "L9 potential"),
    ("D1a_v", "0[V]", "deflector 1 half a potential (2D uses the mean of a and b)"),
    ("D1b_v", "0[V]", "deflector 1 half b potential"),
    ("D2a_v", "0[V]", "deflector 2 half a potential (2D uses the mean of a and b)"),
    ("D2b_v", "0[V]", "deflector 2 half b potential"),
    # MCP / screen
    ("V_mcp_front", "-10000[V]", "MCP front potential"),
    ("V_mcp_back", "-5000[V]", "MCP back potential"),
    ("V_screen", "-1000[V]", "screen mesh potential"),
    ("R_cross", "21[mm]", "effective -1 kV screen-cross ring outer radius, tuned to 3D on-axis V (8.485 = hub only; 3D arms reach 45.4)"),
    ("eps_polyimide", "3", "rel. permittivity of polyimide ring (P25N)"),
    ("eps_holder", "3.15", "rel. permittivity of MCP holder (Ultem 1000 polyetherimide)"),
    # particles
    ("m_ion", "1.7e-24[kg]", "particle mass"),
    ("Z_ion", "1", "charge number"),
    ("E_ion", "1[eV]", "initial kinetic energy"),
    ("N_ion", "1000", "number of particles released (Particle Beam release only)"),
    ("t_end", "800[us]", "particle tracing end time (3D model used 200 us)"),
    ("dt_out", "1[us]", "particle tracing output interval"),
]


# Lens assembly, from the STEP part faces (r in mm; z in the assembly CAD frame, beam along +z).
# The parts are bodies of revolution near the axis; slots, rod holes, spacer pockets and set-screw holes
# (all at r > 14 mm) are dropped.  Rods and bracket (grounded, off-axis) are not axisymmetric -> omitted.
ELECTRODES = [  # tag, profile, CAD z of the front face (the face closest to the needle)
    ("L1", "lens", -136.165), ("L2", "lens", -124.935), ("L3", "lens", -113.705), ("L4", "lens", -102.475),
    ("L5", "accel", -91.245), ("L6", "accel", -79.015), ("L7", "accel", -66.785), ("L8", "accel", -54.555),
    ("L9", "accel", -42.325),
]
# Deflector pairs (D1 = halves a/b at CAD z -25.46..-12.69, D2 at -12.0..+0.77): each half is a 4.5 mm
# plate plus a half-tube (r 5..6.5) reaching past the other half's plate.  2D: full tube + both plates.
DEFLECTORS = [
    ("D1", [("5", -25.46), ("6.5", -25.46), ("6.5", -24.69), ("32.5", -24.69), ("32.5", -20.19),
            ("6.5", -20.19), ("6.5", -17.96), ("32.5", -17.96), ("32.5", -13.46), ("6.5", -13.46),
            ("6.5", -12.69), ("5", -12.69)]),
    ("D2", [("5", -12.0), ("6.5", -12.0), ("6.5", -11.23), ("32.5", -11.23), ("32.5", -6.73),
            ("6.5", -6.73), ("6.5", -4.5), ("32.5", -4.5), ("32.5", 0.0), ("6.5", 0.0),
            ("6.5", 0.77), ("5", 0.77)]),
]
ASM_TAGS = [t for t, _, _ in ELECTRODES] + [t for t, _ in DEFLECTORS]


def profile(kind, z_cad):
    """r-z polygon of one electrode; z offsets from its front face."""
    if kind == "lens":      # 9 mm plate, aperture r 5, front groove r 10..15 (5 deep), back lip r 12..13 (5 long)
        pts = [(5, 0), (10, 0), (10, 5), (15, 5), (15, 0), (32.5, 0), (32.5, 9), (13, 9), (13, 14),
               (12, 14), (12, 9), (5, 9)]
    else:                   # 10 mm plate, front recess r<15 (7 deep), 1 mm web with aperture r 5,
        pts = [(5, 7), (15, 7), (15, 0), (32.5, 0), (32.5, 10), (13, 10), (13, 15),  # back recess r<12,
               (12, 15), (12, 8), (5, 8)]                                          # lip r 12..13
    return [[f"{r:g}", f"z_asm+({z_cad}+{dz:g})"] for r, dz in pts]


def sarr2(rows):
    """Python list of lists -> java String[][]"""
    JS = jpype.JArray(jpype.JString, 2)
    return JS([[str(v) for v in row] for row in rows])


def polygon(g, tag, pts, label, selresult=True, contribute=None):
    f = g.create(tag, "Polygon")
    f.label(label)
    f.set("source", "table")
    f.set("table", sarr2(pts))
    if selresult:
        f.set("selresult", True)
    if contribute:
        f.set("contributeto", contribute)
    return f


def build_geometry(comp):
    g = comp.geom().create("geom1", 2)
    g.axisymmetric(True)
    g.lengthUnit("mm")

    # cumulative selections
    g.selection().create("csel_cond", "CumulativeSelection").label("Conductors (excluded)")
    g.selection().create("csel_diel", "CumulativeSelection").label("Dielectrics (MCP, holder, ring)")

    r = g.create("dom", "Rectangle")
    r.label("Vacuum domain")
    r.set("pos", jpype.JArray(jpype.JString)(["0", "z_dom0"]))
    r.set("size", jpype.JArray(jpype.JString)(["r_dom", "z_dom1-z_dom0"]))

    # ---------------- chamber 1 (tube) ----------------
    g.create("if1", "If").set("condition", "cfg==1||cfg==3")
    g.feature("if1").label("If tube chamber 1")
    polygon(g, "ch1", [
        ["74.928", "0"], ["101.6", "0"], ["101.6", "22.352"], ["76.2", "22.352"],
        ["76.2", "274.828"], ["101.6", "274.828"], ["101.6", "298.704"], ["74.928", "298.704"],
    ], "Chamber 1 tube + flanges (gnd)", contribute="csel_cond")
    g.create("endif1", "EndIf")

    # ---------------- chamber 2 (sphere) ----------------
    g.create("if2", "If").set("condition", "cfg==2||cfg==3")
    g.feature("if2").label("If sphere chamber 2")
    for tag, R in (("c2out", "152.4"), ("c2in", "147.637")):
        c = g.create(tag, "Circle")
        c.set("r", R)
        c.set("pos", jpype.JArray(jpype.JString)(["0", "z_c2+z_c2_center"]))
        c.set("angle", "180")
        c.set("rot", "-90")
    d = g.create("c2shell", "Difference")
    d.selection("input").set(jpype.JArray(jpype.JString)(["c2out"]))
    d.selection("input2").set(jpype.JArray(jpype.JString)(["c2in"]))
    bore = g.create("c2bore", "Rectangle")
    bore.set("pos", jpype.JArray(jpype.JString)(["0", "z_c2"]))
    bore.set("size", jpype.JArray(jpype.JString)(["74.09", "2*z_c2_center"]))
    d2 = g.create("c2cut", "Difference")
    d2.selection("input").set(jpype.JArray(jpype.JString)(["c2shell"]))
    d2.selection("input2").set(jpype.JArray(jpype.JString)(["c2bore"]))
    # input-side flange + nipple (z relative to z_c2); the output side is its mirror image
    fl = [["85.725", "0"], ["101.219", "0"], ["101.219", "22.352"], ["76.2", "22.352"],
          ["76.2", "86"], ["74.09", "86"], ["74.09", "12.7"], ["75.145", "12.7"],
          ["75.145", "1.168"], ["85.725", "1.168"]]
    polygon(g, "c2fl1", [[rr, f"z_c2+{zz}"] for rr, zz in fl], "Chamber 2 input flange", selresult=False)
    polygon(g, "c2fl2", [[rr, f"z_c2+2*z_c2_center-{zz}"] for rr, zz in fl], "Chamber 2 output flange",
            selresult=False)
    u = g.create("ch2", "Union")
    u.label("Chamber 2 (gnd)")
    u.selection("input").set(jpype.JArray(jpype.JString)(["c2cut", "c2fl1", "c2fl2"]))
    u.set("intbnd", False)
    u.set("selresult", True)
    u.set("contributeto", "csel_cond")
    g.create("endif2", "EndIf")

    # ---------------- needle ----------------
    polygon(g, "needle", [
        ["0", "tip_base_z"], ["r_needle", "tip_base_z"], ["r_needle", "tip_z-L_cone"],
        ["r_tip", "tip_z"], ["0", "tip_z"],
    ], "Needle (gnd)", contribute="csel_cond")

    # ---------------- lens assembly ----------------
    for tag, kind, z_cad in ELECTRODES:
        polygon(g, tag, profile(kind, z_cad), f"{tag} ({kind})", contribute="csel_cond")
    # Deflectors: deleted for cfg 1 and 2 to make room (same as the 3D model's "If delete deflectors").
    # Each split-cylinder pair is idealised as one axisymmetric body (full tube + both mounting plates).
    g.create("if_defl", "If").set("condition", "cfg!=1&&cfg!=2")
    g.feature("if_defl").label("If keep deflectors (deleted for cfg 1 and 2)")
    for tag, pts in DEFLECTORS:
        polygon(g, tag, [[r, f"z_asm+({z})"] for r, z in pts], f"{tag} (deflector pair, axisymmetric)",
                contribute="csel_cond")
    g.create("endif_defl", "EndIf")

    # ---------------- MCP stack (relative to mcp_z) ----------------
    m = "mcp_z"
    mcp = g.create("mcp", "Rectangle")
    mcp.label("MCP plate")
    mcp.set("pos", jpype.JArray(jpype.JString)(["0", m]))
    mcp.set("size", jpype.JArray(jpype.JString)(["20", "5.9"]))
    mcp.set("selresult", True)
    mcp.set("contributeto", "csel_diel")
    polygon(g, "holder", [
        ["25", f"{m}-4"], ["33", f"{m}-4"], ["33", f"{m}+4.9"], ["43", f"{m}+4.9"], ["43", f"{m}+7.9"],
        ["25", f"{m}+7.9"], ["25", f"{m}+4.9"], ["20", f"{m}+4.9"], ["20", f"{m}-1"], ["25", f"{m}-1"],
    ], "MCP holder (Ultem)", contribute="csel_diel")
    ring = g.create("ring", "Rectangle")
    ring.label("Polyimide ring")
    ring.set("pos", jpype.JArray(jpype.JString)(["27.5", f"{m}+7.9"]))
    ring.set("size", jpype.JArray(jpype.JString)(["69.862-27.5", "7.5"]))
    ring.set("selresult", True)
    ring.set("contributeto", "csel_diel")
    hub = g.create("hub", "Rectangle")
    hub.label("Screen cross hub / effective cross ring (r 5.5..R_cross)")
    hub.set("pos", jpype.JArray(jpype.JString)(["5.5", f"{m}-15.6"]))
    hub.set("size", jpype.JArray(jpype.JString)(["max(R_cross,8.485[mm])-5.5[mm]", "3"]))
    hub.set("selresult", True)
    hub.set("contributeto", "csel_cond")
    ln = g.create("meshline", "Polygon")
    ln.label("Screen mesh (transparent, -1 kV)")
    ln.set("type", "open")
    ln.set("source", "table")
    ln.set("table", sarr2([["0", f"{m}-12.7"], ["5.5", f"{m}-12.7"]]))
    ln.set("selresult", True)

    # expose domain + boundary selections of every object that creates one
    for t in ("ch1", "ch2", "needle", *ASM_TAGS, "mcp", "holder", "ring", "hub", "meshline"):
        g.feature(t).set("selresultshow", "all")

    g.run("fin")

    # derived selections
    cs = g.create("sel_es", "ComplementSelection")
    cs.label("es domains (not conductors)")
    cs.set("input", jpype.JArray(jpype.JString)(["csel_cond"]))
    un = g.create("sel_solid", "UnionSelection")
    un.label("All solids")
    un.set("input", jpype.JArray(jpype.JString)(["csel_cond", "csel_diel"]))
    cv = g.create("sel_vac", "ComplementSelection")
    cv.label("Vacuum (particle domain)")
    cv.set("input", jpype.JArray(jpype.JString)(["sel_solid"]))
    bt = g.create("sel_tip", "BoxSelection")
    bt.label("Needle tip face")
    bt.set("entitydim", jpype.JInt(1))
    bt.set("xmin", "-1e-3"); bt.set("xmax", "r_tip+1e-3")
    bt.set("ymin", "tip_z-1e-3"); bt.set("ymax", "tip_z+1e-3")
    bt.set("condition", "inside")
    for tag, src in (("bnd_mcpfront", ("0", "20", m, m)), ("bnd_mcpback", ("0", "20", f"{m}+5.9", f"{m}+5.9"))):
        b = g.create(tag, "BoxSelection")
        b.set("entitydim", jpype.JInt(1))
        b.set("xmin", f"{src[0]}-1e-3"); b.set("xmax", f"{src[1]}+1e-3")
        b.set("ymin", f"{src[2]}-1e-3"); b.set("ymax", f"{src[3]}+1e-3")
        b.set("condition", "inside")
    g.feature("bnd_mcpfront").label("MCP front face")
    g.feature("bnd_mcpback").label("MCP back face")
    g.run()
    print(f"geometry: {g.getNDomains()} domains, {g.getNBoundaries()} boundaries", flush=True)
    return g


def build_physics(comp, release="file"):
    es = comp.physics().create("es", "Electrostatics", "geom1")
    es.selection().named("geom1_sel_es")
    es.feature("ccn1").set("epsilonr_mat", "userdef")
    es.feature("ccn1").set("epsilonr", jpype.JArray(jpype.JString)(["1", "0", "0", "0", "1", "0", "0", "0", "1"]))
    c2 = es.create("ccn2", "ChargeConservation", 2)
    c2.label("Polyimide ring")
    c2.selection().named("geom1_ring_dom")
    c2.set("epsilonr_mat", "userdef")
    c2.set("epsilonr", jpype.JArray(jpype.JString)(["eps_polyimide", "0", "0", "0", "eps_polyimide", "0", "0", "0", "eps_polyimide"]))
    c3 = es.create("ccn3", "ChargeConservation", 2)
    c3.label("MCP holder")
    c3.selection().named("geom1_holder_dom")
    c3.set("epsilonr_mat", "userdef")
    c3.set("epsilonr", jpype.JArray(jpype.JString)(["eps_holder", "0", "0", "0", "eps_holder", "0", "0", "0", "eps_holder"]))

    def bc(tag, typ, sel, label, V=None):
        f = es.create(tag, typ, 1)
        f.label(label)
        f.selection().named(sel)
        if V:
            f.set("V0", V)
        return f

    bc("gnd_needle", "Ground", "geom1_needle_bnd", "Ground needle")
    bc("gnd_ch1", "Ground", "geom1_ch1_bnd", "Ground chamber 1")
    bc("gnd_ch2", "Ground", "geom1_ch2_bnd", "Ground chamber 2")
    for tag, _, _ in ELECTRODES:
        bc(f"pot_{tag}", "ElectricPotential", f"geom1_{tag}_bnd", f"{tag} potential", f"{tag}_v")
    bc("pot_D1", "ElectricPotential", "geom1_D1_bnd", "D1 potential (mean of halves)", "(D1a_v+D1b_v)/2")
    bc("pot_D2", "ElectricPotential", "geom1_D2_bnd", "D2 potential (mean of halves)", "(D2a_v+D2b_v)/2")
    bc("pot_mcpf", "ElectricPotential", "geom1_bnd_mcpfront", "MCP front", "V_mcp_front")
    bc("pot_mcpb", "ElectricPotential", "geom1_bnd_mcpback", "MCP back", "V_mcp_back")
    bc("pot_hub", "ElectricPotential", "geom1_hub_bnd", "Screen hub", "V_screen")
    bc("pot_mesh", "ElectricPotential", "geom1_meshline_bnd", "Screen mesh", "V_screen")

    cpt = comp.physics().create("cpt", "ChargedParticleTracing", "geom1")
    cpt.selection().named("geom1_sel_vac")
    # The axis node defaults to "Freeze", which stops particles at the beam crossover.
    # A ray crossing the axis in 3D is a specular reflection in (r, z) -> Bounce.
    cpt.feature("axi1").set("WallCondition", "Bounce")
    pp = cpt.feature("pp1")
    pp.set("mp", "m_ion")
    pp.set("Z", "Z_ion")
    ef = cpt.create("ef1", "ElectricForce", 2)
    ef.selection().named("geom1_sel_vac")
    allowed = [str(v) for v in ef.getAllowedPropertyValues("E_src")]
    esrc = [v for v in allowed if ".es." in v]
    print("E_src options:", allowed, flush=True)
    ef.set("E_src", esrc[0])
    # default wall (wall1) freezes particles on all exterior boundaries of the vacuum
    if release == "file":
        # exact 3D initial conditions mapped to meridional rays (export_3d_release.py)
        rel = cpt.create("relf1", "ReleaseFromDataFile")
        rel.label("Release: 3D beam initial conditions")
        rel.set("Filename", str(RELEASE_FILE))
        rel.set("icolp", jpype.JInt(0))
        rel.set("InitialVelocity", "FromFile")
        rel.set("icolv", jpype.JInt(2))
        rel.importData()
        print(f"release: data file {RELEASE_FILE.name}", flush=True)
    else:
        # COMSOL's 2D-axisymmetric Particle Beam; NOTE: samples r<0 for half of the
        # particles (they freeze at the tip) -> not equivalent to the 3D beam
        rel = cpt.create("pbeam1", "ParticleBeam", 1)
        rel.selection().named("geom1_sel_tip")
        for k, v in (("N", "N_ion"), ("El", "E_ion"), ("LongitudinalVelocitySpecification", "SpecifyKineticEnergy"),
                     ("TransverseVelocityDistributionSpecification", "SpecifyPhaseSpaceEllipseDimensions"),
                     ("xm", "50[nm]"), ("xmp", "0.5"), ("SamplingFromPhaseSpaceEllipse", "Gaussian")):
            rel.set(k, v)
        print("release: ParticleBeam", flush=True)
    return es, cpt


def build_mesh(comp):
    mesh = comp.mesh().create("mesh1")
    sz = mesh.feature("size")
    sz.set("custom", True)
    sz.set("hmax", "4")
    sz.set("hmin", "0.002")
    sz.set("hgrad", "1.2")
    sz.set("hcurve", "0.2")
    ft = mesh.create("ftri1", "FreeTri")
    sizes = [("s_tip", "geom1_needle_bnd", "0.02")]
    sizes += [(f"s_{t}", f"geom1_{t}_bnd", "0.3") for t in ASM_TAGS]
    sizes += [("s_mesh", "geom1_meshline_bnd", "0.2"), ("s_hub", "geom1_hub_bnd", "0.3"),
              ("s_mcp", "geom1_bnd_mcpfront", "0.5")]
    for tag, sel, h in sizes:
        s = ft.create(tag, "Size")
        s.selection().geom("geom1", 1)
        s.selection().named(sel)
        s.set("custom", True)
        s.set("hmax", h)
        s.set("hmaxactive", True)
    # finer near the axis where the beam travels
    sax = ft.create("s_axis", "Size")
    sax.selection().geom("geom1", 2)
    sax.selection().named("geom1_sel_vac")
    sax.set("custom", True)
    sax.set("hmax", "4")
    sax.set("hmaxactive", True)
    t = time.time()
    mesh.run()
    print(f"mesh: {mesh.getNumElem()} elements, {mesh.getNumVertex()} vertices ({time.time()-t:.1f} s)", flush=True)
    return mesh


def build_studies(model):
    j = model.java
    s1 = j.study().create("std1")
    s1.label("Study 1 - electrostatics")
    st = s1.create("stat", "Stationary")
    st.setEntry("activate", "es", True)
    st.setEntry("activate", "cpt", False)

    s2 = j.study().create("std2")
    s2.label("Study 2 - particle tracing")
    tm = s2.create("time", "Transient")
    tm.setEntry("activate", "es", False)
    tm.setEntry("activate", "cpt", True)
    tm.set("tlist", "range(0,dt_out,t_end)")
    tm.set("usesol", True)
    tm.set("notsolmethod", "sol")
    tm.set("notstudy", "std1")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT_DEFAULT))
    ap.add_argument("--solve", action="store_true", help="solve electrostatics (std1)")
    ap.add_argument("--particles", action="store_true", help="also run particle tracing (std2)")
    ap.add_argument("--release", choices=["file", "beam"], default="file",
                    help="file: 3D beam initial conditions (default); beam: 2D Particle Beam feature")
    a = ap.parse_args()

    client = start()
    model = client.create("lens8_axisym")
    j = model.java
    for name, expr, desc in PARAMS:
        j.param().set(name, expr, desc)
    comp = j.component().create("comp1", True)
    build_geometry(comp)
    build_physics(comp, a.release)
    build_mesh(comp)
    build_studies(model)
    model.save(a.out)
    print(f"saved {a.out}", flush=True)
    if a.solve or a.particles:
        t = time.time()
        model.solve("Study 1 - electrostatics")
        print(f"std1 solved in {time.time()-t:.1f} s", flush=True)
        model.save(a.out)
    if a.particles:
        t = time.time()
        model.solve("Study 2 - particle tracing")
        print(f"std2 solved in {time.time()-t:.1f} s", flush=True)
        model.save(a.out)
    print(f"saved {a.out}", flush=True)


if __name__ == "__main__":
    main()
