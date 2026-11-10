"""Put the Ultem material on the MCP holder and polyimide back on the ring in the 3D v4 model (edited in place).

The GUI selection 'dom_holder' (sel12) actually selects the polyimide ring behind the MCP, so the
Ultem ended up on the ring and the holder stayed 304L (eps 1).  Domains are identified by position
(checked against the mesh) before anything is changed:
  holder: r 20..53 mm, z mcp_z-6 .. mcp_z+7.9        -> Ultem 1000 (eps 3.15)
  ring:   r 27.5..69.9 mm, z mcp_z+7.9 .. mcp_z+15.4 -> P25N polyimide (eps 3)

Usage:  .venv\\Scripts\\python.exe scripts\\fix_v4_dielectrics.py
"""
import jpype
import numpy as np

from comsol_session import PROJECT_DIR, load, start

MODEL = PROJECT_DIR / "lens8newMCP_ks_v4_lens_voltages.mph"


def domain_boxes(comp):
    mesh = comp.mesh("mesh1")
    V = np.array([np.array(r) for r in mesh.getVertex()])
    T = np.array([np.array(r) for r in mesh.getElem("tet")]).astype(np.int64)
    E = np.array(mesh.getElemEntity("tet"), dtype=np.int64)
    r = np.hypot(V[0], V[1])
    out = {}
    for d in np.unique(E):
        idx = np.unique(T[:, E == d].ravel())
        out[int(d)] = (r[idx].min(), r[idx].max(), V[2, idx].min(), V[2, idx].max())
    return out


def find(boxes, rmin, rmax, zmin, zmax, tol=0.2):
    hits = [d for d, b in boxes.items()
            if all(abs(a - e) < tol for a, e in zip(b, (rmin, rmax, zmin, zmax)))]
    assert len(hits) == 1, (hits, (rmin, rmax, zmin, zmax))
    return hits[0]


def main():
    client = start()
    model = load(client, MODEL)
    j = model.java
    comp = j.component("comp1")
    mcp = j.param().evaluate("mcp_z") * 1e3
    boxes = domain_boxes(comp)
    holder = find(boxes, 20.0, 52.948, mcp - 6.0, mcp + 7.9)
    ring = find(boxes, 27.499, 69.862, mcp + 7.9, mcp + 15.4)
    print(f"holder = domain {holder}, ring = domain {ring}")

    mats = {str(t): comp.material(t) for t in comp.material().tags()}
    ultem = [t for t, m in mats.items() if "ultem" in str(m.label()).lower()]
    poly = [t for t, m in mats.items() if "polyimide" in str(m.label()).lower()]
    assert len(ultem) == 1 and len(poly) == 1, (ultem, poly)
    mu, mp = mats[ultem[0]], mats[poly[0]]
    eps_u = list(mu.propertyGroup("def").getStringArray("relpermittivity"))
    print(f"{ultem[0]} '{mu.label()}' eps {eps_u[0]}: domains {list(mu.selection().entities(3))} -> [{holder}]")
    mu.selection().set(jpype.JArray(jpype.JInt)([holder]))
    pd = sorted(set(int(d) for d in mp.selection().entities(3)) | {ring})
    print(f"{poly[0]} '{mp.label()}': domains -> {pd}")
    mp.selection().set(jpype.JArray(jpype.JInt)(pd))
    for d in (holder, ring):
        owners = [t for t, m in mats.items() if d in [int(x) for x in m.selection().entities(3)]]
        print(f"  domain {d}: materials {owners} (last one wins)")
    model.save(str(MODEL))
    print(f"saved {MODEL.name}")
    client.clear()


if __name__ == "__main__":
    main()
