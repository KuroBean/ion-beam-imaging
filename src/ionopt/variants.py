"""Model variants made by the editor agent (plan_phase2 7.3; 2D only for now).

A variant is an edited copy of scripts/build_axisym.py and the 2D model it builds, stored with a
manifest under results/variants/<variant_id>/:

  variant.json      VariantManifest (below)
  build_axisym.py   the edited build script
  <model_file>      the built model (.mph, not tracked)

What a variant may add to the base model:
  * parameters      new model parameters. role 'variable': a length the optimizer sweeps inside the
                    inventory range (job.positions[name], metres; planner bounds '<name>_mm');
                    role 'switch': 0/1 set per configuration (job.variant_settings). Every parameter's
                    as_built value reproduces the parent model exactly.
  * parts           new conductors, wired like lens plates (wiring node = part name, potential
                    parameter set from the wiring, boundary selection for potentials and fates)
  * removed_base    base parts that no longer exist (screen_mesh: mesh disc + cross hub)
  * mesh_open_fraction   optical transmission of the (new) screen mesh, 1.0 without one
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .config import Config, ConfigError, ParameterDef

BASE = "base"
MANIFEST = "variant.json"
NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
REMOVABLE_BASE = ("screen_mesh",)


class VariantParam(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(description="optimizer name, lowercase, e.g. mesh_open_diameter")
    comsol_name: str = Field(description="model parameter set by the worker, e.g. d_mesh_open")
    role: Literal["variable", "switch"] = "variable"
    unit: Literal["mm", ""] = "mm"          # variable: mm; switch: dimensionless 0/1
    as_built: float = Field(description="value that reproduces the parent model exactly")
    range: list[float] = Field(description="[lo, hi]: inventory range (variable) or [0, 1] (switch)")
    inventory_item: str | None = None

    @model_validator(mode="after")
    def _check(self):
        if not NAME_RE.match(self.name):
            raise ValueError(f"parameter name '{self.name}': lowercase letters, digits, _")
        if len(self.range) != 2 or self.range[0] > self.range[1]:
            raise ValueError(f"{self.name}: range must be [lo, hi]")
        if self.role == "variable" and self.unit != "mm":
            raise ValueError(f"{self.name}: variable parameters are lengths (unit mm)")
        if self.role == "switch" and (self.unit != "" or self.range != [0, 1] or self.as_built not in (0, 1)):
            raise ValueError(f"{self.name}: switches are dimensionless 0/1 with range [0, 1]")
        return self


class VariantPart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(description="wiring node name, e.g. g1")
    selection: str = Field(description="COMSOL boundary selection of the part, e.g. geom1_G1_bnd")
    potential_param: str = Field(description="model parameter holding its potential, e.g. G1_v")
    connectable: bool = True
    present_when: str | None = Field(None, description="switch parameter that must be 1 for the part to exist")
    inventory_item: str | None = None

    @model_validator(mode="after")
    def _check(self):
        if not NAME_RE.match(self.name):
            raise ValueError(f"part name '{self.name}': lowercase letters, digits, _")
        return self


class VariantManifest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    variant_id: str
    parent: str = BASE
    edit_id: str = ""
    created_at: str = ""
    description: str = ""
    inventory_items: list[str] = []
    script: str = "build_axisym.py"
    model_file: str = "model.mph"
    model_hash: str = ""
    parameters: list[VariantParam] = []
    parts: list[VariantPart] = []
    removed_base: list[Literal["screen_mesh"]] = []
    mesh_open_fraction: float | None = Field(None, gt=0, le=1)
    checks: dict = {}
    approved: bool = False
    approved_at: str | None = None

    @model_validator(mode="after")
    def _unique(self):
        names = [p.name for p in self.parameters] + [p.name for p in self.parts]
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            raise ValueError(f"duplicate names in variant {self.variant_id}: {sorted(dup)}")
        if not NAME_RE.match(self.variant_id.replace("-", "_")):
            raise ValueError(f"variant id '{self.variant_id}': lowercase letters, digits, _ and -")
        return self

    def param(self, name: str) -> VariantParam:
        return next(p for p in self.parameters if p.name == name)

    def variables(self) -> list[VariantParam]:
        return [p for p in self.parameters if p.role == "variable"]

    def switches(self) -> list[VariantParam]:
        return [p for p in self.parameters if p.role == "switch"]


def variants_dir(cfg: Config) -> Path:
    return cfg.path("results_dir") / "variants"


def variant_dir(cfg: Config, variant_id: str) -> Path:
    return variants_dir(cfg) / variant_id


def load_variant(cfg: Config, variant_id: str | None) -> VariantManifest | None:
    """Manifest of a variant; None for the base model."""
    if not variant_id or variant_id == BASE:
        return None
    f = variant_dir(cfg, variant_id) / MANIFEST
    if not f.is_file():
        raise ConfigError(f"unknown model variant '{variant_id}' (no {f})")
    return VariantManifest.model_validate_json(f.read_text(encoding="utf-8"))


def save_variant(cfg: Config, m: VariantManifest) -> Path:
    d = variant_dir(cfg, m.variant_id)
    d.mkdir(parents=True, exist_ok=True)
    (d / MANIFEST).write_text(m.model_dump_json(indent=1), encoding="utf-8")
    return d / MANIFEST


def list_variants(cfg: Config, approved_only: bool = True) -> list[VariantManifest]:
    out = []
    root = variants_dir(cfg)
    for f in sorted(root.glob(f"*/{MANIFEST}")) if root.is_dir() else []:
        m = VariantManifest.model_validate_json(f.read_text(encoding="utf-8"))
        if m.approved or not approved_only:
            out.append(m)
    return out


def model_path(cfg: Config, variant_id: str, fidelity: str) -> Path:
    """Model file of a variant (2D only) or the base model."""
    m = load_variant(cfg, variant_id)
    if m is None:
        return cfg.path(f"models.{fidelity}")
    if fidelity != "2d":
        raise ConfigError(f"variant {variant_id} exists in 2D only")
    return variant_dir(cfg, variant_id) / m.model_file


def registry(m: VariantManifest | None) -> dict[str, ParameterDef]:
    """Registry entries of a variant: its parameters and the potentials of its parts."""
    if m is None:
        return {}
    out = {}
    for p in m.parameters:
        out[p.name] = ParameterDef(name=p.name, comsol_name=p.comsol_name, type="float" if p.role == "variable"
                                   else "int", unit=p.unit or None, default=p.as_built, geometric=True,
                                   description=f"variant {m.variant_id}: {p.role}")
    for part in m.parts:
        out[f"v_{part.name}"] = ParameterDef(name=f"v_{part.name}", comsol_name=part.potential_param, unit="V",
                                             default=0.0, description=f"variant {m.variant_id}: part {part.name}")
    return out


def present_parts(m: VariantManifest | None, settings: dict[str, float]) -> list[VariantPart]:
    """Variant parts that exist with these switch settings (unset switches: as built)."""
    if m is None:
        return []
    sw = {p.name: settings.get(p.name, p.as_built) for p in m.switches()}
    return [p for p in m.parts if p.present_when is None or sw.get(p.present_when, 1) >= 0.5]


def manifest_json(m: VariantManifest) -> str:
    return json.dumps(m.model_dump(mode="json"), indent=1)


def approve_variant(cfg: Config, variant_id: str) -> VariantManifest:
    """Mark a variant approved by the author (planner and validator may then use it in any run)."""
    from .utils import now_iso  # noqa: PLC0415
    m = load_variant(cfg, variant_id)
    if m is None:
        raise ConfigError("the base model needs no approval")
    m = m.model_copy(update={"approved": True, "approved_at": now_iso()})
    save_variant(cfg, m)
    return m
