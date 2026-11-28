"""ionopt agent-run / agent-resume / trace with scripted responses on the mock backend."""

import json

from ionopt.cli import main

from test_cli import _args


def _script(d, items):
    d.mkdir()
    for name, data in items:
        (d / f"{name}.json").write_text(json.dumps(data))
    return d


def test_agent_run_pause_resume_trace(tmp_path, capsys):
    plan = {"diagnosis": "none", "diagnosis_evidence": "first round", "action": "optimize",
            "configuration": {"cfg": 1, "wiring": {"tip": "LV1", "e3": "LV2"}}, "solve_budget": 10,
            "claims": [{"id": "c1", "statement": "valid", "evidence_needed": "flags"}], "rationale": "r"}
    script = _script(tmp_path / "script", [
        ("planner_0", {"diagnosis": "none", "diagnosis_evidence": "-", "action": "escalate_spec",
                       "escalation": "Which species first?", "rationale": "r"}),
        ("planner_1", plan),
        ("critic_0", {"verdict": "accept", "reasons": "ok"}),
        ("planner_2", {"diagnosis": "parametric", "diagnosis_evidence": "-", "action": "stop", "rationale": "r"}),
    ])
    common = _args(tmp_path, "--set", "backend.backend=mock", "--set", "optimizer.write_plots=false")
    assert main(["agent-run", *common, "--run-id", "t1", "--budget", "30", "--fake-llm", str(script)]) == 3
    out = capsys.readouterr().out
    assert "PAUSED" in out and "Which species first?" in out and "agent-resume t1 --answer" in out
    # resuming without an answer only repeats the question
    assert main(["agent-resume", "t1", *common, "--fake-llm", str(script)]) == 3
    capsys.readouterr()
    # a new process: the fake LLM restarts its queue, so give it the remaining responses only
    rest = _script(tmp_path / "rest", [("planner_0", plan), ("critic_0", {"verdict": "accept", "reasons": "ok"}),
                                       ("planner_1", {"diagnosis": "parametric", "diagnosis_evidence": "-",
                                                      "action": "stop", "rationale": "r"})])
    assert main(["agent-resume", "t1", *common, "--answer", "Na+", "--fake-llm", str(rest)]) == 0
    out = capsys.readouterr().out
    assert "stop planner_stop" in out and "1 rounds, 10/30 solves" in out
    assert main(["trace", "t1", *common]) == 0
    md = (tmp_path / "results" / "runs" / "t1" / "trace.md").read_text(encoding="utf-8")
    assert "| 1 | optimize | none | ok | t1-r01 | 10 |" in md
    assert main(["agent-run", *common, "--run-id", "t1", "--fake-llm", str(script)]) == 2   # exists


def test_agent_plan_goal_reaches_the_planner_prompt(tmp_path, capsys):
    common = _args(tmp_path, "--set", "backend.backend=mock")
    goal = "Test whether a wider screen mesh (inventory screen_mesh_wide) improves the design."
    assert main(["agent-plan", *common, "--run-id", "g1", "--goal", goal, "--prompt-only"]) == 0
    out = capsys.readouterr().out
    path = out.split("written: ")[1].strip()
    text = open(path, encoding="utf-8").read()
    assert text.startswith("# Author's goal for this run\n" + goal)
    assert main(["agent-plan", *common, "--run-id", "g2", "--prompt-only"]) == 0
    path = capsys.readouterr().out.split("written: ")[1].strip()
    assert "Author's goal" not in open(path, encoding="utf-8").read()


def test_round_max_caps_the_planner_study(tmp_path, capsys):
    common = _args(tmp_path, "--set", "backend.backend=mock")
    assert main(["agent-plan", *common, "--run-id", "m1", "--budget", "60", "--round-max", "30", "--prompt-only"]) == 0
    path = capsys.readouterr().out.split("written: ")[1].strip()
    assert "solve_budget for this round: 10 to 30" in open(path, encoding="utf-8").read()


def test_stop_rule_flags_reach_the_prompt_and_survive_resume(tmp_path, capsys):
    from argparse import Namespace

    from ionopt.agents.cli_agents import _stored_loop_flags

    common = _args(tmp_path, "--set", "backend.backend=mock", "--set", "optimizer.write_plots=false")
    assert main(["agent-plan", *common, "--run-id", "p1", "--no-improvement-rounds", "12",
                 "--improvement-tol", "0.002", "--prompt-only"]) == 0
    path = capsys.readouterr().out.split("written: ")[1].strip()
    assert "stops after 12 rounds without improving the best score by more than 0.002 deg" in \
        open(path, encoding="utf-8").read()
    script = _script(tmp_path / "script", [("planner_0", {"diagnosis": "none", "diagnosis_evidence": "-",
                                                          "action": "escalate_spec", "escalation": "Q?",
                                                          "rationale": "r"})])
    assert main(["agent-run", *common, "--run-id", "p2", "--budget", "30", "--round-max", "20",
                 "--no-improvement-rounds", "12", "--improvement-tol", "0.002", "--fake-llm", str(script)]) == 3
    run_dir = tmp_path / "results" / "runs" / "p2"
    assert json.loads((run_dir / "run_config.json").read_text())["loop"] == {
        "study_budget_max": 20, "no_improvement_rounds": 12, "improvement_tol_deg": 0.002}
    a = Namespace(round_max=None, no_improvement_rounds=5, improvement_tol=None)   # a flag given on resume wins
    _stored_loop_flags(a, run_dir)
    assert (a.round_max, a.no_improvement_rounds, a.improvement_tol) == (20, 5, 0.002)


def test_resume_refuses_other_overrides(tmp_path, capsys):
    script = _script(tmp_path / "script", [("planner_0", {"diagnosis": "none", "diagnosis_evidence": "-",
                                                          "action": "escalate_spec", "escalation": "Q?",
                                                          "rationale": "r"})])
    common = _args(tmp_path, "--set", "backend.backend=mock", "--set", "optimizer.write_plots=false")
    assert main(["agent-run", *common, "--run-id", "o1", "--budget", "30", "--fake-llm", str(script)]) == 3
    stored = json.loads((tmp_path / "results" / "runs" / "o1" / "run_config.json").read_text())["overrides"]
    assert "backend.backend=mock" in stored
    capsys.readouterr()
    assert main(["agent-resume", "o1", *common, "--set", "optimizer.seed=7", "--answer", "x",
                 "--fake-llm", str(script)]) == 2
    assert "started with overrides" in capsys.readouterr().err


def test_resume_extends_rounds_and_solves(tmp_path, capsys):
    plan = {"diagnosis": "none", "diagnosis_evidence": "-", "action": "optimize",
            "configuration": {"cfg": 1, "wiring": {"tip": "LV1", "e3": "LV2"}}, "solve_budget": 10,
            "claims": [{"id": "c1", "statement": "valid", "evidence_needed": "flags"}], "rationale": "r"}
    stop = {"diagnosis": "parametric", "diagnosis_evidence": "-", "action": "stop", "rationale": "r"}
    common = _args(tmp_path, "--set", "backend.backend=mock", "--set", "optimizer.write_plots=false")
    first = _script(tmp_path / "s1", [("planner_0", {"diagnosis": "none", "diagnosis_evidence": "-",
                                                     "action": "escalate_spec", "escalation": "Q?", "rationale": "r"})])
    assert main(["agent-run", *common, "--run-id", "x1", "--budget", "10", "--rounds", "1",
                 "--fake-llm", str(first)]) == 3
    rest = _script(tmp_path / "s2", [("planner_0", plan), ("critic_0", {"verdict": "accept", "reasons": "ok"}),
                                     ("planner_1", stop)])
    assert main(["agent-resume", "x1", *common, "--answer", "go", "--extend-rounds", "1", "--extend-solves", "5",
                 "--fake-llm", str(rest)]) == 0
    summary = json.loads((tmp_path / "results" / "runs" / "x1" / "summary.json").read_text())
    # without the extension the run would stop at round_cap (1 round) / budget (10 solves) before planner_1
    assert summary["stop_reason"] not in ("round_cap", "budget") and summary["rounds"] == 1
    assert any("extended the run by 1 rounds and 5 solves" in x for x in summary["assumptions"])


def test_resume_has_no_unregistered_type_warnings(tmp_path, capsys, caplog):
    """The checkpoint serializer allowlists our state models: no LangGraph 'unregistered type' warning on
    resume, and the state comes back as typed objects (strict LangGraph versions will block the rest)."""
    import logging

    script = _script(tmp_path / "script", [("planner_0", {"diagnosis": "none", "diagnosis_evidence": "-",
                                                          "action": "escalate_spec", "escalation": "Q?",
                                                          "rationale": "r"})])
    common = _args(tmp_path, "--set", "backend.backend=mock", "--set", "optimizer.write_plots=false")
    assert main(["agent-run", *common, "--run-id", "w1", "--budget", "30", "--fake-llm", str(script)]) == 3
    from langgraph.checkpoint.serde import jsonplus
    jsonplus._warned_unregistered_types.clear()      # LangGraph warns once per type per process
    caplog.clear()
    with caplog.at_level(logging.WARNING):
        assert main(["agent-resume", "w1", *common, "--fake-llm", str(script)]) == 3   # repeats the question
    assert not [r for r in caplog.records if "unregistered type" in r.getMessage()]
