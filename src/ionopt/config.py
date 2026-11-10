"""Configuration: loading, validation, overrides, TBD handling and snapshots (plan section 4).

All adjustable values live in YAML files under config/. Each file becomes one top-level
section of :class:`Config` (``cfg.spec``, ``cfg.constraints``, ...). The models keep the
units written in the key names (mm, kV, eV, deg); SI values come from properties or
from :mod:`ionopt.units` at the point of use.

``null`` in a file means TBD. Loading succeeds; :meth:`Config.require` raises
:class:`TBDError` naming the exact key when a step needs a TBD value.
"""
from __future__ import annotations

import copy
import fnmatch
import hashlib
import json
import math
import os
from pathlib import Path
from typing import Annotated, Any, Iterable, Literal

import yaml
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from . import units

CONFIG_FILES = ("paths", "parameters", "spec", "constraints", "backend", "optimizer", "b0_configs")
CONFIG_DIR_ENV = "IONOPT_CONFIG_DIR"
# keys where null means "not used" rather than TBD (fnmatch patterns over dotted keys)
NOT_TBD = (
    "parameters.parameters.*.unit",
    "parameters.parameters.*.allowed",
    "spec.analysis.spline_smoothing",
    "backend.mock.fold_theta_deg",           # null = no fold
    "constraints.electrodes.deflectors.*.plate_mm",   # optional (defaults to length)
    "constraints.electrodes.stack.*.plate_mm",
    "spec.requirements.impact_threshold_mps",   # alternative to impact_threshold_eV_per_charge
)


class ConfigError(Exception):
    """Invalid configuration (bad file, bad value, unknown override key)."""


class TBDError(ConfigError):
    """A value needed by the current step is still null (TBD) in the config files."""

    def __init__(self, key: str):
        self.key = key
        super().__init__(f"{key} is TBD; set it in config/{key.split('.')[0]}.yaml")


# --------------------------------------------------------------------------- helpers


def _check_range(v: list | None) -> list | None:
    if v is None:
        return v
    if len(v) != 2:
        raise ValueError("range must be [min, max]")
    lo, hi = v
    if lo is not None and hi is not None and lo > hi:
        raise ValueError(f"min {lo} is larger than max {hi}")
    return v


Range = Annotated[list[float | None], AfterValidator(_check_range)]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


def range_known(r: list | None) -> bool:
    return r is not None and r[0] is not None and r[1] is not None


# --------------------------------------------------------------------------- paths


class PathsConfig(_Model):
    comsol_root: str | None = None
    models: dict[str, str | None] = {}
    queue_dir: str = "queue"
    results_dir: str = "results"
    db_path: str = "results/runlog.sqlite"
    optuna_db_path: str = "results/optuna.sqlite"


# --------------------------------------------------------------------------- parameter registry


class ParameterDef(_Model):
    name: str
    comsol_name: str | None = None
    type: Literal["float", "int", "bool"] = "float"
    unit: str | None = None
    allowed: list[Any] | None = None
    per_electrode: bool = False
    description: str = ""

    @model_validator(mode="after")
    def _template(self):
        if self.per_electrode and "{k}" not in self.name:
            raise ValueError(f"per_electrode parameter '{self.name}' must contain {{k}} in its name")
        return self


class ParametersConfig(_Model):
    parameters: list[ParameterDef]

    @field_validator("parameters")
    @classmethod
    def _unique(cls, v):
        names = [p.name for p in v]
        dup = {n for n in names if names.count(n) > 1}
        if dup:
            raise ValueError(f"duplicate parameter names: {sorted(dup)}")
        return v


# --------------------------------------------------------------------------- spec


class LaunchConfig(_Model):
    hwhm_deg: float = Field(gt=0)
    theta_max_deg: float = Field(gt=0, lt=90)
    n_theta: int | None = Field(None, ge=2)
    n_E: int | None = Field(None, ge=1)
    n_phi: int | None = Field(None, ge=1)
    E0_eV: float | None = Field(None, gt=0)
    dE_eV: float = Field(0.0, ge=0)
    charge: int = 1
    mass_Da: float | None = Field(None, gt=0)
    launch_offset_um: float | None = Field(None, ge=0)
    axis_offset_nm: float = Field(1.0, ge=0)
    t_end_us: float | None = Field(None, gt=0)
    convergence_ion_factor: int = Field(2, ge=1)

    @field_validator("charge")
    @classmethod
    def _nonzero(cls, v):
        if v == 0:
            raise ValueError("charge must be nonzero")
        return v

    @model_validator(mode="after")
    def _energy(self):
        if self.E0_eV is not None and self.E0_eV - self.dE_eV / 2 <= 0:
            raise ValueError(f"E0_eV - dE_eV/2 must be > 0 (got E0 {self.E0_eV}, dE {self.dE_eV})")
        return self

    @property
    def sigma_rad(self) -> float:
        """Gaussian sigma of dI/dOmega in radians from the HWHM."""
        return self.hwhm_deg * units.DEG / math.sqrt(2 * math.log(2))


class DetectorConfig(_Model):
    model: str = ""
    mcp_active_diameter_mm: float = Field(gt=0)
    sigma_mcp_um: float | None = Field(None, ge=0)
    mesh_opening_diameter_mm: float | None = Field(None, gt=0)
    mesh_open_fraction: float | None = Field(None, gt=0, le=1)


class RequirementsConfig(_Model):
    eta_min: float | None = Field(None, ge=0, le=1)
    impact_threshold_eV_per_charge: float | None = Field(None, ge=0)
    impact_threshold_mps: float | None = Field(None, ge=0)
    threshold_species_mass_Da: float | None = Field(None, gt=0)
    frac_fast_min: float = Field(0.9, ge=0, le=1)
    optional_constraints: dict[str, float] = {}

    @field_validator("optional_constraints")
    @classmethod
    def _keys(cls, v):
        bad = [k for k in v if not (k.startswith("min_") or k.startswith("max_"))]
        if bad:
            raise ValueError(f"optional constraint keys must start with min_ or max_: {bad}")
        return v

    @model_validator(mode="after")
    def _one_threshold(self):
        if self.impact_threshold_eV_per_charge is not None and self.impact_threshold_mps is not None:
            raise ValueError("set impact_threshold_eV_per_charge OR impact_threshold_mps, not both")
        return self


class TolerancesConfig(_Model):
    energy_conservation_rel: float | None = Field(None, gt=0)
    potential_match_V: float | None = Field(None, ge=0)
    monotonic_tol_um: float | None = Field(None, ge=0)
    convergence_rel: float | None = Field(None, gt=0)
    fate_position_tol_um: float | None = Field(None, ge=0)
    eval_range_landed_frac: float = Field(0.99, gt=0, le=1)


class AnalysisConfig(_Model):
    drdtheta_method: Literal["central", "spline"] = "central"
    spline_smoothing: float | None = Field(None, ge=0)


class SpecConfig(_Model):
    launch: LaunchConfig
    detector: DetectorConfig
    requirements: RequirementsConfig
    tolerances: TolerancesConfig
    analysis: AnalysisConfig = AnalysisConfig()


# --------------------------------------------------------------------------- constraints


class ChamberSetup(_Model):
    name: str = ""
    z_mcp_mm: Range = [None, None]
    mesh_gap_mm: Range = [None, None]
    lens_gap_mm: Range = [None, None]      # tip apex to the L1 (E1) front face


class MeshConstraints(_Model):
    min_gap_to_mcp_mm: float | None = Field(None, ge=0)


class StackPart(_Model):
    """One part of the fixed lens stack, positioned relative to the E1 (L1) front face."""
    front_mm: float = Field(ge=0)          # front face, measured from the E1 front face along +z
    length_mm: float = Field(gt=0)         # full axial extent including lips (bounding box)
    plate_mm: float | None = Field(None, gt=0)   # plate thickness without lips (field checks)
    r_in_mm: float = Field(ge=0)
    r_out_mm: float = Field(gt=0)

    @model_validator(mode="after")
    def _radii(self):
        if self.r_in_mm >= self.r_out_mm:
            raise ValueError("r_in_mm must be smaller than r_out_mm")
        return self


class Deflector(StackPart):
    name: str                              # d1, d2; halves are <name>a / <name>b
    cfgs: list[int]                        # chamber setups in which the deflector exists


class ElectrodeConstraints(_Model):
    count: int = Field(9, ge=1)
    stack: list[StackPart] = []            # E1..E9 in order
    deflectors: list[Deflector] = []
    deflectors_grounded: bool = True       # Phase 1: every deflector half at 0 V
    clearance_mm: float | None = Field(None, gt=0)   # smallest gap between neighbouring plates

    @model_validator(mode="after")
    def _stack(self):
        if self.stack and len(self.stack) != self.count:
            raise ValueError(f"electrodes.stack has {len(self.stack)} entries, count is {self.count}")
        fr = [e.front_mm for e in self.stack]
        if fr != sorted(fr) or (fr and fr[0] != 0):
            raise ValueError("electrodes.stack front_mm must start at 0 (E1) and increase")
        return self


class LowVoltage(_Model):
    channels: list[str]
    range_V: Range = [None, None]
    connectable: list[str]


class HighVoltage(_Model):
    range_V: Range = [None, None]
    roles: dict[str, str]

    @field_validator("roles")
    @classmethod
    def _roles(cls, v):
        need = {"mcp_front", "mcp_back", "phosphor", "mesh"}
        if set(v.values()) != need or len(v) != 4:
            raise ValueError(f"high-voltage roles must map 4 ports one-to-one onto {sorted(need)}")
        return v


class Supplies(_Model):
    low_voltage: LowVoltage
    high_voltage: HighVoltage
    mcp_front_V: Range = [None, None]
    mesh_V: Range = [None, None]
    mcp_back_offset_V: float | None = None
    phosphor_offset_V: float | None = None

    def hv_port(self, role: str) -> str:
        return next(p for p, r in self.high_voltage.roles.items() if r == role)


class Electrical(_Model):
    max_field_kV_per_mm: float | None = Field(None, gt=0)


class ConstraintsConfig(_Model):
    chamber_setups: dict[int, ChamberSetup]
    mesh: MeshConstraints = MeshConstraints()
    electrodes: ElectrodeConstraints = ElectrodeConstraints()
    supplies: Supplies
    electrical: Electrical = Electrical()


# --------------------------------------------------------------------------- backend / optimizer


class WorkerConfig(_Model):
    count: int = Field(1, ge=1)
    restart_after_jobs: int = Field(20, ge=1)
    output_steps: int = Field(500, ge=10)        # particle output times per run: dt_out = t_end / output_steps
    allow_3d_geometry_change: bool = False       # 3D models still have numeric selections (KNOWN_ISSUES #13)
    particle_rtol: float = Field(1e-9, gt=0, lt=1)   # particle solver relative tolerance (sol2/t1 rtol)


class SSHConfig(_Model):
    host_env_var: str = "IONOPT_SSH_HOST"
    remote_queue_dir_env_var: str = "IONOPT_SSH_QUEUE_DIR"


class MockConfig(_Model):
    seed: int = 0
    f0: float = Field(gt=0)
    lens_channel: str = "LV2"
    lens_opt_V: float = 0.0
    lens_scale_V: float = Field(1.0, gt=0)
    mesh_opt_V: float = 0.0
    mesh_scale_V: float = Field(1.0, gt=0)
    chroma_min_m_per_eV: float = Field(0.0, ge=0)
    chroma_coeff_m_per_eV: float = Field(0.0, ge=0)
    fold_theta_deg: float | None = Field(None, gt=0)
    noise_r_um: float = Field(0.0, ge=0)
    energy_noise_eV: float = Field(0.0, ge=0)
    failure_rate: float = Field(0.0, ge=0, le=1)
    timeout_rate: float = Field(0.0, ge=0, le=1)
    missing_file_rate: float = Field(0.0, ge=0, le=1)


class BackendConfig(_Model):
    backend: Literal["mock", "queue"] = "mock"
    transport: Literal["local", "ssh"] = "local"
    poll_interval_s: float = Field(2.0, gt=0)
    job_timeout_s: float = Field(1800.0, gt=0)
    worker: WorkerConfig = WorkerConfig()
    ssh: SSHConfig = SSHConfig()
    mock: MockConfig


class OptimizerConfig(_Model):
    sampler: Literal["auto", "gp", "tpe"] = "auto"
    seed: int = 0
    n_startup_trials: int = Field(10, ge=1)
    default_budget: int = Field(50, ge=1)
    nonevaluable_score_deg: float = Field(90.0, gt=0)
    write_plots: bool = False


# --------------------------------------------------------------------------- b0 configurations


class ConfigurationDef(_Model):
    """A structural configuration: chamber setup and wiring (plan 7.2, fixed stack).

    wiring maps the tip and electrodes e1..e9 to LV1..LV4 or GND; nodes not listed are GND.
    """

    config_id: str
    description: str = ""
    cfg: int
    wiring: dict[str, str] = {}


class B0Config(_Model):
    configurations: list[ConfigurationDef] = []

    @field_validator("configurations")
    @classmethod
    def _unique(cls, v):
        ids = [c.config_id for c in v]
        dup = {i for i in ids if ids.count(i) > 1}
        if dup:
            raise ValueError(f"duplicate config_id: {sorted(dup)}")
        return v

    def get(self, config_id: str) -> ConfigurationDef:
        for c in self.configurations:
            if c.config_id == config_id:
                return c
        raise ConfigError(f"unknown config_id '{config_id}'; known: {[c.config_id for c in self.configurations]}")


# --------------------------------------------------------------------------- root


class Config(_Model):
    paths: PathsConfig
    parameters: ParametersConfig
    spec: SpecConfig
    constraints: ConstraintsConfig
    backend: BackendConfig
    optimizer: OptimizerConfig
    b0_configs: B0Config

    # not part of the files
    root_dir: Path = Field(default=Path("."), exclude=True)
    overrides: list[str] = Field(default_factory=list, exclude=True)

    @model_validator(mode="after")
    def _cross_checks(self):
        cs = self.constraints
        known = set(cs.chamber_setups)
        if not known:
            raise ValueError("constraints.chamber_setups is empty")
        cfg_param = next((p for p in self.parameters.parameters if p.name == "cfg"), None)
        if cfg_param and cfg_param.allowed and set(cfg_param.allowed) != known:
            raise ValueError(f"parameters cfg.allowed {cfg_param.allowed} != constraints.chamber_setups {sorted(known)}")
        if self.backend.mock.lens_channel not in cs.supplies.low_voltage.channels:
            raise ValueError(f"backend.mock.lens_channel '{self.backend.mock.lens_channel}' is not an LV channel")
        for c in self.b0_configs.configurations:
            if c.cfg not in known:
                raise ValueError(f"b0_configs '{c.config_id}': cfg {c.cfg} is not a chamber setup")
        return self

    # ---- access helpers -------------------------------------------------

    def resolved(self) -> dict:
        """Fully resolved config as plain JSON-compatible data (defaults included)."""
        return self.model_dump(mode="json")

    def config_hash(self) -> str:
        return _hash(self.resolved())

    def spec_hash(self) -> str:
        return _hash(self.resolved()["spec"])

    def path(self, key: str) -> Path:
        """Absolute path for a key in paths.yaml (e.g. 'results_dir', 'models.2d')."""
        val = self.require(f"paths.{key}")
        p = Path(val)
        return p if p.is_absolute() else (self.root_dir / p)

    def get(self, key: str) -> Any:
        """Value at a dotted key (e.g. 'spec.detector.sigma_mcp_um'); None if TBD."""
        return _walk(self.resolved(), key.split("."), key)

    def require(self, key: str) -> Any:
        """Value at a dotted key; raises TBDError if it (or part of a range) is null."""
        v = self.get(key)
        if v is None or (isinstance(v, list) and any(x is None for x in v)):
            raise TBDError(key)
        return v

    def list_tbd(self) -> list[str]:
        """Dotted keys still null (TBD). Optional keys where null means 'not used' are skipped."""
        out: list[str] = []
        _collect_tbd(self.resolved(), "", out)
        req = self.spec.requirements
        skip = list(NOT_TBD)
        if req.impact_threshold_eV_per_charge is not None or req.impact_threshold_mps is not None:
            skip.append("spec.requirements.impact_threshold_*")
        return [k for k in out if not any(fnmatch.fnmatchcase(k, pat) for pat in skip)]

    def registry(self) -> dict[str, ParameterDef]:
        """Parameter registry with per-electrode templates expanded (k = 1..count)."""
        out: dict[str, ParameterDef] = {}
        n = self.constraints.electrodes.count
        for p in self.parameters.parameters:
            if p.per_electrode:
                for k in range(1, n + 1):
                    d = p.model_dump()
                    d["name"] = p.name.replace("{k}", str(k))
                    d["comsol_name"] = p.comsol_name.replace("{k}", str(k)) if p.comsol_name else None
                    d["per_electrode"] = False
                    out[d["name"]] = ParameterDef(**d)
            else:
                out[p.name] = p
        return out

    def chamber(self, cfg: int) -> ChamberSetup:
        try:
            return self.constraints.chamber_setups[cfg]
        except KeyError:
            raise ConfigError(f"cfg {cfg} is not a chamber setup; known: {sorted(self.constraints.chamber_setups)}")

    def with_overrides(self, overrides: Iterable[str]) -> "Config":
        """New Config with extra --set style overrides applied on top of this one."""
        raw = self.resolved()
        overrides = list(overrides)
        for o in overrides:
            _apply_set(raw, o)
        return _validate(raw, self.root_dir, self.overrides + overrides)


# --------------------------------------------------------------------------- loading


def find_config_dir(start: Path | None = None) -> Path:
    env = os.environ.get(CONFIG_DIR_ENV)
    if env:
        return Path(env)
    here = (start or Path.cwd()).resolve()
    for d in (here, *here.parents):
        if (d / "config" / "spec.yaml").is_file():
            return d / "config"
    raise ConfigError(f"no config/ directory found above {here} (or set {CONFIG_DIR_ENV})")


def load_config(config_dir: Path | str | None = None, overrides: Iterable[str] = (),
                override_files: Iterable[Path | str] = ()) -> Config:
    """Load, override and validate all config files.

    overrides: strings 'section.key.sub=value' (value parsed as YAML).
    override_files: partial YAML files deep-merged over the config (keys must exist).
    """
    cdir = Path(config_dir) if config_dir else find_config_dir()
    raw: dict[str, Any] = {}
    for name in CONFIG_FILES:
        f = cdir / f"{name}.yaml"
        if not f.is_file():
            raise ConfigError(f"missing config file {f}")
        try:
            raw[name] = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"cannot parse {f}: {e}") from e
    applied: list[str] = []
    for of in override_files:
        of = Path(of)
        try:
            data = yaml.safe_load(of.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError) as e:
            raise ConfigError(f"cannot read override file {of}: {e}") from e
        _deep_merge_strict(raw, data, str(of), "")
        applied.append(f"@file:{of.as_posix()}")
    for o in overrides:
        _apply_set(raw, o)
        applied.append(o)
    return _validate(raw, cdir.resolve().parent, applied)


def load_snapshot(path: Path | str, root_dir: Path | str | None = None) -> Config:
    """Load a config_snapshot.yaml written by write_snapshot."""
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    overrides = data.pop("_overrides", [])
    data.pop("_config_hash", None)
    root = Path(root_dir) if root_dir else Path(data.pop("_root_dir", "."))
    data.pop("_root_dir", None)
    return _validate(data, root, overrides)


def write_snapshot(cfg: Config, path: Path | str) -> str:
    """Write the fully resolved config; returns its hash."""
    data = cfg.resolved()
    h = _hash(data)
    out = {"_config_hash": h, "_overrides": cfg.overrides, "_root_dir": str(cfg.root_dir), **data}
    Path(path).write_text(yaml.safe_dump(out, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return h


def _validate(raw: dict, root: Path, overrides: list[str]) -> Config:
    try:
        return Config.model_validate({**raw, "root_dir": root, "overrides": overrides})
    except ValidationError as e:
        lines = []
        for err in e.errors():
            loc = ".".join(str(x) for x in err["loc"])
            lines.append(f"  {loc}: {err['msg']}")
        raise ConfigError("invalid configuration:\n" + "\n".join(lines)) from None


def _hash(data: Any) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


# --------------------------------------------------------------------------- dotted-key walking


def _child(node: Any, seg: str, full: str) -> tuple[Any, Any]:
    """Return (key_or_index, child) for one path segment; raises ConfigError if absent."""
    if isinstance(node, dict):
        if seg in node:
            return seg, node[seg]
        if seg.lstrip("-").isdigit() and int(seg) in node:
            return int(seg), node[int(seg)]
        raise ConfigError(f"unknown config key '{full}' (no '{seg}'; available: {sorted(map(str, node))})")
    if isinstance(node, list):
        if seg.isdigit() and int(seg) < len(node):
            return int(seg), node[int(seg)]
        for i, item in enumerate(node):
            if isinstance(item, dict) and seg in (item.get("name"), item.get("config_id")):
                return i, item
        raise ConfigError(f"unknown config key '{full}' (no list item '{seg}')")
    raise ConfigError(f"unknown config key '{full}' ('{seg}' is below a value, not a section)")


def _walk(node: Any, segs: list[str], full: str) -> Any:
    for s in segs:
        _, node = _child(node, s, full)
    return node


def _apply_set(raw: dict, override: str) -> None:
    if "=" not in override:
        raise ConfigError(f"override '{override}' must look like section.key=value")
    key, _, val = override.partition("=")
    key = key.strip()
    segs = key.split(".")
    if segs[0] not in CONFIG_FILES:
        raise ConfigError(f"override '{key}': first part must be one of {list(CONFIG_FILES)}")
    parent = _walk(raw, segs[:-1], key)
    k, _ = _child(parent, segs[-1], key)
    try:
        parent[k] = yaml.safe_load(val)
    except yaml.YAMLError as e:
        raise ConfigError(f"override '{override}': cannot parse value: {e}") from e


def _deep_merge_strict(base: Any, upd: Any, src: str, prefix: str) -> None:
    for k, v in upd.items():
        full = f"{prefix}{k}"
        key, cur = _child(base, str(k), f"{full} (in {src})")
        if isinstance(v, dict) and isinstance(cur, dict):
            _deep_merge_strict(cur, v, src, full + ".")
        else:
            base[key] = copy.deepcopy(v)


def _collect_tbd(node: Any, prefix: str, out: list[str]) -> None:
    if isinstance(node, dict):
        for k, v in node.items():
            _collect_tbd(v, f"{prefix}{k}.", out)
    elif isinstance(node, list) and node and all(isinstance(x, dict) for x in node):
        for i, item in enumerate(node):
            seg = item.get("name") or item.get("config_id") or str(i)
            _collect_tbd(item, f"{prefix}{seg}.", out)
    elif node is None or (isinstance(node, list) and any(x is None for x in node)):
        out.append(prefix.rstrip("."))
