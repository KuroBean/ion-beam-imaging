"""COMSOL model adapter (plan 9.5): the ONLY place that knows COMSOL node tags and property names.

Every tag and property here was confirmed by introspection (docs/comsol_api_notes.md). The adapter
loads a base model once, then per job: sets the registry parameters, rebuilds geometry and mesh when
a geometric parameter changed, points a ReleaseFromDataFile node at the job's release file, solves
std1 (electrostatics) then std2 (particles), and writes the raw files (schemas.FILES). The base model
is never saved.

Coordinates: the models use a chamber frame with the tip apex at tip_z; everything written out is in
plan coordinates (z = z_model - tip_z, metres).
"""
from __future__ import annotations

import hashlib
import logging
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .. import units
from ..config import Config
from ..electrodes import expected_potentials, geometry_electrodes, stack_layout
from ..launch import write_release_file
from ..schemas import FILES, FINAL_COLUMNS, JobSpec
from ..utils import write_json

log = logging.getLogger(__name__)

# --------------------------------------------------------------------------- tags (both models)
COMP, GEOM, MESH = "comp1", "geom1", "mesh1"
PHYS_ES, PHYS_CPT = "es", "cpt"
STD_ES, STD_PT, STEP_PT = "std1", "std2", "time"
SOL_ES, SOL_PT, SOLVER_TIME = "sol1", "sol2", "t1"
DSET_ES = "dset1"
TIP_Z, MCP_Z = "tip_z", "mcp_z"                       # model parameters read (never set) by the adapter
RELEASE_TYPES = ("ReleaseFromDataFile", "ParticleBeam", "Release", "Inlet", "ReleaseFromGrid",
                 "ReleaseFromPoint", "ReleaseFromEdge", "ReleaseFromBoundary", "ReleaseFromDomain")
GEOMETRIC = ("cfg", "lens_gap", "mesh_gap", "z_mcp")  # registry names whose change needs a rebuild
Z_POSITIONS = ("z_mcp",)                              # plan z (from the tip apex); model value = z + tip_z
UNIT_SI = {None: 1.0, "": 1.0, "mm": units.MM, "um": units.UM, "us": units.US, "V": 1.0, "kg": 1.0}

# per-fidelity: release node, result expressions, numerical feature types, and the selection behind
# each plan selection name (sel_*). A list = union of several selections.
FIDELITY: dict[str, dict[str, Any]] = {
    "2d": {
        "release_tag": "relf1", "icolv": 2,
        "pos": ("qr", "qz"), "vel": ("cpt.vr", "cpt.vz"), "r_expr": "r", "z_expr": "z",
        "num": {"min": "MinLine", "max": "MaxLine", "av": "AvLine"}, "cutpoint": "CutPoint2D",
        "selections": {"sel_tip": "geom1_needle_bnd", "sel_e{k}": "geom1_L{k}_bnd",
                       "sel_d1": "geom1_D1_bnd", "sel_d2": "geom1_D2_bnd",
                       "sel_mesh_plane": "geom1_meshline_bnd", "sel_mesh_frame": "geom1_hub_bnd",
                       "sel_mcp_face": "geom1_bnd_mcpfront"},
    },
    "3d": {
        "release_tag": "relf_job", "icolv": 3,
        "pos": ("qx", "qy", "qz"), "vel": ("cpt.vx", "cpt.vy", "cpt.vz"), "r_expr": "sqrt(x^2+y^2)", "z_expr": "z",
        "num": {"min": "MinSurface", "max": "MaxSurface", "av": "AvSurface"}, "cutpoint": "CutPoint3D",
        # electrodes / deflector halves are imported parts, found by label (import order may change)
        "label_selections": {"sel_e{k}": "L{k} (Import lens assembly)", "sel_d1a": "D1a (Import lens assembly)",
                             "sel_d1b": "D1b (Import lens assembly)", "sel_d2a": "D2a (Import lens assembly)",
                             "sel_d2b": "D2b (Import lens assembly)"},
        "selections": {"sel_tip": "adj5", "sel_d1": ["sel_d1a", "sel_d1b"], "sel_d2": ["sel_d2a", "sel_d2b"],
                       "sel_mesh_plane": "adj3", "sel_mesh_frame": "adj2", "sel_mcp_face": "geom1_sel3"},
    },
}


class AdapterError(RuntimeError):
    """A job cannot run on this model (missing parameter, unsafe change, inconsistent geometry)."""


def file_hash(path: Path, chunk: int = 1 << 24) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def _jstr(xs):
    import jpype
    return jpype.JArray(jpype.JString)([str(x) for x in xs])


@dataclass
class ModelAdapter:
    client: Any
    cfg: Config
    fidelity: str
    path: Path = field(init=False)
    model: Any = field(init=False, default=None)
    model_hash: str = field(init=False, default="")
    sel: dict[str, Any] = field(init=False, default_factory=dict)       # plan selection -> model selection(s)
    model_params: set[str] = field(init=False, default_factory=set)
    _geom_state: dict[str, str] = field(init=False, default_factory=dict)

    def __post_init__(self):
        if self.fidelity not in FIDELITY:
            raise ValueError(f"unknown fidelity {self.fidelity!r}")
        self.F = FIDELITY[self.fidelity]
        self.path = self.cfg.path(f"models.{self.fidelity}")

    # ------------------------------------------------------------------ setup

    @property
    def j(self):
        return self.model.java

    def load(self) -> None:
        t = time.time()
        self.model = self.client.load(str(self.path))
        log.info("loaded %s in %.0f s", self.path.name, time.time() - t)
        self.model_hash = file_hash(self.path)
        self.model_params = {str(n) for n in self.j.param().varnames()}
        self._resolve_selections()
        self._prepare_release()
        self._geom_state = {}       # unknown -> first job rebuilds unless values match the stored model

    def _resolve_selections(self) -> None:
        comp = self.j.component(COMP)
        tags = [str(t) for t in comp.selection().tags()]
        by_label: dict[str, list[str]] = {}
        for t in tags:
            by_label.setdefault(str(comp.selection(t).label()), []).append(t)
        n = self.cfg.constraints.electrodes.count
        out: dict[str, Any] = {}

        def expand_k(d):
            for key, val in d.items():
                ks = range(1, n + 1) if "{k}" in key else [None]
                for k in ks:
                    yield (key.replace("{k}", str(k)) if k else key,
                           val.replace("{k}", str(k)) if (k and isinstance(val, str)) else val)

        for key, label in expand_k(self.F.get("label_selections", {})):
            cands = [t for t in by_label.get(label, []) if t.endswith("_bnd")]
            if len(cands) != 1:
                raise AdapterError(f"{self.path.name}: expected one boundary selection labelled '{label}', got {cands}")
            out[key] = cands[0]
        for key, val in expand_k(self.F["selections"]):
            out[key] = val
        for key, val in out.items():
            for s in (val if isinstance(val, list) else [val]):
                if s not in tags and s not in out:
                    raise AdapterError(f"{self.path.name}: selection '{s}' (for {key}) not found")
        self.sel = out

    def _prepare_release(self) -> None:
        cpt = self.j.component(COMP).physics(PHYS_CPT)
        rel_tag = self.F["release_tag"]
        for t in [str(x) for x in cpt.feature().tags()]:
            f = cpt.feature(t)
            if t != rel_tag and str(f.getType()) in RELEASE_TYPES and f.isActive():
                log.info("disabling release feature %s (%s)", t, f.getType())
                f.active(False)
        if rel_tag not in [str(x) for x in cpt.feature().tags()]:
            cpt.create(rel_tag, "ReleaseFromDataFile")
        rel = cpt.feature(rel_tag)
        if str(rel.getType()) != "ReleaseFromDataFile":
            raise AdapterError(f"cpt/{rel_tag} is {rel.getType()}, expected ReleaseFromDataFile")
        rel.active(True)

    # ------------------------------------------------------------------ parameters

    def _named_selection_names(self, key: str) -> list[str]:
        v = self.sel[key]
        out = []
        for s in (v if isinstance(v, list) else [v]):
            out += self._named_selection_names(s) if s in self.sel else [s]
        return out

    def param_value(self, expr: str) -> float:
        return float(self.j.param().evaluate(expr))

    def set_params(self, params: dict[str, Any], job: JobSpec) -> tuple[dict[str, str], list[str], bool]:
        """Write registry parameters to the model. Returns (comsol expressions set, notes, geometry_changed)."""
        reg = self.cfg.registry()
        set_exprs: dict[str, str] = {}
        notes: list[str] = []
        missing = []
        tip = self.param_value(TIP_Z)
        for name, value in params.items():
            if name in Z_POSITIONS:
                value = value + tip          # plan -> model frame (plan section 3)
            d = reg[name]
            if d.comsol_name is None:
                notes.append(f"{name} not modelled (no comsol_name); value {value} not applied")
                continue
            if name == "z_mcp" and job.cfg != 1:
                continue                     # fixed by the chamber in cfg 2/3; checked after the update
            if d.comsol_name not in self.model_params:
                missing.append(f"{name} -> {d.comsol_name}")
                continue
            if d.type == "int":
                expr = str(int(value))
            elif d.type == "bool":
                expr = "1" if value else "0"
            else:
                expr = f"{float(value) / UNIT_SI[d.unit]!r}" + (f"[{d.unit}]" if d.unit else "")
            set_exprs[d.comsol_name] = expr
        if missing:
            raise AdapterError(f"{self.path.name} lacks parameters needed by this job: {missing}")

        geo_names = {reg[n].comsol_name for n in GEOMETRIC if n in params and reg[n].comsol_name}
        before = {n: str(self.j.param().get(n)) for n in geo_names}
        changed = any(before[n] != set_exprs.get(n, before[n]) for n in geo_names)
        stored_matches = all(math.isclose(self.param_value(n), self.param_value(set_exprs[n]) if n in set_exprs
                                          else self.param_value(n), rel_tol=0, abs_tol=1e-12) for n in geo_names)
        if self.fidelity == "3d" and not stored_matches and not self.cfg.backend.worker.allow_3d_geometry_change:
            raise AdapterError("this 3D job changes the geometry (cfg/lens_gap/mesh_gap/z_mcp) but the 3D model "
                               "still has numeric selections that a rebuild can silently break (KNOWN_ISSUES #13); "
                               "set backend.worker.allow_3d_geometry_change=true to override")
        for n, e in set_exprs.items():
            self.j.param().set(n, e)
        rebuild = changed if self._geom_state else not stored_matches
        self._geom_state = {n: set_exprs.get(n, before[n]) for n in geo_names}
        return set_exprs, notes, rebuild

    def check_positions(self, job: JobSpec) -> dict[str, float]:
        """Model geometry (plan coordinates) after the update; must match the job."""
        tip = self.param_value(TIP_Z)
        z_mcp = self.param_value(MCP_Z) - tip
        lens_gap = self.param_value("lens_gap")
        tol = 1e-7
        bad = []
        if abs(z_mcp - job.positions["z_mcp"]) > tol:
            bad.append(f"model MCP face at z = {z_mcp / units.MM:.4f} mm, job z_mcp = {job.positions['z_mcp'] / units.MM:.4f} mm"
                       + ("" if job.cfg == 1 else f" (fixed in cfg {job.cfg})"))
        if abs(lens_gap - job.positions["lens_gap"]) > tol:
            bad.append(f"model lens_gap {lens_gap / units.MM:.4f} mm != job {job.positions['lens_gap'] / units.MM:.4f} mm")
        if bad:
            raise AdapterError("; ".join(bad))
        return {"tip_z_model_m": tip, "z_mcp_m": z_mcp, "lens_gap_m": lens_gap}

    # ------------------------------------------------------------------ evaluation helpers

    def _field_boundaries(self, ents: list[int]) -> list[int]:
        """Boundaries that touch a domain where es solves for V (others, e.g. a conductor's edge on the
        symmetry axis, have V undefined and make any average fail)."""
        comp = self.j.component(COMP)
        sdim = int(comp.geom(GEOM).getSDim())
        es_dom = {int(e) for e in comp.physics(PHYS_ES).selection().entities(sdim)}
        up, down = (np.array(list(r), int) for r in comp.geom(GEOM).getUpDown())
        return [b for b in ents if up[b - 1] in es_dom or down[b - 1] in es_dom]

    def _numerical(self, kind: str, key: str, exprs: list[str], field_only: bool = False) -> list[float]:
        num = self.j.result().numerical()
        tag = f"ad_{kind}"
        if tag in [str(t) for t in num.tags()]:
            num.remove(tag)
        n = num.create(tag, self.F["num"][kind])
        n.set("data", DSET_ES)
        names = self._named_selection_names(key)
        if len(names) == 1 and not field_only:
            n.selection().named(names[0])
        else:
            comp = self.j.component(COMP)
            dim = int(list(comp.selection(names[0]).dimension())[0])
            ents = sorted({int(e) for s in names for e in comp.selection(s).entities(dim)})
            if field_only:
                ents = self._field_boundaries(ents)
            if not ents:
                raise AdapterError(f"{key}: no boundaries with a defined field")
            n.selection().geom(GEOM, dim)
            n.selection().set(ents)
        n.set("expr", _jstr(exprs))
        vals = [float(row[0]) for row in n.getReal()]
        num.remove(tag)
        return vals

    def eval_points(self, coords_model: np.ndarray, exprs: list[str]) -> np.ndarray:
        """[len(exprs), n] at model-coordinate points (mm): 2D rows (r, z), 3D rows (x, y, z)."""
        import jpype
        ds = self.j.result().dataset()
        num = self.j.result().numerical()
        for t, coll in (("ad_cp", ds), ("ad_ev", num)):
            if t in [str(x) for x in coll.tags()]:
                coll.remove(t)
        cp = ds.create("ad_cp", self.F["cutpoint"])
        cp.set("data", DSET_ES)
        for i, ax in enumerate(("pointx", "pointy", "pointz")[:coords_model.shape[0]]):
            cp.set(ax, " ".join(f"{v:.9g}" for v in coords_model[i]))
        ev = num.create("ad_ev", "EvalPoint")
        ev.set("data", "ad_cp")
        ev.set("expr", jpype.JArray(jpype.JString)(exprs))
        raw = ev.getReal()
        out = np.array([np.array(list(row), float) for row in raw])
        num.remove("ad_ev")
        ds.remove("ad_cp")
        return out.reshape(len(exprs), -1)

    def particle_all(self, exprs: list[str]) -> np.ndarray:
        """[len(exprs), particle, time] at all output times of the particle solution."""
        ds = self.j.result().dataset()
        num = self.j.result().numerical()
        for t, coll in (("ad_part", ds), ("ad_pev", num)):
            if t in [str(x) for x in coll.tags()]:
                coll.remove(t)
        ds.create("ad_part", "Particle").set("solution", SOL_PT)
        ev = num.create("ad_pev", "Particle")
        ev.set("data", "ad_part")
        ev.set("innerinput", "all")
        ev.set("evaluate", "all")
        out = []
        for e in exprs:
            ev.set("expr", e)
            out.append(np.array([np.array(list(row), float) for row in ev.getReal()]))
        num.remove("ad_pev")
        ds.remove("ad_part")
        return np.array(out)

    # ------------------------------------------------------------------ run

    def run(self, job: JobSpec, params: dict[str, Any], ions: pd.DataFrame, out_dir: Path,
            deadline: float | None = None) -> dict:
        """Run one job; writes raw files into out_dir and returns metadata for meta.json."""
        timings: dict[str, float] = {}

        def stage(name):
            if deadline is not None and time.time() > deadline:
                from ..results import JobTimeout
                raise JobTimeout(f"job exceeded backend.job_timeout_s before stage '{name}'")
            timings[name] = time.time()

        def done(name):
            timings[name] = round(time.time() - timings[name], 2)

        if self.fidelity == "3d" and "mesh_gap" in params and "mesh_gap" not in self.model_params:
            raise AdapterError("3D model has no mesh_gap parameter yet (author adds it in the GUI)")
        stage("params")
        set_exprs, notes, rebuild = self.set_params(params, job)
        pos = self.check_positions(job)
        done("params")
        if not rebuild and int(self.j.component(COMP).mesh(MESH).getNumElem()) == 0:
            # saved without a mesh (e.g. after a GUI edit): the stored geometry state may also be stale
            # (3D v6 as saved: 54 domains, empty dom_cross_posts; 58 and correct after geom.run())
            rebuild = True
            notes.append("model had no stored mesh: rebuilt geometry and mesh (same parameters)")
        if rebuild:
            stage("geometry_mesh")
            self.j.component(COMP).geom(GEOM).run()
            self.j.component(COMP).mesh(MESH).run()
            done("geometry_mesh")
        tip_m = pos["tip_z_model_m"]

        # release file
        stage("release")
        rel_file = out_dir / "release.txt"
        axis_off = (self.cfg.spec.launch.axis_offset_nm or 0.0) * units.NM
        write_release_file(ions, rel_file, self.fidelity, z_shift_m=tip_m, axis_offset_m=axis_off)
        import jpype
        rel = self.j.component(COMP).physics(PHYS_CPT).feature(self.F["release_tag"])
        rel.set("Filename", str(rel_file))
        rel.set("icolp", jpype.JInt(0))
        rel.set("InitialVelocity", "FromFile")
        rel.set("icolv", jpype.JInt(self.F["icolv"]))
        rel.importData()
        done("release")

        # particle solver tolerance (re-fetch the node: running a study regenerates the solver features)
        self.j.sol(SOL_PT).feature(SOLVER_TIME).set("rtol", repr(self.cfg.backend.worker.particle_rtol))
        for std, name in ((STD_ES, "solve_es"), (STD_PT, "solve_pt")):
            stage(name)
            self.j.study(std).run()
            done(name)

        stage("export")
        n_ions = self._export(job, params, ions, out_dir, tip_m, pos)
        done("export")
        comp = self.j.component(COMP)
        return {"params": params, "model_file": self.path.name, "model_hash": self.model_hash,
                "comsol_version": str(self.client.version), "mesh_elements": int(comp.mesh(MESH).getNumElem()),
                "n_ions": n_ions, "comsol_params": set_exprs, "adapter_notes": notes, "rebuilt_geometry": rebuild,
                "timings_s": timings, "model_positions_m": pos,
                "particle_rtol": str(self.j.sol(SOL_PT).feature(SOLVER_TIME).getString("rtol"))}

    # ------------------------------------------------------------------ export

    def _export(self, job: JobSpec, params: dict, ions: pd.DataFrame, out: Path, tip_m: float, pos: dict) -> int:
        F = self.F
        tip_mm = tip_m / units.MM
        ions.to_csv(out / FILES["ions_launch"], index=False)

        # ---- particles: all output times
        # V and cpt.Ep are evaluated by COMSOL at each particle's position, inside the domain the particle
        # is in (a point evaluation right at a conductor surface averages in the excluded side -> undefined)
        arr = self.particle_all(["t"] + list(F["pos"]) + list(F["vel"]) + ["V", "cpt.Ep"])
        t, Vp, Ep = arr[0], arr[-2], arr[-1]
        arr = arr[:-2]
        if self.fidelity == "2d":
            r, z, vr, vz = arr[1:]
            x, y, vx, vy = r, np.zeros_like(r), vr, np.zeros_like(r)
        else:
            x, y, z, vx, vy, vz = arr[1:]
        n = x.shape[0]
        if n != len(ions):
            raise AdapterError(f"COMSOL released {n} particles, the release file has {len(ions)}")
        # last finite state and the time it stopped moving (frozen at a wall) or t_end
        fin = np.isfinite(z)
        last = np.where(fin.any(axis=1), fin.shape[1] - 1 - np.argmax(fin[:, ::-1], axis=1), -1)
        idx = np.arange(n)
        pick = lambda a: np.where(last >= 0, a[idx, np.maximum(last, 0)], np.nan)  # noqa: E731
        xf, yf, zf, vxf, vyf, vzf = (pick(a) for a in (x, y, z, vx, vy, vz))
        moved = np.abs(np.diff(np.nan_to_num(z), axis=1)) + np.abs(np.diff(np.nan_to_num(x), axis=1)) > 1e-12
        stop = np.where(moved.any(axis=1), moved.shape[1] - np.argmax(moved[:, ::-1], axis=1), 0)
        stop = np.minimum(stop, np.maximum(last, 0))
        t_stop = np.where(last >= 0, t[idx, stop], np.nan)
        ke = pick(Ep) / units.E_CHARGE                     # COMSOL kinetic energy (J) -> eV
        v_end = pick(Vp)
        v_start = Vp[:, 0]
        mm = units.MM
        final = pd.DataFrame({
            "ion_id": ions.sort_values("ion_id")["ion_id"].to_numpy(),      # release-file row i = ion_id i
            "x_m": xf * mm, "y_m": yf * mm, "z_m": (zf - tip_mm) * mm,
            "vx_mps": vxf, "vy_mps": vyf, "vz_mps": vzf, "KE_eV": ke, "t_s": t_stop,
            "V_start_V": v_start, "V_end_V": v_end})[FINAL_COLUMNS]
        final.to_csv(out / FILES["ions_final"], index=False)

        # trajectories (subsampled, plots only)
        step = max(1, t.shape[1] // 100)
        k = np.arange(0, t.shape[1], step)
        pd.DataFrame({"ion_id": np.repeat(final["ion_id"].to_numpy(), len(k)), "t_s": t[:, k].ravel(),
                      "x_m": (x[:, k] * mm).ravel(), "y_m": (y[:, k] * mm).ravel(),
                      "z_m": ((z[:, k] - tip_mm) * mm).ravel()}).dropna().to_csv(out / FILES["traj"], index=False)

        # ---- fields: axis and r-z plane, tip apex to the MCP face
        z_mcp_mm = pos["z_mcp_m"] / mm
        za = np.linspace(1e-3, z_mcp_mm - 1e-3, 800)
        axis = np.vstack([np.full_like(za, 1e-6), za + tip_mm]) if self.fidelity == "2d" else \
            np.vstack([np.zeros_like(za), np.zeros_like(za), za + tip_mm])
        ez_expr = "es.Ez"
        V, Ez = self.eval_points(axis, ["V", ez_expr])
        pd.DataFrame({"z_m": za * mm, "V_V": V, "Ez_Vpm": Ez}).to_csv(out / FILES["axis_potential"], index=False)
        geom_el = geometry_electrodes(job, self.cfg)
        r_max = 1.5 * max(e["r_out_m"] for e in geom_el) / mm
        rr, zz = np.meshgrid(np.linspace(0, r_max, 40), np.linspace(0, z_mcp_mm, 250))
        pts = np.vstack([rr.ravel(), zz.ravel() + tip_mm]) if self.fidelity == "2d" else \
            np.vstack([rr.ravel(), np.zeros(rr.size), zz.ravel() + tip_mm])
        Vg, Eg = self.eval_points(pts, ["V", "es.normE"])
        pd.DataFrame({"r_m": rr.ravel() * mm, "z_m": zz.ravel() * mm, "V_V": Vg, "Emag_Vpm": Eg}).to_csv(
            out / FILES["cutplane_field"], index=False)

        # ---- electrode potentials (mean V on each plan selection)
        rows = []
        for key in expected_potentials(job, self.cfg):
            rows.append((key, self._numerical("av", key, ["V"], field_only=True)[0]))
        pd.DataFrame(rows, columns=["selection", "V_mean_V"]).to_csv(out / FILES["electrode_potentials"], index=False)

        # ---- geometry.json: stack from config, cross-checked against the model; detector from the model
        rz = [F["z_expr"], F["r_expr"]]
        checks = {}
        for e in geom_el:
            zmin, rmin = self._numerical("min", e["selection"], rz)
            zmax, rmax = self._numerical("max", e["selection"], rz)
            checks[e["name"]] = {"z_min_m": (zmin - tip_mm) * mm, "z_max_m": (zmax - tip_mm) * mm,
                                 "r_min_m": rmin * mm, "r_max_m": rmax * mm}
            front_model = (zmin - tip_mm) * mm
            front_cfg = e["z_m"] - e["thickness_m"] / 2
            if abs(front_model - front_cfg) > 0.05 * mm:
                raise AdapterError(f"{e['name']}: model front face at {front_model / mm:.3f} mm, "
                                   f"constraints.electrodes stack says {front_cfg / mm:.3f} mm")
        fz0, fr0 = self._numerical("min", "sel_mesh_frame", rz)
        fz1, fr1 = self._numerical("max", "sel_mesh_frame", rz)
        mz0, _ = self._numerical("min", "sel_mesh_plane", rz)
        mz1, mr1 = self._numerical("max", "sel_mesh_plane", rz)
        _, r_mcp = self._numerical("max", "sel_mcp_face", rz)
        la = job.launch
        geom = {
            "source": f"comsol:{self.path.name}", "fidelity": self.fidelity, "cfg": job.cfg,
            "z_tip_m": 0.0, "z_launch_m": (la.launch_offset_um or 0.0) * units.UM,
            "z_mcp_m": pos["z_mcp_m"], "r_mcp_active_m": r_mcp * mm,
            "z_mesh_m": (0.5 * (mz0 + mz1) - tip_mm) * mm, "r_mesh_open_m": fr0 * mm,
            "mesh_frame_z_m": [(fz0 - tip_mm) * mm, (fz1 - tip_mm) * mm], "mesh_frame_r_m": [fr0 * mm, fr1 * mm],
            "electrodes": geom_el, "model_boxes": checks,
            "lens_gap_m": pos["lens_gap_m"], "t_end_s": params["t_end"],
        }
        write_json(out / FILES["geometry"], geom)
        return n
