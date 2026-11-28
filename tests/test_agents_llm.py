"""agents/llm.py and llm_fake.py: no real `claude` process is started."""

import json
import subprocess

import pytest
from pydantic import BaseModel, Field

from conftest import CONFIG_DIR
from ionopt.agents.config import load_agents_config
from ionopt.agents.llm import ClaudeCLIClient, LLMError
from ionopt.agents.llm_fake import FakeLLM


class Answer(BaseModel):
    answer: int = Field(ge=0)
    note: str = ""


@pytest.fixture
def acfg():
    return load_agents_config(CONFIG_DIR)


def _cli_result(structured, subtype="success", is_error=False, cost=0.01):
    return json.dumps({"type": "result", "subtype": subtype, "is_error": is_error, "session_id": "s1",
                       "total_cost_usd": cost, "result": "x", "structured_output": structured})


class Runner:
    """Records commands; returns queued stdout strings (or raises queued exceptions)."""

    def __init__(self, outs):
        self.outs, self.calls = list(outs), []

    def __call__(self, cmd, **kw):
        self.calls.append((cmd, kw))
        o = self.outs.pop(0)
        if isinstance(o, Exception):
            raise o
        return subprocess.CompletedProcess(cmd, 0, stdout=o, stderr="")


def test_agents_config_loads(acfg):
    assert acfg.role("planner").tools == []
    assert acfg.role("critic").tools == ["Read"]
    assert acfg.loop.study_budget_min <= acfg.loop.study_budget_max
    assert len(acfg.hash()) == 64


def test_command_flags(acfg, tmp_path):
    cmd = ClaudeCLIClient(acfg).command("critic", "SYS", Answer, add_dirs=[tmp_path])
    assert cmd[:2] == ["claude", "-p"]
    for flag in ("--json-schema", "--model", "--tools", "--system-prompt", "--no-session-persistence",
                 "--restricted", "--strict-mcp-config", "--add-dir"):
        assert flag in cmd
    assert cmd[cmd.index("--model") + 1] == "claude-opus-5-5"
    assert cmd[cmd.index("--tools") + 1] == "Read"
    assert json.loads(cmd[cmd.index("--json-schema") + 1])["properties"]["answer"]["type"] == "integer"
    planner = ClaudeCLIClient(acfg).command("planner", "SYS", Answer)
    assert planner[planner.index("--tools") + 1] == ""        # no tools at all


def test_call_success_writes_files(acfg, tmp_path):
    r = Runner([_cli_result({"answer": 5})])
    rec = ClaudeCLIClient(acfg, runner=r).call("planner", "SYS", "what is 2+3", Answer, tmp_path / "c1")
    assert rec.output.answer == 5 and rec.retries == 0 and rec.session_id == "s1"
    assert rec.cost_usd == pytest.approx(0.01)
    assert r.calls[0][1]["input"] == "what is 2+3"            # prompt goes through stdin
    assert r.calls[0][1]["cwd"] == str(tmp_path / "c1")
    for f in ("system.md", "prompt_0.md", "response_0.json", "output.json", "schema.json"):
        assert (tmp_path / "c1" / f).is_file()


def test_validation_retry_appends_error(acfg, tmp_path):
    r = Runner([_cli_result({"answer": -1}), _cli_result({"answer": 4})])
    rec = ClaudeCLIClient(acfg, runner=r).call("planner", "SYS", "P", Answer, tmp_path / "c")
    assert rec.output.answer == 4 and rec.retries == 1
    assert "rejected by the validator" in r.calls[1][1]["input"]
    assert rec.cost_usd == pytest.approx(0.02)


def test_cli_error_and_timeout_then_raise(acfg, tmp_path):
    r = Runner([_cli_result(None, subtype="error_max_turns", is_error=True),
                subprocess.TimeoutExpired("claude", 1), "not json"])
    with pytest.raises(LLMError, match="not JSON"):
        ClaudeCLIClient(acfg, runner=r).call("planner", "SYS", "P", Answer, tmp_path / "c")
    assert len(r.calls) == acfg.claude.max_retries + 1
    assert (tmp_path / "c" / "error.txt").is_file()


def test_fake_llm_queue_and_callable(tmp_path):
    fake = FakeLLM({"planner": [{"answer": 1}, lambda prompt, schema: {"answer": len(prompt)}]})
    assert fake.call("planner", "S", "P", Answer, tmp_path / "a").output.answer == 1
    assert fake.call("planner", "S", "abcd", Answer, tmp_path / "b").output.answer == 4
    with pytest.raises(LLMError, match="no scripted response"):
        fake.call("planner", "S", "P", Answer, tmp_path / "c")
    fake.push("critic", {"answer": -3})
    with pytest.raises(LLMError, match="does not validate"):
        fake.call("critic", "S", "P", Answer, tmp_path / "d")


def test_fake_llm_from_dir(tmp_path):
    for i, v in enumerate([3, 7]):
        (tmp_path / f"planner_{i}.json").write_text(json.dumps({"answer": v}))
    fake = FakeLLM.from_dir(tmp_path)
    assert [fake.call("planner", "", "", Answer, tmp_path / f"c{i}").output.answer for i in range(2)] == [3, 7]
