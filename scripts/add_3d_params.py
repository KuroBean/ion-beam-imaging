"""Give the 3D model the same global parameters as the 2D model (one-off edit, saved to a NEW file).

The 3D v4 model has literals where the 2D model has parameters (docs/comsol_api_notes.md §3, §9 #4).
This adds the parameters with the 2D names, with values equal to the current literals, and points the
nodes at them. Physics is unchanged, so the stored mesh and solutions stay valid.

  parameter     value          node(s) rebound
  V_mcp_front   -10000[V]      es/pot5.V0   (MCP Front Electric Potential)
  V_mcp_back    -5000[V]       es/pot6.V0   (MCP Back Electric Potential)
  V_screen      -1000[V]       es/pot7.V0, es/pot8.V0   (screen mesh cross, screen mesh)
  m_ion         1.7e-24[kg]    cpt/pp1.mp
  Z_ion         1              cpt/pp1.Z
  t_end         250[us]        std2/time.tlist and sol2/t1.tlist = range(0,dt_out,t_end)
  dt_out        0.5[us]

Every node is checked (tag, label, current literal) before it is changed; any mismatch aborts
without saving. The input model is never saved; an existing output file is never overwritten.

Usage:  .venv\\Scripts\\python.exe scripts\\add_3d_params.py [in.mph] [out.mph]
        (defaults: models.3d from config/paths.yaml -> lens8newMCP_ks_v5_params.mph next to it)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from introspect_models import setup_mph  # noqa: E402
from ionopt.config import load_config  # noqa: E402

PARAMS = [  # name, expression, description (descriptions as in build_axisym.py)
    ("V_mcp_front", "-10000[V]", "MCP front potential"),
    ("V_mcp_back", "-5000[V]", "MCP back potential"),
    ("V_screen", "-1000[V]", "screen mesh potential (mesh disc and cross)"),
    ("m_ion", "1.7e-24[kg]", "particle mass"),
    ("Z_ion", "1", "charge number"),
    ("t_end", "250[us]", "particle tracing end time"),
    ("dt_out", "0.5[us]", "particle tracing output interval"),
]
# (physics, feature tag, label must contain, property, current literal (evaluated), new expression)
REBIND = [
    ("es", "pot5", "MCP Front", "V0", -10000.0, "V_mcp_front"),
    ("es", "pot6", "MCP Back", "V0", -5000.0, "V_mcp_back"),
    ("es", "pot7", "Screen Mesh Cross", "V0", -1000.0, "V_screen"),
    ("es", "pot8", "Screen Mesh", "V0", -1000.0, "V_screen"),
    ("cpt", "pp1", "Particle Properties", "mp", 1.7e-24, "m_ion"),
    ("cpt", "pp1", "Particle Properties", "Z", 1.0, "Z_ion"),
]
TLIST = "range(0,dt_out,t_end)"
OLD_TLIST = [0.0, 0.5e-6, 250e-6]   # first, second, last output time of the current literal tlist


def close(a: float, b: float) -> bool:
    return abs(a - b) <= 1e-9 * max(abs(a), abs(b), 1e-30)


def times(node) -> list[float]:
    """Output times of a tlist property, evaluated (COMSOL expands range() on read)."""
    try:
        return [float(x) for x in node.getDoubleArray("tlist")]
    except Exception:  # noqa: BLE001
        m = node.getStringMatrix("tlist")
        return [float(x) for row in m for x in row]


def main():
    cfg = load_config(ROOT / "config")
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else cfg.path("models.3d")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_name("lens8newMCP_ks_v5_params.mph")
    if out.resolve() == src.resolve():
        sys.exit("refusing to save over the input model")
    if out.exists():
        sys.exit(f"refusing to overwrite existing {out}")

    mph = setup_mph(cfg.paths.comsol_root)
    client = mph.start()
    t = time.time()
    model = client.load(str(src))
    print(f"loaded {src.name} in {time.time() - t:.0f} s", flush=True)
    j = model.java
    comp = j.component("comp1")
    par = j.param()

    # ---- checks first: nothing is changed unless every target is as expected
    existing = {str(n) for n in par.varnames()}
    clash = [n for n, _, _ in PARAMS if n in existing]
    if clash:
        sys.exit(f"ABORT: parameters already exist: {clash}")
    for ph, tag, lab, prop, old, _ in REBIND:
        f = comp.physics(ph).feature(tag)
        label, cur = str(f.label()), str(f.getString(prop))
        if lab not in label or not close(float(cur), old):
            sys.exit(f"ABORT: {ph}/{tag} '{label}' {prop}={cur!r}, expected label ~'{lab}' and {old}")
        print(f"check ok  {ph}/{tag:5s} '{label}'  {prop} = {cur}", flush=True)
    step = j.study("std2").feature("time")
    t1 = j.sol("sol2").feature("t1")
    for name, node in (("std2/time", step), ("sol2/t1", t1)):
        tl = times(node)
        if not (close(tl[0], OLD_TLIST[0] + 0.0) and close(tl[1], OLD_TLIST[1]) and close(tl[-1], OLD_TLIST[2])):
            sys.exit(f"ABORT: {name} tlist {node.getString('tlist')!r} != range(0,0.5 us,250 us)")
        print(f"check ok  {name} tlist = {node.getString('tlist')} ({len(tl)} times)", flush=True)

    # ---- edits
    for name, expr, descr in PARAMS:
        par.set(name, expr, descr)
    for ph, tag, _, prop, _, expr in REBIND:
        comp.physics(ph).feature(tag).set(prop, expr)
    step.set("tlist", TLIST)
    t1.set("tlist", TLIST)

    # ---- verify: same values as before, now through the parameters
    for ph, tag, _, prop, old, expr in REBIND:
        got = str(comp.physics(ph).feature(tag).getString(prop))
        val = float(par.evaluate(expr))
        assert got == expr and close(val, old), (ph, tag, prop, got, val, old)
        print(f"set       {ph}/{tag:5s} {prop} = {got} -> {val:g}", flush=True)
    for name, node in (("std2/time", step), ("sol2/t1", t1)):
        tl = times(node)
        assert str(node.getString("tlist")) == TLIST
        assert close(tl[1], OLD_TLIST[1]) and close(tl[-1], OLD_TLIST[2]) and len(tl) == 501, (name, len(tl))
        print(f"set       {name} tlist = {TLIST} ({len(tl)} times, last {tl[-1]:g} s)", flush=True)

    t = time.time()
    model.save(str(out))
    print(f"saved {out.name} in {time.time() - t:.0f} s (input {src.name} not saved)", flush=True)
    client.remove(model)


if __name__ == "__main__":
    main()
