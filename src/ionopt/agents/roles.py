"""Shared plumbing for agent calls: prompt templates, call folders, run-log records."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..backends import SimulationBackend
from ..config import Config
from ..runlog import RunLog
from .config import AgentsConfig, Role
from .llm import CallRecord, LLMClient


@dataclass
class LoopContext:
    """Everything the loop nodes need that is not state (not checkpointed)."""

    cfg: Config
    acfg: AgentsConfig
    llm: LLMClient
    backend: SimulationBackend
    runs_dir: Path                                   # results/runs
    prompts_dir: Path                                # prompts/
    editor: Callable | None = None                   # (EditRequest, LoopState, LoopContext, sandbox) -> EditResult
    log: Callable[[str], None] = field(default=lambda s: None)

    def run_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def db(self) -> RunLog:
        return RunLog(self.cfg.path("db_path"))


def template(ctx: LoopContext, role: Role) -> tuple[str, str]:
    """System prompt of a role and its hash (prompts/<role>.md, versioned in git)."""
    text = (ctx.prompts_dir / f"{role}.md").read_text(encoding="utf-8").strip()
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def call_dir(ctx: LoopContext, run_id: str, round_: int, role: str) -> tuple[str, Path]:
    """New, unique call folder results/runs/<run_id>/calls/r<round>_<role>_<k>."""
    base = ctx.run_dir(run_id) / "calls"
    k = len(list(base.glob(f"r{round_:02d}_{role}_*"))) if base.is_dir() else 0
    name = f"r{round_:02d}_{role}_{k}"
    return f"{run_id}/{name}", base / name


def record_call(ctx: LoopContext, call_id: str, run_id: str, round_: int, role: str, rec: CallRecord | None,
                template_hash: str, error: str | None = None, cdir: Path | None = None,
                model: str | None = None) -> None:
    with ctx.db() as rl:
        rl.record_agent_call(
            call_id, run_id, round_, role, rec.model if rec else (model or ""), str(rec.call_dir if rec else cdir),
            rec.prompt_hash if rec else "", template_hash,
            rec.output.model_dump(mode="json") if rec and rec.output is not None else None,
            rec.raw if rec else None, rec.session_id if rec else None, rec.duration_s if rec else 0.0,
            rec.cost_usd if rec else 0.0, rec.retries if rec else 0, error or (rec.error if rec else None))
