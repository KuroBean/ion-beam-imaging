"""Where do the 3D mesh elements go?  Per-domain counts, vacuum elements by region, size-node settings.

Usage:  .venv\\Scripts\\python.exe scripts\\mesh_stats_3d.py [3d.mph]
"""
import sys

import numpy as np

from comsol_session import PROJECT_DIR, load, start
from dump_features import props

MODEL = PROJECT_DIR / "lens8newMCP_ks_v4_lens_voltages.mph"


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else str(MODEL)
    client = start()
    model = load(client, path)
    j = model.java
    comp = j.component("comp1")
    par = j.param()
    tip = par.evaluate("tip_z") * 1e3
    z_asm_end = tip + par.evaluate("lens_gap") * 1e3 + 136.165 + 1
    mcp = par.evaluate("mcp_z") * 1e3

    print("== size nodes ==")
    ft = comp.mesh("mesh1").feature("ftet4")
    for t in ft.feature().tags():
        t = str(t)
        f = ft.feature(t)
        p = props(f)
        try:
            named = str(f.selection().named())
        except Exception:
            named = ""
        try:
            d = list(f.selection().dimension())
            n = len(list(f.selection().entities(int(d[0])))) if d else 0
        except Exception:
            d, n = "?", "?"
        keys = [k for k in ("hmax", "hmin", "hgrad", "hcurve", "hnarrow") if p.get(k + "active") in ("on", "true", True)]
        print(f"  {t:12s} '{f.label()}' dim={d} n={n} named='{named}' custom={p.get('custom')} hauto={p.get('hauto')} "
              + " ".join(f"{k}={p.get(k)}" for k in keys))
    p = props(comp.mesh("mesh1").feature("size"))
    print(f"  global size: hauto={p.get('hauto')} custom={p.get('custom')} hmax={p.get('hmax')} hmin={p.get('hmin')} "
          f"hgrad={p.get('hgrad')}")

    mesh = comp.mesh("mesh1")
    V = np.array([np.array(r) for r in mesh.getVertex()])
    T = np.array([np.array(r) for r in mesh.getElem("tet")]).astype(np.int64)
    E = np.array(mesh.getElemEntity("tet"), dtype=np.int64)
    P = V[:, T]                                   # (3, 4, N)
    c = P.mean(axis=1)
    a, b, cc = P[:, 1] - P[:, 0], P[:, 2] - P[:, 0], P[:, 3] - P[:, 0]
    vol = np.abs(np.einsum("ij,ij->j", a, np.cross(b, cc, axis=0))) / 6
    h = (6 * np.sqrt(2) * vol) ** (1 / 3)         # edge of a regular tet with that volume
    r = np.hypot(c[0], c[1])
    z = c[2]
    print(f"\ntotal {len(E)} tets")

    # domain groups
    groups = {}
    for name, sel in (("vacuum", None), ("lens assembly (incl. rods, bracket)", "geom1_uni6_dom"),
                      ("chamber 2 sphere", "geom1_sel9_dom"), ("needle", "geom1_sel1"),
                      ("MCP + surround + ring", "geom1_sel7"), ("screen cross", "geom1_sel6"),
                      ("screen mesh disc", "geom1_sel5")):
        if sel:
            groups[name] = set(int(x) for x in comp.selection(sel).entities(3))
    vac = int(np.bincount(E).argmax())            # largest domain = vacuum
    print(f"vacuum domain = {vac}")
    assigned = set().union(*groups.values()) | {vac}
    for name, ds in groups.items():
        m = np.isin(E, list(ds))
        print(f"  {name:38s} {m.sum():9d} tets  ({len(ds)} domains, median h {np.median(h[m]):.2f} mm)")
    m = ~np.isin(E, list(assigned))
    print(f"  {'other solids (chamber 1, posts, ...)':38s} {m.sum():9d} tets  (median h {np.median(h[m]):.2f} mm)")

    vm = E == vac
    print(f"\nvacuum: {vm.sum()} tets")
    regions = [
        ("needle shank/cone (z < tip, r < 5)", (z < tip) & (r < 5)),
        ("tip..assembly end, r < 7 (beam)", (z >= tip) & (z < z_asm_end) & (r < 7)),
        ("tip..assembly end, 7 <= r < 33 (inside electrodes)", (z >= tip) & (z < z_asm_end) & (r >= 7) & (r < 33)),
        ("tip..assembly end, r >= 33 (outside electrodes)", (z >= tip) & (z < z_asm_end) & (r >= 33)),
        ("drift, assembly end..MCP-20, r < 20", (z >= z_asm_end) & (z < mcp - 20) & (r < 20)),
        ("drift, assembly end..MCP-20, r >= 20", (z >= z_asm_end) & (z < mcp - 20) & (r >= 20)),
        ("MCP/screen region MCP-20..MCP+20", (z >= mcp - 20) & (z < mcp + 20)),
        ("behind MCP (z > MCP+20)", z >= mcp + 20),
        ("before needle (z < tip, r >= 5)", (z < tip) & (r >= 5)),
    ]
    for name, m in regions:
        m = m & vm
        if m.any():
            print(f"  {name:52s} {m.sum():9d}  median h {np.median(h[m]):6.2f} mm  min h {h[m].min():.3f}")
    # outside the chamber walls (between chamber outer surface and the bounding cylinder)
    out = vm & (r > 102)
    print(f"  {'(of these) r > 102 mm, outside chamber 1 flanges':52s} {out.sum():9d}  median h {np.median(h[out]):6.2f} mm")
    np.savez_compressed(PROJECT_DIR / "logs" / "mesh_stats_3d.npz", r=r, z=z, h=h, E=E, vac=vac)
    client.clear()


if __name__ == "__main__":
    main()
