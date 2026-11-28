"""Task 8 (plan_v1 section 13): COMSOL introspection of the base models.

Loads each model READ ONLY (never saves) and records what the adapter (task 9) needs:
parameters, model tree, named selections, physics features (with their selection and key
settings), materials, particle release nodes (all properties), studies, solutions,
datasets and export nodes, and the electrode geometry features.

Writes, per model key:
  logs/introspect_<key>.txt    human-readable report
  logs/introspect_<key>.json   the same data, for diffing after model edits

Model paths and the COMSOL root come from config/paths.yaml (models.<key>, comsol_root).

Usage:  .venv\\Scripts\\python.exe scripts\\introspect_models.py [2d] [3d] [--path other.mph]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ionopt.config import load_config  # noqa: E402

# Geometry features whose full property list is dumped (electrodes, needle, detector, imports)
GEOM_DETAIL = re.compile(r"(imp|mov|rot|^L\d|^D\d|lens|acc|defl|needle|tip|cone|cyl|mcp|mesh|ring|hub|"
                         r"holder|screen|cross|if|endif|rect|^r\d|^e\d|sel|box|uni|del|wp)", re.I)
# Physics features whose full property list is dumped (release, walls, force)
PHYS_DETAIL = re.compile(r"(Release|Beam|Inlet|Outlet|Wall|Force|Particle|Axial|Bounce)", re.I)
# Properties read as the unevaluated expression (getStringMatrix returns the expanded list)
EXPR_PROPS = ("tlist", "plist", "pname", "newposx", "newposy", "newposz", "displx", "disply", "displz",
              "quickz", "offset", "r", "h", "z", "V0", "mp", "Z", "N", "El")


def sel_dim(s):
    """COMSOL returns dimension() as an int[] (one entry) for most selection objects."""
    d = safe(lambda: s.dimension())
    if d is None:
        return None
    try:
        d = [int(x) for x in d]
    except TypeError:          # a plain int
        return int(d)
    return d[0] if len(d) == 1 else d


def sel_entities(s, dim):
    if isinstance(dim, int):
        return safe(lambda: [int(e) for e in s.entities(dim)])
    return None


def setup_mph(comsol_root: str | None):
    if comsol_root:
        jre = Path(comsol_root) / "java" / "win64" / "jre" / "bin"
        if str(jre) not in os.environ.get("PATH", ""):
            os.environ["PATH"] = str(jre) + os.pathsep + os.environ.get("PATH", "")
    import mph  # noqa: PLC0415  (after the PATH fix)
    return mph


def tags(node_list) -> list[str]:
    try:
        return [str(t) for t in node_list.tags()]
    except Exception:  # noqa: BLE001
        return []


def safe(fn, default=None):
    try:
        return fn()
    except Exception:  # noqa: BLE001
        return default


def props(f) -> dict:
    """All properties of a feature as strings / lists of strings."""
    out = {}
    for p in safe(lambda: [str(x) for x in f.properties()], []):
        if p in EXPR_PROPS:
            v = safe(lambda: str(f.getString(p)))
            if v is not None:
                out[p] = v
                continue
        v = safe(lambda: [[str(x) for x in row] for row in f.getStringMatrix(p)])
        if v is not None:
            if len(v) == 1:
                v = v[0]
                if len(v) == 1:
                    v = v[0]
        else:
            v = safe(lambda: [str(x) for x in f.getStringArray(p)])
            if v is not None and len(v) == 1:
                v = v[0]
            if v is None:
                v = safe(lambda: str(f.getString(p)), "<?>")
        out[p] = v
    return out


def selection_info(f) -> dict | None:
    s = safe(lambda: f.selection())
    if s is None:
        return None
    info = {"named": safe(lambda: str(s.named()), "")}
    dim = sel_dim(s)
    info["dim"] = dim
    ents = sel_entities(s, dim)
    if ents is not None:
        info["n"] = len(ents)
        info["entities"] = ents if len(ents) <= 40 else ents[:40] + ["..."]
    return info


def fmt_sel(si: dict | None) -> str:
    if not si:
        return ""
    s = f" sel[dim{si.get('dim')}"
    if si.get("named"):
        s += f" named={si['named']}"
    if "n" in si:
        s += f" n={si['n']}"
        if not si.get("named"):
            s += f" {si['entities'][:12]}"
    return s + "]"


# --------------------------------------------------------------------------- sections


def parameters(model, j) -> list[dict]:
    out = []
    p = j.param()
    for name in [str(n) for n in p.varnames()]:
        expr = str(p.get(name))
        desc = safe(lambda: str(p.descr(name)), "")
        val = safe(lambda: float(p.evaluate(name)))   # SI value
        if val is None:
            val = safe(lambda: str(model.evaluate(name)), "?")
        out.append({"name": name, "expr": expr, "value_SI": val, "descr": desc})
    return out


def geometry(comp) -> list[dict]:
    out = []
    for gt in tags(comp.geom()):
        g = comp.geom(gt)
        gd = {"tag": gt, "sdim": safe(lambda: int(g.getSDim())),
              "n_dom": safe(lambda: int(g.getNDomains())), "n_bnd": safe(lambda: int(g.getNBoundaries())),
              "features": [], "selections": []}
        for ft in tags(g.feature()):
            f = g.feature(ft)
            d = {"tag": ft, "type": safe(lambda: str(f.getType()), "?"), "label": safe(lambda: str(f.label()), ""),
                 "active": bool(safe(lambda: f.isActive(), True))}
            if GEOM_DETAIL.search(ft) or GEOM_DETAIL.search(d["label"]) or GEOM_DETAIL.search(d["type"]):
                d["props"] = props(f)
            gd["features"].append(d)
        for st in tags(g.selection()):
            s = g.selection(st)
            gd["selections"].append({"tag": st, "type": safe(lambda: str(s.getType()), "?"),
                                     "label": safe(lambda: str(s.label()), "")})
        out.append(gd)
    return out


def comp_selections(comp) -> list[dict]:
    out = []
    for st in tags(comp.selection()):
        s = comp.selection(st)
        d = {"tag": st, "label": safe(lambda: str(s.label()), ""),
             "type": safe(lambda: str(s.getType()), "?"), "dim": sel_dim(s)}
        ents = sel_entities(s, d["dim"])
        if ents is not None:
            d["n"] = len(ents)
            d["entities"] = ents if len(ents) <= 40 else ents[:40] + ["..."]
        d["props"] = props(s)
        out.append(d)
    return out


def physics(comp) -> list[dict]:
    out = []
    for pt in tags(comp.physics()):
        ph = comp.physics(pt)
        pd = {"tag": pt, "type": safe(lambda: str(ph.getType()), "?"), "label": safe(lambda: str(ph.label()), ""),
              "props": props(ph), "features": []}
        if pt == "cpt" or "Particle" in pd["type"]:
            pd["prop_groups"] = {}
            for grp in ("ParticleReleaseSpecification", "ParticleProperties", "PhysicsVariables",
                        "AdvancedSettings"):
                pd["prop_groups"][grp] = safe(lambda: props(ph.prop(grp)), {})
        for ft in tags(ph.feature()):
            f = ph.feature(ft)
            d = {"tag": ft, "type": safe(lambda: str(f.getType()), "?"), "label": safe(lambda: str(f.label()), ""),
                 "active": bool(safe(lambda: f.isActive(), True)), "selection": selection_info(f)}
            p = props(f)
            if PHYS_DETAIL.search(d["type"]) or d["type"] in ("ElectricPotential", "Ground"):
                d["props"] = p
            else:
                d["props"] = {k: v for k, v in p.items() if k in ("V0", "epsilonr", "epsilonr_mat", "ConstitutiveRelationD")}
            # sub-features (e.g. particle properties inside a release node)
            subs = []
            for sft in tags(safe(lambda: f.feature())):
                sf = f.feature(sft)
                subs.append({"tag": sft, "type": safe(lambda: str(sf.getType()), "?"), "props": props(sf)})
            if subs:
                d["subfeatures"] = subs
            pd["features"].append(d)
        out.append(pd)
    return out


def materials(comp) -> list[dict]:
    out = []
    for mt in tags(comp.material()):
        m = comp.material(mt)
        d = {"tag": mt, "label": safe(lambda: str(m.label()), ""), "selection": selection_info(m)}
        d["epsilonr"] = safe(lambda: [str(x) for x in m.propertyGroup("def").getStringArray("relpermittivity")])
        out.append(d)
    return out


def meshes(comp) -> list[dict]:
    out = []
    for mt in tags(comp.mesh()):
        ms = comp.mesh(mt)
        d = {"tag": mt, "label": safe(lambda: str(ms.label()), ""),
             "n_elem": safe(lambda: int(ms.getNumElem())), "features": []}
        for ft in tags(ms.feature()):
            f = ms.feature(ft)
            fd = {"tag": ft, "type": safe(lambda: str(f.getType()), "?"), "label": safe(lambda: str(f.label()), ""),
                  "selection": selection_info(f)}
            subs = []
            for sft in tags(safe(lambda: f.feature())):
                sf = f.feature(sft)
                subs.append({"tag": sft, "type": safe(lambda: str(sf.getType()), "?"),
                             "label": safe(lambda: str(sf.label()), ""), "selection": selection_info(sf)})
            if subs:
                fd["subfeatures"] = subs
            d["features"].append(fd)
        out.append(d)
    return out


def studies(j) -> list[dict]:
    out = []
    for st in tags(j.study()):
        s = j.study(st)
        d = {"tag": st, "label": safe(lambda: str(s.label()), ""), "steps": []}
        for ft in tags(s.feature()):
            f = s.feature(ft)
            p = props(f)
            keep = ("tlist", "activate", "useinitsol", "initmethod", "initstudy", "initsoln", "usesol",
                    "notsolmethod", "notstudy", "notsol", "solnum", "plot", "useadvanceddisable",
                    "disabledphysics", "disabledvariables", "geometricNonlinearity", "outputmap")
            d["steps"].append({"tag": ft, "type": safe(lambda: str(f.getType()), "?"),
                               "props": {k: v for k, v in p.items() if k in keep}})
        out.append(d)
    return out


def solutions(j) -> list[dict]:
    out = []
    for st in tags(j.sol()):
        s = j.sol(st)
        d = {"tag": st, "label": safe(lambda: str(s.label()), ""), "study": safe(lambda: str(s.study()), ""),
             "features": []}
        for ft in tags(s.feature()):
            f = s.feature(ft)
            fd = {"tag": ft, "type": safe(lambda: str(f.getType()), "?")}
            if fd["type"] in ("Time", "TimeDependent", "Stationary", "StudyStep", "Variables"):
                fd["props"] = {k: v for k, v in props(f).items()
                               if k in ("tlist", "rtol", "atolglobal", "tstepsbdf", "maxstep", "initstep",
                                        "timemethod", "storeudot", "notsolmethod", "notsol", "notsoluse",
                                        "solnum", "initmethod", "initsol", "initsoluse", "studystep")}
            d["features"].append(fd)
        out.append(d)
    return out


def results(j) -> dict:
    r = j.result()
    ds = []
    for dt in tags(r.dataset()):
        dd = r.dataset(dt)
        ds.append({"tag": dt, "type": safe(lambda: str(dd.getType()), "?"), "label": safe(lambda: str(dd.label()), ""),
                   "props": {k: v for k, v in props(dd).items() if k in ("solution", "data", "comp", "geom", "par1",
                                                                          "genpoints", "quickplane", "quicky",
                                                                          "quickz", "quickx")}})
    ex = []
    for et in tags(r.export()):
        e = r.export(et)
        ex.append({"tag": et, "type": safe(lambda: str(e.getType()), "?"), "label": safe(lambda: str(e.label()), ""),
                   "props": props(e)})
    nums = []
    for nt in tags(r.numerical()):
        n = r.numerical(nt)
        nums.append({"tag": nt, "type": safe(lambda: str(n.getType()), "?"), "label": safe(lambda: str(n.label()), "")})
    pgs = [{"tag": t, "label": safe(lambda: str(r.feature(t).label()), "")} for t in tags(r)]
    return {"datasets": ds, "exports": ex, "numerical": nums, "plot_groups": pgs}


# --------------------------------------------------------------------------- report


def report(data: dict) -> str:
    L = []
    w = L.append
    w(f"# Introspection: {data['file']}  ({data['key']})")
    w(f"COMSOL {data['comsol_version']}, loaded in {data['load_s']:.1f} s, size {data['size_MB']:.0f} MB")
    w(f"MPh tree:\n{data['tree']}")
    w("\n== Parameters (expr -> SI value) ==")
    for p in data["parameters"]:
        w(f"  {p['name']:16s} = {p['expr']:60s} -> {p['value_SI']}   {p['descr']}")
    for comp in data["components"]:
        w(f"\n######## component {comp['tag']} ########")
        for g in comp["geometry"]:
            w(f"\n== Geometry {g['tag']} (sdim {g['sdim']}): {g['n_dom']} domains, {g['n_bnd']} boundaries ==")
            for f in g["features"]:
                w(f"  {f['tag']:16s} {f['type']:24s} '{f['label']}'{'' if f['active'] else '  [DISABLED]'}")
                for k, v in (f.get("props") or {}).items():
                    if k in ("selresult", "selresultshow", "contributeto", "condition", "filename", "displ",
                             "pos", "size", "r", "h", "table", "x", "y", "rot", "axis", "input", "entitydim",
                             "xmin", "xmax", "ymin", "ymax", "zmin", "zmax", "keep", "importtype", "newposz",
                             "workplane", "z", "face", "oldposvertex"):
                        w(f"      {k} = {v}")
            w("  -- geometry-level selections (named as <geom>_<tag>) --")
            for s in g["selections"]:
                w(f"  {s['tag']:16s} {s['type']:24s} '{s['label']}'")
        w("\n== Component selections ==")
        for s in comp["selections"]:
            ents = f" n={s.get('n')}" if "n" in s else ""
            w(f"  {s['tag']:16s} {s['type']:14s} dim{s['dim']}{ents}  '{s['label']}'")
        w("\n== Materials ==")
        for m in comp["materials"]:
            w(f"  {m['tag']:10s} '{m['label']}' eps_r={m['epsilonr']}{fmt_sel(m['selection'])}")
        w("\n== Physics ==")
        for ph in comp["physics"]:
            w(f"  [{ph['tag']}] {ph['type']} '{ph['label']}'")
            for grp, gp in (ph.get("prop_groups") or {}).items():
                if gp:
                    w(f"     prop({grp}): {gp}")
            for f in ph["features"]:
                w(f"     {f['tag']:12s} {f['type']:26s} '{f['label']}'{'' if f['active'] else '  [DISABLED]'}"
                  f"{fmt_sel(f['selection'])}")
                pr = f.get("props") or {}
                if f["type"] in ("ElectricPotential",):
                    w(f"         V0 = {pr.get('V0')}")
                elif PHYS_DETAIL.search(f["type"]):
                    for k, v in pr.items():
                        w(f"         {k} = {v}")
                for sf in f.get("subfeatures", []):
                    w(f"         sub {sf['tag']} {sf['type']}: {sf['props']}")
        w("\n== Meshes ==")
        for m in comp["meshes"]:
            w(f"  {m['tag']} '{m['label']}' n_elem={m['n_elem']}")
            for f in m["features"]:
                w(f"     {f['tag']:12s} {f['type']:14s} '{f['label']}'{fmt_sel(f['selection'])}")
                for sf in f.get("subfeatures", []):
                    w(f"         {sf['tag']:12s} {sf['type']:10s} '{sf['label']}'{fmt_sel(sf['selection'])}")
    w("\n== Studies ==")
    for s in data["studies"]:
        w(f"  {s['tag']} '{s['label']}'")
        for st in s["steps"]:
            w(f"     {st['tag']:10s} {st['type']:14s} {st['props']}")
    w("\n== Solutions ==")
    for s in data["solutions"]:
        w(f"  {s['tag']} '{s['label']}' study={s['study']}  features={[f['tag'] + ':' + f['type'] for f in s['features']]}")
        for f in s["features"]:
            if f.get("props"):
                w(f"       {f['tag']}: {f['props']}")
    r = data["results"]
    w("\n== Datasets ==")
    for d in r["datasets"]:
        w(f"  {d['tag']:10s} {d['type']:20s} '{d['label']}' {d['props']}")
    w("\n== Export nodes ==")
    for e in r["exports"] or []:
        w(f"  {e['tag']:10s} {e['type']:16s} '{e['label']}'")
        for k, v in e["props"].items():
            if k in ("filename", "data", "expr", "plotgroup", "plot", "exporttype", "struct", "header",
                     "fullprec", "sort", "resolution", "alwaysask"):
                w(f"      {k} = {v}")
    if not r["exports"]:
        w("  (none)")
    w("\n== Numerical (derived values) ==")
    for n in r["numerical"] or []:
        w(f"  {n['tag']:10s} {n['type']:16s} '{n['label']}'")
    w("\n== Plot groups ==")
    for p in r["plot_groups"]:
        w(f"  {p['tag']:10s} '{p['label']}'")
    return "\n".join(L) + "\n"


def introspect(mph, client, key: str, path: Path) -> dict:
    t = time.time()
    model = client.load(str(path))
    load_s = time.time() - t
    print(f"[{key}] loaded {path.name} in {load_s:.1f} s", flush=True)
    j = model.java
    import io
    from contextlib import redirect_stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        safe(lambda: mph.tree(model, max_depth=1))
    data = {"key": key, "file": path.name, "size_MB": path.stat().st_size / 1e6, "load_s": load_s,
            "comsol_version": str(client.version), "tree": buf.getvalue(),
            "parameters": parameters(model, j), "components": []}
    for ct in tags(j.component()):
        comp = j.component(ct)
        print(f"[{key}] component {ct}", flush=True)
        data["components"].append({"tag": ct, "geometry": geometry(comp), "selections": comp_selections(comp),
                                   "materials": materials(comp), "physics": physics(comp),
                                   "meshes": meshes(comp)})
    data["studies"] = studies(j)
    data["solutions"] = solutions(j)
    data["results"] = results(j)
    client.remove(model)   # never saved
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="*", default=["2d", "3d"], help="model keys from config/paths.yaml")
    ap.add_argument("--path", help="introspect this .mph instead (single key used as the output name)")
    ap.add_argument("--out", default=str(ROOT / "logs"))
    a = ap.parse_args()
    cfg = load_config(ROOT / "config")
    mph = setup_mph(cfg.paths.comsol_root)
    t = time.time()
    client = mph.start(cores=None)
    print(f"COMSOL {client.version} started in {time.time() - t:.1f} s", flush=True)
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    for key in a.keys:
        path = Path(a.path) if a.path else cfg.path(f"models.{key}")
        data = introspect(mph, client, key, path)
        (out / f"introspect_{key}.json").write_text(json.dumps(data, indent=1, default=str), encoding="utf-8")
        (out / f"introspect_{key}.txt").write_text(report(data), encoding="utf-8")
        print(f"[{key}] wrote {out / f'introspect_{key}.txt'}", flush=True)


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"Total {time.time() - t0:.1f} s")
