"""Dump all properties of geometry, physics, material and study features.

Writes a greppable text dump so dimensions/settings can be transferred
to the 2D axisymmetric model.

Usage:  .venv\\Scripts\\python.exe scripts\\dump_features.py > logs\\features.txt
"""
from comsol_session import load, start


def props(f):
    out = {}
    try:
        names = [str(p) for p in f.properties()]
    except Exception:
        return out
    for p in names:
        try:
            v = f.getStringMatrix(p)
            v = [[str(x) for x in row] for row in v]
            if len(v) == 1:
                v = v[0]
            if len(v) == 1:
                v = v[0]
        except Exception:
            try:
                v = [str(x) for x in f.getStringArray(p)]
                if len(v) == 1:
                    v = v[0]
            except Exception:
                try:
                    v = str(f.getString(p))
                except Exception:
                    v = "<?>"
        out[p] = v
    return out


def ents(sel):
    try:
        return f"dim{sel.dimension()}:{list(sel.entities(sel.dimension()))}"
    except Exception:
        for d in (3, 2, 1, 0):
            try:
                e = list(sel.entities(d))
                if e:
                    return f"dim{d}:{e}"
            except Exception:
                pass
    return "?"


def dump(label, f, indent="  "):
    active = "" if f.isActive() else "  [DISABLED]"
    print(f"{indent}{f.tag()} ({f.getType()}) '{f.label()}'{active}")
    try:
        print(f"{indent}   selection: {ents(f.selection())}")
    except Exception:
        pass
    for k, v in props(f).items():
        if v in ("", [], [[]]):
            continue
        s = str(v)
        if len(s) > 300:
            s = s[:300] + " ..."
        print(f"{indent}   {k} = {s}")


def walk_geom(seq, indent="  "):
    for t in seq.feature().tags():
        f = seq.feature(t)
        dump(t, f, indent)
        if str(f.getType()) == "WorkPlane":
            print(f"{indent}   -- work plane sequence:")
            walk_geom(f.geom(), indent + "      ")


def main():
    client = start()
    model = load(client)
    j = model.java
    comp = j.component("comp1")

    print("\n######## GEOMETRY ########")
    walk_geom(comp.geom("geom1"))

    print("\n######## GEOMETRY SELECTIONS (named) ########")
    for t in comp.selection().tags():
        s = comp.selection(t)
        try:
            print(f"  {t} '{s.label()}' {ents(s)}")
        except Exception as e:
            print(f"  {t} '{s.label()}' ({e})")

    print("\n######## MATERIALS ########")
    for t in comp.material().tags():
        m = comp.material(t)
        print(f"  {t} '{m.label()}' sel={ents(m.selection())}")
        try:
            print(f"     def: {props(m.propertyGroup('def'))}")
        except Exception:
            pass

    for ph in comp.physics().tags():
        print(f"\n######## PHYSICS {ph} ########")
        p = comp.physics(ph)
        for k, v in props(p).items():
            print(f"   {k} = {v}")
        for t in p.feature().tags():
            dump(t, p.feature(t))
            for st in p.feature(t).feature().tags():
                dump(st, p.feature(t).feature(st), "        ")

    print("\n######## MESH ########")
    for t in comp.mesh("mesh1").feature().tags():
        f = comp.mesh("mesh1").feature(t)
        dump(t, f)
        for st in f.feature().tags():
            dump(st, f.feature(st), "        ")

    print("\n######## STUDIES ########")
    for s in j.study().tags():
        for t in j.study(s).feature().tags():
            f = j.study(s).feature(t)
            print(f"  [{s}]")
            d = props(f)
            d.pop("tlist", None)
            print(f"  {t} ({f.getType()}) {d}")

    print("\n######## SOLVER sol2 ########")
    for t in j.sol("sol2").feature().tags():
        f = j.sol("sol2").feature(t)
        dump(t, f)
        for st in f.feature().tags():
            dump(st, f.feature(st), "        ")

    client.clear()


if __name__ == "__main__":
    main()
