"""Editor agent (plan_phase2 7.3): builds inventory parts into a 2D model variant.

The LLM edits a copy of the parent's build script (scripts/build_axisym.py or an approved variant's)
in a sandbox folder; it has file tools only (no shell). Everything after that is deterministic:

  1. static checks   only build_axisym.py changed; imports and calls on an allow-list; the reported
                     parameters and parts exist in the script
  2. build           the script builds the variant model (subprocess, COMSOL ~1 min)
  3. equivalence     at its as-built values the variant reproduces a stored run of the parent
                     (skipped when the variant removes a base part: nothing to compare)
  4. smoke           new parts present, sweep variables mid-range: the checker must call the run valid,
                     and no new part may overlap a stack part
  5. author approval (graph interrupt), then the variant is usable in any run

A failed check goes back to the editor with its message (loop.editor_attempts calls per edit).
Check solves count against the run's solve budget (EditResult.n_solves).
"""
from __future__ import annotations

import ast
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from .. import units
from ..checker import check
from ..electrodes import JobValidationError, validate_job
from ..schemas import FILES, JobSpec, new_job_id
from ..utils import now_iso
from ..variants import (BASE, VariantManifest, VariantParam, VariantPart, load_variant, save_variant,
                        variant_dir)
from .llm import LLMError
from .roles import LoopContext, call_dir, record_call, template
from .schemas import EditRequest, EditResult, NewParameter
from .state import LoopState

SCRIPT = "build_axisym.py"
PARENT = "parent_build_axisym.py"
NOTES = "COMSOL_API_NOTES.md"
REQUEST = "REQUEST.md"
SANDBOX_FILES = {SCRIPT, PARENT, NOTES, REQUEST}
ALLOWED_IMPORTS = {"argparse", "time", "math", "jpype", "comsol_session"}
FORBIDDEN_NAMES = {"open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars", "getattr", "setattr",
                   "delattr", "input", "breakpoint", "os", "sys", "subprocess", "shutil", "socket", "pathlib",
                   "importlib", "builtins", "urllib", "requests", "glob"}
FORBIDDEN_ATTRS = {"system", "popen", "Popen", "unlink", "rmtree", "rmdir", "remove_file", "write_text",
                   "write_bytes", "mkdir", "rename", "chmod", "spawn", "run_path"}
EQ_TOL_UM = 10.0          # equivalence: landing positions within 10 um (MCP resolution sigma 70 um)
EQ_TOL_EV = 0.05

Builder = Callable[[Path, Path, Path, float], tuple[bool, str]]


class _S(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EditorParam(_S):
    name: str = Field(description="optimizer name: lowercase letters, digits, _ (e.g. mesh_open_diameter)")
    comsol_name: str = Field(description="the parameter name you added to PARAMS")
    role: Literal["variable", "switch"] = Field(description="variable: a length the optimizer sweeps; "
                                                            "switch: 0/1 presence of a new part")
    inventory_item: str | None = Field(None, description="inventory id it implements")
    inventory_param: str | None = Field(None, description="for a variable: the inventory parameter it implements")
    as_built: float = Field(description="variable: its value in mm that reproduces the parent exactly; switch: 0")


class EditorPart(_S):
    name: str = Field(description="wiring name of a new conductor: lowercase, e.g. g1")
    selection: str = Field(description="its boundary selection, geom1_<TAG>_bnd")
    potential_param: str = Field(description="the potential parameter you added, e.g. G1_v")
    present_when: str | None = Field(None, description="name (EditorParam.name) of the switch that makes it exist")
    inventory_item: str | None = None


class EditorReport(_S):
    summary: str = Field(description="what you changed, in words, for the author")
    parameters: list[EditorParam] = Field(default_factory=list)
    parts: list[EditorPart] = Field(default_factory=list)
    removed_base: list[Literal["screen_mesh"]] = Field(default_factory=list)
    notes: str = ""


# --------------------------------------------------------------------------- static checks


def static_problems(script: str) -> list[str]:
    """Imports and calls outside the allow-list (the script runs on the author's machine)."""
    try:
        tree = ast.parse(script)
    except SyntaxError as e:
        return [f"{SCRIPT} does not parse: {e}"]
    p = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            bad = [a.name for a in node.names if a.name.split(".")[0] not in ALLOWED_IMPORTS]
        elif isinstance(node, ast.ImportFrom):
            bad = [node.module or "."] if (node.module or "").split(".")[0] not in ALLOWED_IMPORTS else []
        else:
            bad = []
        if bad:
            p.append(f"line {node.lineno}: import {bad} not allowed (allowed: {sorted(ALLOWED_IMPORTS)})")
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            p.append(f"line {node.lineno}: '{node.id}' is not allowed (no file, process or network access)")
        if isinstance(node, ast.Attribute) and node.attr in FORBIDDEN_ATTRS:
            p.append(f"line {node.lineno}: '.{node.attr}' is not allowed")
    return sorted(set(p))


def report_problems(rep: EditorReport, script: str, items: dict, cfg) -> list[str]:
    """The report must match the script and the inventory."""
    p = []
    for x in rep.parameters:
        if not re.search(rf'["\']{re.escape(x.comsol_name)}["\']', script):
            p.append(f"parameter {x.comsol_name} is not in {SCRIPT}")
        if x.role == "variable":
            item = items.get(x.inventory_item)
            if item is None or x.inventory_param not in item.parameters:
                p.append(f"variable {x.name}: inventory_item/inventory_param must name one of the requested items' "
                         f"parameters ({ {i: list(it.parameters) for i, it in items.items()} })")
        elif x.as_built != 0:
            p.append(f"switch {x.name}: as_built must be 0 (the new part is absent in the parent)")
    switches = {x.name for x in rep.parameters if x.role == "switch"}
    for part in rep.parts:
        tag = re.match(r"geom1_(\w+)_bnd$", part.selection)
        if tag is None or not re.search(rf'["\']{re.escape(tag.group(1))}["\']', script):
            p.append(f"part {part.name}: selection {part.selection} must be geom1_<TAG>_bnd of a feature in the script")
        if not re.search(rf'["\']{re.escape(part.potential_param)}["\']', script):
            p.append(f"part {part.name}: potential parameter {part.potential_param} is not in {SCRIPT}")
        if part.present_when is not None and part.present_when not in switches:
            p.append(f"part {part.name}: present_when {part.present_when} is not a reported switch")
    nodes = set(cfg.constraints.supplies.low_voltage.connectable) | {"tip"}
    p += [f"part name {x.name} is already a wiring node" for x in rep.parts if x.name in nodes]
    return p


# --------------------------------------------------------------------------- build


def build_model(script: Path, out: Path, log: Path, timeout_s: float) -> tuple[bool, str]:
    """Run the edited build script (python -P: the sandbox folder is not on sys.path)."""
    scripts = Path(__file__).resolve().parents[3] / "scripts"
    env = {**os.environ, "PYTHONPATH": str(scripts) + os.pathsep + os.environ.get("PYTHONPATH", "")}
    cmd = [sys.executable, "-P", str(script), "--out", str(out), "--solve", "--particles"]
    try:
        r = subprocess.run(cmd, cwd=str(script.parent), env=env, capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        log.write_text(f"timeout after {timeout_s} s", encoding="utf-8")
        return False, f"build timed out after {timeout_s:.0f} s"
    text = (r.stdout or "") + "\n" + (r.stderr or "")
    log.write_text(text, encoding="utf-8")
    ok = r.returncode == 0 and out.is_file()
    return ok, "" if ok else "\n".join(text.strip().splitlines()[-25:])


def fake_build(script: Path, out: Path, log: Path, timeout_s: float) -> tuple[bool, str]:
    """Mock backend: no COMSOL; the script only has to parse."""
    out.write_bytes(b"")
    log.write_text("mock build (no COMSOL)", encoding="utf-8")
    return True, ""


# --------------------------------------------------------------------------- runs


def reference_job(ctx: LoopContext, parent: str) -> JobSpec | None:
    """Latest valid 2D run of the parent model on this backend (equivalence reference)."""
    rd = ctx.cfg.path("results_dir")
    with ctx.db() as rl:
        rows = rl._rows("SELECT j.job_id FROM jobs j JOIN metrics m ON m.job_id=j.job_id WHERE j.fidelity='2d' "
                        "AND j.backend=? AND m.valid=1 ORDER BY j.created_at DESC LIMIT 200",
                        (getattr(ctx.backend, "name", ""),))
    for r in rows:
        f = rd / r["job_id"] / FILES["job"]
        if f.is_file():
            job = JobSpec.model_validate_json(f.read_text(encoding="utf-8"))
            if job.variant_id == parent and (rd / r["job_id"] / FILES["ions_final"]).is_file():
                return job
    return None


def variant_job(base: JobSpec, m: VariantManifest, mid: bool, purpose: str, wiring: dict | None = None) -> JobSpec:
    """The reference settings on a variant: as built (mid=False) or new parts on, variables mid-range."""
    pos = {k: v for k, v in base.positions.items()}
    for x in m.variables():
        pos[x.name] = (0.5 * (x.range[0] + x.range[1]) if mid else x.as_built) * units.MM
    settings = {x.name: (1.0 if mid else x.as_built) for x in m.switches()}
    return base.model_copy(update={
        "job_id": new_job_id(), "variant_id": m.variant_id, "variant_settings": settings, "positions": pos,
        "wiring": {**base.wiring, **(wiring or {})}, "mesh_open_fraction": m.mesh_open_fraction,
        "tags": {**base.tags, "purpose": purpose, "variant": m.variant_id}})


def _final(d: Path) -> pd.DataFrame:
    return pd.read_csv(d / FILES["ions_final"]).set_index("ion_id").sort_index()


def compare_runs(a: Path, b: Path) -> dict:
    fa, fb = _final(a), _final(b)
    both = fa["z_m"].notna() & fb["z_m"].notna()
    r = lambda f: np.hypot(f["x_m"], f["y_m"])  # noqa: E731
    out = {"n_ions": int(len(fa)), "same_lost": bool((fa["z_m"].isna() == fb["z_m"].isna()).all()),
           "max_dr_um": float((r(fa) - r(fb))[both].abs().max() / units.UM) if both.any() else 0.0,
           "max_dz_um": float((fa["z_m"] - fb["z_m"])[both].abs().max() / units.UM) if both.any() else 0.0,
           "max_dKE_eV": float((fa["KE_eV"] - fb["KE_eV"])[both].abs().max()) if both.any() else 0.0}
    out["ok"] = (out["same_lost"] and out["max_dr_um"] <= EQ_TOL_UM and out["max_dz_um"] <= EQ_TOL_UM
                 and out["max_dKE_eV"] <= EQ_TOL_EV)
    return out


def overlap_problems(result_dir: Path) -> list[str]:
    """New parts (measured in the model) against the stack parts' bounding boxes."""
    geom = json.loads((result_dir / FILES["geometry"]).read_text(encoding="utf-8"))
    new = [e for e in geom.get("electrodes", []) if e.get("kind") == "variant_part"]
    old = [e for e in geom.get("electrodes", []) if e.get("kind") != "variant_part"]
    p = []
    for a in new:
        for b in old:
            dz = abs(a["z_m"] - b["z_m"]) - (a["thickness_m"] + b["thickness_m"]) / 2
            dr = min(a["r_out_m"], b["r_out_m"]) - max(a["r_in_m"], b["r_in_m"])
            if dz < 0 and dr > 0:
                p.append(f"new part {a['name']} overlaps {b['name']} (z {a['z_m'] / units.MM:.2f} mm, "
                         f"r {a['r_in_m'] / units.MM:.2f}..{a['r_out_m'] / units.MM:.2f} mm)")
    return p


# --------------------------------------------------------------------------- the agent


def editor_prompt(req: EditRequest, items: dict, parent: VariantManifest | None, feedback: list[str]) -> str:
    inv = "\n".join(f"- {i}: {json.dumps(it.model_dump(mode='json'))}" for i, it in items.items())
    par = "the as-built base model" if parent is None else \
        f"variant {parent.variant_id}: {json.dumps(parent.model_dump(mode='json', exclude={'checks'}))}"
    parts = [f"# Edit request\n{json.dumps(req.model_dump(mode='json'), indent=1)}",
             f"# Inventory items to build in\n{inv}",
             f"# Parent model\n{par}",
             f"# Files\nEdit {SCRIPT} in this folder: {PARENT} is the unchanged parent, {NOTES} has COMSOL API notes."]
    if feedback:
        parts.append("# Your previous attempt failed these checks; fix the script in place\n"
                     + "\n".join(f"- {f}" for f in feedback))
    return "\n\n".join(parts)


class Editor:
    """ctx.editor: (EditRequest, LoopState, LoopContext, sandbox) -> EditResult."""

    def __init__(self, builder: Builder | None = None):
        self.builder = builder

    def __call__(self, req: EditRequest, state: LoopState, ctx: LoopContext, sandbox: Path) -> EditResult:
        cfg, lp = ctx.cfg, ctx.acfg.loop
        round_ = state.budget.rounds_used + 1
        vid = f"v-{state.run_id}-{sandbox.name}".lower().replace("_", "-")
        parent = load_variant(cfg, req.parent_variant)
        items = {i: cfg.inventory.get(i) for i in req.inventory_items}
        builder = self.builder or (fake_build if getattr(ctx.backend, "name", "") == "mock" else build_model)
        parent_script = (Path(__file__).resolve().parents[3] / "scripts" / SCRIPT) if parent is None else \
            variant_dir(cfg, parent.variant_id) / parent.script
        script = sandbox / SCRIPT
        if not script.is_file():
            shutil.copyfile(parent_script, script)
            shutil.copyfile(parent_script, sandbox / PARENT)
            notes = cfg.root_dir / "docs" / "comsol_api_notes.md"
            if notes.is_file():
                shutil.copyfile(notes, sandbox / NOTES)
        system, t_hash = template(ctx, "editor")
        feedback: list[str] = []
        n_solves = 0
        checks: dict[str, bool] = {}
        for _ in range(lp.editor_attempts):
            prompt = editor_prompt(req, items, parent, feedback)
            (sandbox / REQUEST).write_text(prompt, encoding="utf-8")
            call_id, cdir = call_dir(ctx, state.run_id, round_, "editor")
            try:
                rec = ctx.llm.call("editor", system, prompt, EditorReport, cdir, add_dirs=[sandbox])
            except LLMError as e:
                record_call(ctx, call_id, state.run_id, round_, "editor", None, t_hash, error=str(e), cdir=cdir,
                            model=ctx.acfg.role("editor").model)
                return EditResult(ok=False, variant_id="", script_path="", diff_summary="", n_solves=n_solves,
                                  notes=f"editor call failed: {e}")
            record_call(ctx, call_id, state.run_id, round_, "editor", rec, t_hash)
            rep: EditorReport = rec.output
            feedback, checks = [], {}

            # ---- 1. static checks
            text = script.read_text(encoding="utf-8")
            extra = sorted(f.name for f in sandbox.iterdir() if f.is_file() and f.name not in SANDBOX_FILES
                           and f.suffix in (".py", ".pyc", ".pth"))
            feedback += [f"only {SCRIPT} may be edited; remove {extra}"] if extra else []
            feedback += static_problems(text) + report_problems(rep, text, items, cfg)
            if text == (sandbox / PARENT).read_text(encoding="utf-8"):
                feedback.append(f"{SCRIPT} is unchanged")
            checks["static"] = not feedback
            if feedback:
                continue
            try:
                m = self._manifest(vid, req, rep, items, parent, state, sandbox)
            except ValueError as e:
                feedback.append(f"report does not form a valid variant: {e}")
                continue

            # ---- 2. build (one COMSOL at a time: release the loop's client first)
            if hasattr(ctx.backend, "close"):
                ctx.backend.close()
            vdir = variant_dir(cfg, vid)
            vdir.mkdir(parents=True, exist_ok=True)
            ok, err = builder(script, vdir / m.model_file, sandbox / "build.log", lp.editor_build_timeout_s)
            checks["build"] = ok
            if not ok:
                feedback.append(f"the build failed:\n{err}")
                continue
            shutil.copyfile(script, vdir / SCRIPT)

            # ---- 3. equivalence with the parent (as-built values)
            ref = reference_job(ctx, req.parent_variant)
            if ref is None:
                feedback.append(f"no stored valid 2D run of the parent {req.parent_variant} to compare with "
                                f"(run one optimizer round on it first)")
                checks["equivalence"] = False
                break                                      # not the editor's fault: retrying cannot help
            eq_note = "n/a: the variant removes a base part"
            if not m.removed_base:
                wide = m.model_copy(update={"parameters": [x.model_copy(update={"range": [
                    min(x.range[0], x.as_built), max(x.range[1], x.as_built)]}) for x in m.parameters]})
                save_variant(cfg, wide)
                job = variant_job(ref, wide, mid=False, purpose="editor_equivalence")
                res = ctx.backend.run(job, cfg.backend.job_timeout_s)
                n_solves += 1
                if res.status != "success":
                    feedback.append(f"the variant at its as-built values did not run: {res.error}")
                    checks["equivalence"] = False
                    continue
                cmp = compare_runs(cfg.path("results_dir") / ref.job_id, Path(res.result_dir))
                eq_note = json.dumps(cmp)
                checks["equivalence"] = cmp["ok"]
                if not cmp["ok"]:
                    feedback.append(f"at its as-built values the variant does not reproduce the parent run "
                                    f"{ref.job_id[:8]}: {cmp} (tolerance {EQ_TOL_UM} um, {EQ_TOL_EV} eV). Every new "
                                    f"parameter's default must give the parent's geometry; new parts must be off.")
                    continue
            save_variant(cfg, m)

            # ---- 4. smoke run: new parts on, variables mid-range
            wiring = {p.name: req.supply for p in m.parts if req.supply and req.supply != "GND"}
            job = variant_job(ref, m, mid=True, purpose="editor_smoke", wiring=wiring)
            try:
                validate_job(job, cfg)
            except JobValidationError as e:
                feedback.append(f"smoke settings are invalid: {e}")
                checks["smoke_valid"] = False
                continue
            res = ctx.backend.run(job, cfg.backend.job_timeout_s)
            n_solves += 1
            if res.status != "success":
                feedback.append(f"the smoke run failed: {res.error}")
                checks["smoke_valid"] = False
                continue
            met = check(Path(res.result_dir), cfg)
            checks["smoke_valid"] = bool(met.valid)
            over = overlap_problems(Path(res.result_dir)) if m.parts else []
            checks["no_overlap"] = not over
            if not met.valid or over:
                feedback += ([f"the smoke run is not valid: {met.flags}"] if not met.valid else []) + over
                continue

            m = m.model_copy(update={"checks": {**checks, "equivalence_detail": eq_note,
                                                "smoke_job_id": job.job_id, "reference_job_id": ref.job_id}})
            save_variant(cfg, m)
            diff = "".join(difflib.unified_diff(
                (sandbox / PARENT).read_text(encoding="utf-8").splitlines(True), text.splitlines(True),
                fromfile=f"{req.parent_variant}/{SCRIPT}", tofile=f"{vid}/{SCRIPT}"))
            (vdir / "edit.diff").write_text(diff, encoding="utf-8")
            n_add = sum(1 for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++"))
            n_del = sum(1 for ln in diff.splitlines() if ln.startswith("-") and not ln.startswith("---"))
            return EditResult(
                ok=True, variant_id=vid, script_path=str(vdir / SCRIPT),
                diff_summary=f"{rep.summary} (+{n_add} / -{n_del} lines; {vdir / 'edit.diff'})",
                new_parameters=[NewParameter(name=x.name, unit=x.unit, default=x.as_built, lo=x.range[0], hi=x.range[1])
                                for x in m.parameters],
                checks=checks, smoke_job_id=job.job_id, n_solves=n_solves,
                new_parts=[p.name for p in m.parts], new_switches=[x.name for x in m.switches()],
                notes=f"equivalence: {eq_note}. {rep.notes}".strip())
        return EditResult(ok=False, variant_id=vid, script_path=str(script), diff_summary="", checks=checks,
                          n_solves=n_solves, notes="; ".join(feedback)[:2000])

    @staticmethod
    def _manifest(vid: str, req: EditRequest, rep: EditorReport, items: dict, parent: VariantManifest | None,
                  state: LoopState, sandbox: Path) -> VariantManifest:
        params = []
        for x in rep.parameters:
            if x.role == "variable":
                rng = items[x.inventory_item].parameters[x.inventory_param].range
                params.append(VariantParam(name=x.name, comsol_name=x.comsol_name, role="variable", unit="mm",
                                           as_built=x.as_built, range=list(rng), inventory_item=x.inventory_item))
            else:
                params.append(VariantParam(name=x.name, comsol_name=x.comsol_name, role="switch", unit="",
                                           as_built=0, range=[0, 1], inventory_item=x.inventory_item))
        inherited = list(parent.parameters) if parent else []
        trans = [it.transmission for it in items.values() if it.replaces == "screen_mesh" and it.transmission]
        removed = sorted(set(rep.removed_base) | set(parent.removed_base if parent else []))
        return VariantManifest(
            variant_id=vid, parent=req.parent_variant, edit_id=f"{state.run_id}/{sandbox.name}", created_at=now_iso(),
            description=rep.summary, inventory_items=list(req.inventory_items) + (parent.inventory_items if parent else []),
            script=SCRIPT, model_file="model.mph", parameters=inherited + params,
            parts=(list(parent.parts) if parent else []) + [VariantPart(**p.model_dump()) for p in rep.parts],
            removed_base=removed,
            mesh_open_fraction=trans[0] if trans else (parent.mesh_open_fraction if parent else None))


__all__ = ["Editor", "EditorReport", "static_problems", "build_model", "fake_build", "BASE"]
