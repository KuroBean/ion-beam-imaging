"""The only place that invokes `claude` (plan_phase2 section 3).

LLM calls go through headless Claude Code (`claude -p`) on the author's seat; there is no API key.
Each call gets its own folder (the working directory of the CLI process) holding the system prompt,
the prompt, every raw response and the validated output, so a call can be inspected and replayed.

`--bare` is not usable: it accepts only an API key. Isolation instead: `--system-prompt`, an
explicit `--tools` list, `--restricted` (no user/project/local settings, file tools confined to the
working directories), `--strict-mcp-config` and `--no-session-persistence`. Checked 2026-11-14
(CLI 2.1.325): a headless call from a clean folder sees no CLAUDE.md, memory or project files.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence, TypeVar

from pydantic import BaseModel, ValidationError

from .config import AgentsConfig, Role

T = TypeVar("T", bound=BaseModel)


class LLMError(RuntimeError):
    """A call failed after all retries (CLI error, timeout, or output that does not validate)."""


@dataclass
class CallRecord:
    role: str
    model: str
    call_dir: Path
    prompt_hash: str
    output: BaseModel | None
    raw: dict | None                 # last CLI JSON result
    session_id: str | None = None
    duration_s: float = 0.0          # wall time, all attempts
    cost_usd: float = 0.0            # CLI estimate (list price), all attempts; usage data on a seat
    retries: int = 0
    error: str | None = None
    attempts: list[dict] = field(default_factory=list)


class LLMClient(Protocol):
    def call(self, role: Role, system: str, prompt: str, schema: type[T], call_dir: Path,
             add_dirs: Sequence[Path] = ()) -> CallRecord: ...


def prompt_hash(system: str, prompt: str) -> str:
    return hashlib.sha256(f"{system}\n\x00\n{prompt}".encode("utf-8")).hexdigest()


def output_schema(schema: type[BaseModel]) -> dict:
    """JSON schema handed to --json-schema (pydantic's, with $defs inlined by the CLI as needed)."""
    return schema.model_json_schema()


def _write(p: Path, text: str) -> None:
    p.write_text(text, encoding="utf-8")


def retry_prompt(prompt: str, error: str) -> str:
    return (f"{prompt}\n\n---\nYour previous answer was rejected by the validator:\n{error}\n"
            f"Answer again, fixing exactly these problems. Keep everything else as it was.")


class ClaudeCLIClient:
    """Calls `claude -p` with a pinned model and per-role tools; validates with pydantic."""

    def __init__(self, acfg: AgentsConfig, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run):
        self.acfg = acfg
        self.runner = runner

    def command(self, role: Role, system: str, schema: type[BaseModel], add_dirs: Sequence[Path] = ()) -> list[str]:
        rc, cli = self.acfg.role(role), self.acfg.claude
        cmd = [cli.executable, "-p", "--output-format", "json",
               "--json-schema", json.dumps(output_schema(schema), separators=(",", ":")),
               "--model", rc.model, "--tools", ",".join(rc.tools),
               "--system-prompt", system, "--no-session-persistence"]
        if rc.effort:
            cmd += ["--effort", rc.effort]
        if rc.permission_mode:
            cmd += ["--permission-mode", rc.permission_mode]
        if cli.restricted:
            cmd.append("--restricted")
        if cli.strict_mcp_config:
            cmd.append("--strict-mcp-config")
        for d in add_dirs:
            cmd += ["--add-dir", str(Path(d).resolve())]
        return cmd

    def call(self, role: Role, system: str, prompt: str, schema: type[T], call_dir: Path,
             add_dirs: Sequence[Path] = ()) -> CallRecord:
        rc = self.acfg.role(role)
        call_dir = Path(call_dir)
        call_dir.mkdir(parents=True, exist_ok=True)
        _write(call_dir / "system.md", system)
        _write(call_dir / "schema.json", json.dumps(output_schema(schema), indent=1))
        rec = CallRecord(role=role, model=rc.model, call_dir=call_dir, prompt_hash=prompt_hash(system, prompt),
                         output=None, raw=None)
        cmd = self.command(role, system, schema, add_dirs)
        p = prompt
        t0 = time.monotonic()
        for attempt in range(self.acfg.claude.max_retries + 1):
            _write(call_dir / f"prompt_{attempt}.md", p)
            rec.retries = attempt
            err, raw = None, None
            try:
                cp = self.runner(cmd, input=p, capture_output=True, text=True, encoding="utf-8",
                                 cwd=str(call_dir), timeout=rc.timeout_s)
                _write(call_dir / f"response_{attempt}.json", cp.stdout or "")
                if cp.stderr:
                    _write(call_dir / f"stderr_{attempt}.txt", cp.stderr)
                raw = json.loads(cp.stdout) if (cp.stdout or "").strip() else None
            except subprocess.TimeoutExpired:
                err = f"timeout after {rc.timeout_s} s"
            except json.JSONDecodeError as e:
                err = f"CLI output is not JSON: {e}"
            if raw is not None:
                rec.raw = raw
                rec.session_id = raw.get("session_id") or rec.session_id
                rec.cost_usd += float(raw.get("total_cost_usd") or 0.0)
                if raw.get("is_error") or raw.get("subtype") != "success":
                    err = f"CLI error ({raw.get('subtype')}): {str(raw.get('result'))[:500]}"
                elif raw.get("structured_output") is None:
                    err = "no structured_output in the CLI result"
            elif err is None:
                err = f"CLI exited with {cp.returncode} and no output: {(cp.stderr or '')[:500]}"
            if err is None:
                try:
                    rec.output = schema.model_validate(raw["structured_output"])
                except ValidationError as e:
                    err = f"schema validation failed:\n{e}"
                    rec.attempts.append({"attempt": attempt, "error": err})
                    p = retry_prompt(prompt, str(e))
                    continue
                rec.attempts.append({"attempt": attempt, "error": None})
                break
            rec.attempts.append({"attempt": attempt, "error": err})
            p = prompt              # CLI-level failure: resend the original prompt
        rec.duration_s = time.monotonic() - t0
        if rec.output is None:
            rec.error = rec.attempts[-1]["error"] if rec.attempts else "no attempt made"
            _write(call_dir / "error.txt", rec.error)
            raise LLMError(f"{role} call failed after {rec.retries + 1} attempt(s): {rec.error}")
        _write(call_dir / "output.json", rec.output.model_dump_json(indent=1))
        return rec


def run_claude(prompt: str, schema: type[T], role: Role, system: str, cwd: Path, acfg: AgentsConfig,
               add_dirs: Sequence[Path] = ()) -> CallRecord:
    """Convenience wrapper (plan_phase2 section 3 signature)."""
    return ClaudeCLIClient(acfg).call(role, system, prompt, schema, cwd, add_dirs)


def summarize_usage(records: Sequence[CallRecord]) -> dict[str, Any]:
    out: dict[str, Any] = {"calls": len(records), "cost_usd": 0.0, "duration_s": 0.0, "retries": 0}
    for r in records:
        out["cost_usd"] += r.cost_usd
        out["duration_s"] += r.duration_s
        out["retries"] += r.retries
    return out
