"""Build an (r, z) description of every boundary of the 3D geometry.

For each boundary: r/z extents of its mesh vertices, shape class
(z-plane, cylinder, other), azimuthal coverage (360 deg = fully axisymmetric
surface), adjacent domains, their materials, and the physics features using it.

Outputs logs/boundary_table.csv and logs/domain_table.csv.

Usage:  .venv\\Scripts\\python.exe scripts\\boundary_table.py
"""
import csv

import numpy as np

from comsol_session import PROJECT_DIR, load, start

OUT = PROJECT_DIR / "logs"


def jarr(a):
    return np.array([np.array(row) for row in a])


def main():
    client = start()
    model = load(client)
    j = model.java
    comp = j.component("comp1")
    geom = comp.geom("geom1")
    mesh = comp.mesh("mesh1")
    V = jarr(mesh.getVertex())
    T = jarr(mesh.getElem("tri")).T.astype(int)
    E = np.array(mesh.getElemEntity("tri"), dtype=int)
    nb = geom.getNBoundaries()
    nd = geom.getNDomains()
    updown = jarr(geom.getUpDown()).astype(int)  # (2, nb), 0 = outside

    dom_mat = {d: "" for d in range(0, nd + 1)}
    for t in comp.material().tags():
        m = comp.material(t)
        try:
            for d in m.selection().entities(3):
                dom_mat[int(d)] = str(m.label()).split(" [")[0]
        except Exception:
            pass
    dom_tet = np.zeros(nd + 1, int)
    try:
        tet_ent = np.array(mesh.getElemEntity("tet"), dtype=int)
        dom_tet = np.bincount(tet_ent, minlength=nd + 1)
    except Exception:
        pass

    bnd_feats = {b: [] for b in range(1, nb + 1)}
    for ph in comp.physics().tags():
        for ft in comp.physics(ph).feature().tags():
            f = comp.physics(ph).feature(ft)
            try:
                ents = f.selection().entities(2)
            except Exception:
                continue
            if f.getType() in ("ChargeConservation", "init"):
                continue
            label = f"{ph}/{ft}"
            if f.getType() == "ElectricPotential":
                label += f"({f.getString('V0')}V)"
            for b in ents:
                bnd_feats[int(b)].append(label)
    np.savez_compressed(OUT / "mesh3d.npz", V=V, T=T, E=E, updown=updown)
    client.clear()

    r = np.hypot(V[0], V[1])
    phi = np.degrees(np.arctan2(V[1], V[0]))
    z = V[2]
    rows = []
    for b in range(1, nb + 1):
        vid = np.unique(T[E == b])
        if len(vid) == 0:
            continue
        rb, zb, pb = r[vid], z[vid], phi[vid]
        # azimuthal coverage: largest gap in sorted angles
        ps = np.sort(pb)
        gaps = np.diff(np.concatenate([ps, ps[:1] + 360]))
        cover = 360 - gaps.max() if len(ps) > 1 else 0
        zspan, rspan = zb.max() - zb.min(), rb.max() - rb.min()
        if zspan < 0.02:
            shape = "zplane"
        elif rspan < 0.02:
            shape = "cylinder"
        else:
            # cone / sphere test: points on a line in (r,z)?
            A = np.c_[rb, np.ones_like(rb)]
            res = np.linalg.lstsq(A, zb, rcond=None)[1]
            shape = "cone" if len(res) and res[0] / len(rb) < 1e-3 else "other"
        up, dn = updown[0, b - 1], updown[1, b - 1]
        rows.append(dict(
            bnd=b, shape=shape, rmin=round(rb.min(), 3), rmax=round(rb.max(), 3),
            zmin=round(zb.min(), 3), zmax=round(zb.max(), 3), azim_cover=round(cover, 1),
            xc=round(V[0, vid].mean(), 2), yc=round(V[1, vid].mean(), 2),
            up=up, down=dn, mat_up=dom_mat.get(up, "") if up else "OUTSIDE",
            mat_down=dom_mat.get(dn, "") if dn else "OUTSIDE",
            physics=" ".join(bnd_feats[b]),
        ))
    with open(OUT / "boundary_table.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    drows = []
    for d in range(1, nd + 1):
        bs = [row for row in rows if d in (row["up"], row["down"])]
        drows.append(dict(
            dom=d, material=dom_mat.get(d, ""), n_tets=int(dom_tet[d]) if d < len(dom_tet) else 0,
            rmin=min(x["rmin"] for x in bs), rmax=max(x["rmax"] for x in bs),
            zmin=min(x["zmin"] for x in bs), zmax=max(x["zmax"] for x in bs), n_bnd=len(bs),
        ))
    with open(OUT / "domain_table.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(drows[0].keys()))
        w.writeheader()
        w.writerows(drows)
    print(f"wrote {len(rows)} boundaries, {len(drows)} domains")


if __name__ == "__main__":
    main()
