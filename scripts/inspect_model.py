"""Load the .mph and print a summary of its current (final) state.

Usage:  .venv\\Scripts\\python.exe scripts\\inspect_model.py [path\\to\\model.mph]
"""
import sys
import time

from comsol_session import MODEL_FILE, load, start


def tags(node_list):
    return [str(t) for t in node_list.tags()]


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else MODEL_FILE
    client = start()
    model = load(client, path)
    j = model.java

    print("\n== Parameters ==")
    for name, expr in model.parameters().items():
        desc = model.description(name) if hasattr(model, "description") else ""
        try:
            val = model.evaluate(name)
        except Exception:
            val = "?"
        print(f"  {name:14s} = {expr:55s} -> {val}  {desc}")

    comp = j.component("comp1")
    geom = comp.geom("geom1")
    print("\n== Geometry features ==")
    for t in tags(geom.feature()):
        f = geom.feature(t)
        extra = ""
        if str(f.getType()) == "Import":
            try:
                extra = f"  file={f.getString('filename')}  embedded={f.getString('importtype') if f.hasProperty('importtype') else ''}"
            except Exception:
                pass
        print(f"  {t:12s} {f.getType()!s:22s} {f.label()!s}{'' if f.isActive() else '  [disabled]'}{extra}")
    print(f"  geometry: {geom.getNDomains()} domains, {geom.getNBoundaries()} boundaries")

    print("\n== Physics ==")
    for p in tags(comp.physics()):
        ph = comp.physics(p)
        print(f"  {p}: {ph.label()}")
        for ft in tags(ph.feature()):
            f = ph.feature(ft)
            sel = ""
            try:
                sel = f" sel={list(f.selection().entities())[:12]}"
            except Exception:
                pass
            print(f"     {ft:10s} {f.getType()!s:22s} {f.label()!s}{'' if f.isActive() else '  [disabled]'}{sel}")

    print("\n== Mesh ==")
    for mt in tags(comp.mesh()):
        ms = comp.mesh(mt)
        try:
            print(f"  {mt}: {ms.getNumElem()} elements, {ms.getNumVertex()} vertices")
        except Exception as e:
            print(f"  {mt}: not built ({e})")

    print("\n== Studies ==")
    for st in tags(j.study()):
        s = j.study(st)
        print(f"  {st}: {s.label()}")
        for ft in tags(s.feature()):
            f = s.feature(ft)
            extra = ""
            for prop in ("tlist", "activate"):
                try:
                    extra += f" {prop}={list(f.getStringArray(prop))}"
                except Exception:
                    pass
            print(f"     {ft}: {f.getType()} {extra}")

    print("\n== Solutions / datasets ==")
    for s in tags(j.sol()):
        print(f"  sol {s}: {j.sol(s).label()}  study={j.sol(s).study()}")
    for d in tags(j.result().dataset()):
        print(f"  dset {d}: {j.result().dataset(d).label()}")

    print("\n== Plot groups / exports ==")
    for pg in tags(j.result()):
        print(f"  {pg}: {j.result(pg).label()}")
    for e in tags(j.result().export()):
        print(f"  export {e}: {j.result().export(e).label()}")

    client.clear()


if __name__ == "__main__":
    t = time.time()
    main()
    print(f"\nTotal {time.time() - t:.1f} s")
