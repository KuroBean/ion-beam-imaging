"""Headless Claude Code checks for plan_phase2 section 3 (run on the WorkSpace, under the seat).

Checks, through the same client the loop uses (agents/llm.py):
  1. `claude -p` works from Python and returns structured output;
  2. a pydantic schema with nested models ($defs/$ref), enums and Literals is accepted and validated;
  3. the headless session sees no CLAUDE.md, memory or project files (the model lists its context);
  4. the critic role can Read a file in an --add-dir folder and nothing outside it;
and prints the per-call cost estimate and duration.

    .venv/Scripts/python scripts/check_headless.py [--model claude-sonnet-5-5] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ionopt.agents.config import load_agents_config  # noqa: E402
from ionopt.agents.llm import ClaudeCLIClient, summarize_usage  # noqa: E402


class Item(BaseModel):
    name: str
    kind: Literal["claude_md", "memory", "project_file", "tool", "system_prompt", "user_info", "other"]


class ContextReport(BaseModel):
    items: list[Item] = Field(description="every piece of context besides the user message")
    saw_claude_md: bool
    saw_memory: bool
    answer: int


class ReadReport(BaseModel):
    secret_inside: str = Field(description="content of inside.txt, or '' if it could not be read")
    secret_outside: str = Field(description="content of outside.txt, or '' if it could not be read")
    notes: str = ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", help="override the model for this check (default: config/agents.yaml)")
    ap.add_argument("--out", type=Path, help="folder for the call records (default: a temp folder)")
    a = ap.parse_args()
    over = {}
    if a.model:
        acfg0 = load_agents_config(ROOT / "config")
        over = {"roles": {r: {**c.model_dump(), "model": a.model} for r, c in acfg0.roles.items()}}
    acfg = load_agents_config(ROOT / "config", overrides=over)
    client = ClaudeCLIClient(acfg)
    out = a.out or Path(tempfile.mkdtemp(prefix="ionopt_headless_"))
    recs, ok = [], True

    print(f"call records in {out}")
    r1 = client.call("planner", "You are a test assistant. Answer only through the required JSON.",
                     "List every piece of context you were given besides this message (CLAUDE.md content, "
                     "memory files, project files, tools, system prompt parts, user info). Then: what is 2+3?",
                     ContextReport, out / "context")
    recs.append(r1)
    o = r1.output
    print(f"[1-3] structured output OK (nested schema). answer={o.answer} claude_md={o.saw_claude_md} "
          f"memory={o.saw_memory}")
    for it in o.items:
        print(f"      - {it.kind}: {it.name}")
    if o.answer != 5 or o.saw_claude_md or o.saw_memory:
        ok = False
        print("      FAIL: wrong answer or project context leaked")

    ev, other = out / "evidence", out / "elsewhere"
    ev.mkdir(parents=True, exist_ok=True)
    other.mkdir(parents=True, exist_ok=True)
    (ev / "inside.txt").write_text("alpha-417", encoding="utf-8")
    (other / "outside.txt").write_text("omega-923", encoding="utf-8")
    r2 = client.call("critic", "You are a test assistant. Use the Read tool, then answer through the JSON.",
                     f"Read {ev / 'inside.txt'} and {other / 'outside.txt'} and report their contents.",
                     ReadReport, out / "read_call", add_dirs=[ev])
    recs.append(r2)
    o2 = r2.output
    inside_ok, outside_blocked = o2.secret_inside.strip() == "alpha-417", "omega-923" not in o2.secret_outside
    print(f"[4] Read inside add-dir: {'OK' if inside_ok else 'FAIL'}; "
          f"outside blocked: {'OK' if outside_blocked else 'FAIL (critic could read outside its folder)'}")
    ok &= inside_ok and outside_blocked

    u = summarize_usage(recs)
    print(f"usage: {u['calls']} calls, {u['duration_s']:.1f} s, ~${u['cost_usd']:.4f} (CLI estimate), "
          f"retries {u['retries']}")
    (out / "check_headless.json").write_text(json.dumps({"ok": ok, "usage": u}, indent=1), encoding="utf-8")
    print("ALL OK" if ok else "SOME CHECKS FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
