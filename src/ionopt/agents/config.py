"""config/agents.yaml: model per role, CLI flags, loop limits (plan_phase2 sections 3, 5.1)."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from ..config import ConfigError, find_config_dir

Role = Literal["planner", "critic", "editor"]


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ClaudeCLI(_M):
    executable: str = "claude"
    restricted: bool = True
    strict_mcp_config: bool = True
    max_retries: int = Field(2, ge=0)


class RoleConfig(_M):
    model: str
    effort: Literal["low", "medium", "high", "xhigh", "max"] | None = None
    tools: list[str] = []
    timeout_s: float = Field(900, gt=0)
    permission_mode: Literal["acceptEdits"] | None = None   # editor: file edits inside its sandbox only


class LoopConfig(_M):
    round_cap: int = Field(8, ge=1)
    solve_budget: int = Field(200, ge=1)
    study_budget_min: int = Field(10, ge=1)
    study_budget_max: int = Field(60, ge=1)
    no_improvement_rounds: int = Field(3, ge=1)
    improvement_tol_deg: float = Field(0.01, ge=0)
    validator_retries: int = Field(2, ge=0)
    editor_failure_cap: int = Field(2, ge=1)
    editor_attempts: int = Field(3, ge=1)          # editor calls per edit (later ones get the failed check)
    editor_build_timeout_s: float = Field(900, gt=0)
    min_bound_fraction: float = Field(0.1, gt=0, le=1)
    warm_start_top_k: int = Field(3, ge=0)
    # base parts every configuration's model must have removed (variants.REMOVABLE_BASE, e.g. screen_mesh):
    # an author rule for one run, e.g. "no screen mesh" for a setup the lab can build without ordering parts
    require_removed: list[str] = []


class AgentsConfig(_M):
    claude: ClaudeCLI = ClaudeCLI()
    roles: dict[Role, RoleConfig]
    loop: LoopConfig = LoopConfig()

    def role(self, name: Role) -> RoleConfig:
        if name not in self.roles:
            raise ConfigError(f"config/agents.yaml has no settings for role '{name}'")
        return self.roles[name]

    def hash(self) -> str:
        return hashlib.sha256(json.dumps(self.model_dump(mode="json"), sort_keys=True).encode()).hexdigest()


def load_agents_config(config_dir: Path | str | None = None, overrides: dict | None = None) -> AgentsConfig:
    """Load config/agents.yaml; `overrides` is a nested dict merged on top (tests, CLI flags)."""
    f = Path(config_dir or find_config_dir()) / "agents.yaml"
    if not f.is_file():
        raise ConfigError(f"missing config file {f}")
    raw = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
    for k, v in (overrides or {}).items():
        if isinstance(v, dict) and isinstance(raw.get(k), dict):
            raw[k] = {**raw[k], **v}
        else:
            raw[k] = v
    try:
        return AgentsConfig.model_validate(raw)
    except ValidationError as e:
        raise ConfigError(f"invalid {f}:\n{e}") from None
