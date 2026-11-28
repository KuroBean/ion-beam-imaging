"""Check a 3D model's geometry after a GUI edit: where the screen mesh disc and the MCP face sit, and
which material each domain ends up with. Loads READ ONLY (never saves).

If the model has no stored mesh, builds geometry + mesh in memory first (the 3D mesh takes a few min).

Writes logs/verify_geom_<name>.json with, per domain: bounding box (mm), tet count, the materials whose
selection contains it and the effective one (the last in the tree wins), and the named domain
selections it belongs to; plus the z extent (mm) of the key boundary selections.

Compare two runs (e.g. v5 vs v6) with:  verify_3d_geometry.py --compare a.json b.json

Usage:  .venv\\Scripts\\python.exe scripts\\verify_3d_geometry.py [model.mph]
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

DOM_SELS = ["geom1_sel1", "geom1_sel5", "geom1_sel6", "geom1_sel7", "geom1_sel9_dom", "geom1_sel12_dom",
            "geom1_sel13", "geom1_sel14", "geom1_uni6_dom", "geom1_uni7_dom"]
BND_SELS = {"mesh plane (adj3, V_screen)": "adj3", "mesh cross/frame (adj2, V_screen)": "adj2",
            "MCP front (geom1_sel3)": "geom1_sel3", "MCP back (geom1_sel4)": "geom1_sel4", "tip (adj5)": "adj5"}


def tags(nl):
    return [str(t) for t in nl.tags()]


def ents(comp, sel, dim):
    try:
        return [int(e) for e in comp.selection(sel).entities(dim)]
    except Exception:  # noqa: BLE001
        return None


def measure(path: Path) -> dict:
    from introspect_models import setup_mph  # noqa: PLC0415
    from ionopt.config import load_config  # noqa: PLC0415
    cfg = load_config(ROOT / "config")
    mph = setup_mph(cfg.paths.comsol_root)
    client = mph.start(cores=None)
    t = time.time()
    model = client.load(str(path))
    print(f"loaded {path.name} in {time.time() - t:.0f} s", flush=True)
    j = model.java
    comp = j.component("comp1")
    par = j.param()
    pv = {n: float(par.evaluate(n)) * 1e3 for n in ("tip_z", "mcp_z", "lens_gap") if n in [str(x) for x in par.varnames()]}
    if "mesh_gap" in [str(x) for x in par.varnames()]:
        pv["mesh_gap"] = float(par.evaluate("mesh_gap")) * 1e3
    mesh = comp.mesh("mesh1")
    n0 = int(mesh.getNumElem())
    built = False
    timings = {}
    if n0 == 0:
        t = time.time()
        comp.geom("geom1").run()
        timings["geometry_s"] = round(time.time() - t, 1)
        print(f"geometry built in {timings['geometry_s']} s", flush=True)
        t = time.time()
        mesh.run()
        timings["mesh_s"] = round(time.time() - t, 1)
        built = True
        print(f"mesh built in {timings['mesh_s']} s: {int(mesh.getNumElem())} elements", flush=True)
    V = np.array([np.array(r) for r in mesh.getVertex()])                       # (3, Nv) mm
    T = np.array([np.array(r) for r in mesh.getElem("tet")]).astype(np.int64)
    E = np.array(mesh.getElemEntity("tet"), dtype=np.int64)
    F = np.array([np.array(r) for r in mesh.getElem("tri")]).astype(np.int64)
    B = np.array(mesh.getElemEntity("tri"), dtype=np.int64)
    n_dom = int(comp.geom("geom1").getNDomains())
    print(f"tet entity ids {E.min()}..{E.max()} (n_dom {n_dom}), tri ids {B.min()}..{B.max()}", flush=True)

    mats = []
    for mt in tags(comp.material()):
        m = comp.material(mt)
        mats.append((mt, str(m.label()), set(int(e) for e in m.selection().entities(3))))
    sels = {s: set(ents(comp, s, 3) or []) for s in DOM_SELS}

    doms = []
    for d in range(1, n_dom + 1):
        m = E == d
        if m.any():
            p = V[:, np.unique(T[:, m])]
            bb = [[round(float(p[i].min()), 3), round(float(p[i].max()), 3)] for i in range(3)]
        else:
            bb = None
        inm = [mt for mt, _, s in mats if d in s]
        doms.append({"dom": d, "n_tet": int(m.sum()), "bbox_mm": bb, "materials": inm,
                     "material": inm[-1] if inm else None, "sels": [s for s, v in sels.items() if d in v]})

    bnd = {}
    for name, sel in BND_SELS.items():
        b = ents(comp, sel, 2)
        if not b:
            bnd[name] = {"sel": sel, "n": 0}
            continue
        m = np.isin(B, b)
        p = V[:, np.unique(F[:, m])] if m.any() else np.zeros((3, 0))
        bnd[name] = {"sel": sel, "n": len(b),
                     "z_mm": [round(float(p[2].min()), 4), round(float(p[2].max()), 4)] if p.size else None,
                     "r_max_mm": round(float(np.hypot(p[0], p[1]).max()), 3) if p.size else None}
    client.remove(model)
    return {"file": path.name, "params_mm": pv, "n_elem_stored": n0, "mesh_built_here": built,
            "n_elem": int(len(E)), "timings": timings, "n_dom": n_dom,
            "materials": [{"tag": mt, "label": lb, "n": len(s)} for mt, lb, s in mats],
            "domains": doms, "boundaries": bnd}


def report(d: dict) -> None:
    p = d["params_mm"]
    print(f"\n== {d['file']} ==  params (mm): {p}")
    print(f"mesh elements: stored {d['n_elem_stored']}, used {d['n_elem']}  {d['timings']}")
    for name, b in d["boundaries"].items():
        print(f"  {name:36s} n={b['n']:3d} z={b.get('z_mm')} r_max={b.get('r_max_mm')}")
    if "mesh_gap" in p:
        print(f"  expected mesh plane z = mcp_z - mesh_gap = {p['mcp_z'] - p['mesh_gap']:.4f} mm")
    labels = {m["tag"]: m["label"] for m in d["materials"]}
    print("  domains (non-vacuum by size order is not implied):")
    for x in d["domains"]:
        print(f"   {x['dom']:3d} {x['n_tet']:8d} tets  bbox={x['bbox_mm']}  mat={x['material']}"
              f" ({labels.get(x['material'], '-')}) all={x['materials']} sels={x['sels']}")


def compare(a: dict, b: dict) -> None:
    """Match domains by bounding box; list material changes and unmatched domains."""
    la = {m["tag"]: m["label"] for m in a["materials"]}
    lb = {m["tag"]: m["label"] for m in b["materials"]}
    key = lambda x: tuple(round(v, 1) for ax in x["bbox_mm"] for v in ax) if x["bbox_mm"] else None  # noqa: E731
    ia = {key(x): x for x in a["domains"]}
    ib = {key(x): x for x in b["domains"]}
    print(f"\n== compare {a['file']} ({a['n_dom']} dom) -> {b['file']} ({b['n_dom']} dom) ==")
    for k in sorted(set(ia) | set(ib), key=lambda k: (k is None, k)):
        x, y = ia.get(k), ib.get(k)
        if x and y:
            ma, mb = la.get(x["material"], "-"), lb.get(y["material"], "-")
            if ma != mb:
                print(f"  CHANGED  dom {x['dom']}->{y['dom']} bbox={k}: {ma} -> {mb}")
        elif x:
            print(f"  ONLY OLD dom {x['dom']:3d} bbox={k} mat={la.get(x['material'], '-')} tets={x['n_tet']}")
        else:
            print(f"  ONLY NEW dom {y['dom']:3d} bbox={k} mat={lb.get(y['material'], '-')} tets={y['n_tet']}")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--compare":
        a, b = (json.loads(Path(p).read_text()) for p in args[1:3])
        compare(a, b)
        return
    sys.path.insert(0, str(ROOT / "scripts"))
    from ionopt.config import load_config  # noqa: PLC0415
    path = Path(args[0]) if args else load_config(ROOT / "config").path("models.3d")
    d = measure(path)
    out = ROOT / "logs" / f"verify_geom_{path.stem}.json"
    out.write_text(json.dumps(d, indent=1))
    report(d)
    print(f"\nwrote {out}")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Total {time.time() - t0:.0f} s")
