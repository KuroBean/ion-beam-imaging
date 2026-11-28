"""Scripted stand-in for ClaudeCLIClient, so the whole loop runs with no LLM (plan_phase2 section 3).

Responses are queued per role. Each entry is
  - a dict (the structured output),
  - a callable (prompt, schema) -> dict, for responses that depend on the prompt,
  - an Exception instance, raised as the call's failure.
A directory of files `<role>_<n>.json` (n = 0, 1, ...) can be loaded with FakeLLM.from_dir.
Prompts are written to the call folder exactly as the real client writes them.
"""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Callable, Sequence

from pydantic import BaseModel, ValidationError

from .llm import CallRecord, LLMError, output_schema, prompt_hash

Response = dict | Callable[[str, type[BaseModel]], dict] | Exception


class FakeLLM:
    def __init__(self, responses: dict[str, Sequence[Response]] | None = None, model: str = "fake"):
        self.queues: dict[str, deque] = defaultdict(deque)
        for role, items in (responses or {}).items():
            self.queues[role].extend(items)
        self.model = model
        self.calls: list[dict[str, Any]] = []

    @classmethod
    def from_dir(cls, d: Path | str) -> "FakeLLM":
        d = Path(d)
        out: dict[str, list] = defaultdict(list)
        for f in sorted(d.glob("*_*.json"), key=lambda p: (p.stem.rsplit("_", 1)[0], int(p.stem.rsplit("_", 1)[1]))):
            out[f.stem.rsplit("_", 1)[0]].append(json.loads(f.read_text(encoding="utf-8")))
        return cls(out)

    def push(self, role: str, *items: Response) -> None:
        self.queues[role].extend(items)

    def call(self, role, system: str, prompt: str, schema: type[BaseModel], call_dir: Path,
             add_dirs: Sequence[Path] = ()) -> CallRecord:
        call_dir = Path(call_dir)
        call_dir.mkdir(parents=True, exist_ok=True)
        (call_dir / "system.md").write_text(system, encoding="utf-8")
        (call_dir / "prompt_0.md").write_text(prompt, encoding="utf-8")
        (call_dir / "schema.json").write_text(json.dumps(output_schema(schema), indent=1), encoding="utf-8")
        self.calls.append({"role": role, "system": system, "prompt": prompt, "call_dir": call_dir,
                           "add_dirs": list(add_dirs)})
        rec = CallRecord(role=role, model=self.model, call_dir=call_dir, prompt_hash=prompt_hash(system, prompt),
                         output=None, raw=None, session_id=f"fake-{len(self.calls)}")
        if not self.queues[role]:
            rec.error = f"FakeLLM: no scripted response left for role '{role}'"
            raise LLMError(rec.error)
        item = self.queues[role].popleft()
        if isinstance(item, Exception):
            raise LLMError(f"{role} call failed (scripted): {item}") from item
        data = item(prompt, schema) if callable(item) else item
        try:
            rec.output = schema.model_validate(data)
        except ValidationError as e:
            raise LLMError(f"{role} scripted response does not validate: {e}") from e
        rec.raw = {"structured_output": data, "fake": True}
        (call_dir / "output.json").write_text(rec.output.model_dump_json(indent=1), encoding="utf-8")
        return rec
