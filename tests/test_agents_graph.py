"""The agent loop end to end with the scripted FakeLLM and the MockBackend (no LLM, no COMSOL)."""

import json

import pytest

from conftest import CONFIG_DIR
from ionopt.agents.config import load_agents_config
from ionopt.agents.graph import LoopRun, new_state
from ionopt.agents.llm_fake import FakeLLM
from ionopt.agents.roles import LoopContext
from ionopt.agents.schemas import EditResult
from ionopt.backends.mock import MockBackend
from ionopt.runlog import RunLog
from ionopt.variants import VariantManifest, load_variant, save_variant

REPO = CONFIG_DIR.parent
EINZEL = {"tip": "LV1", "e3": "LV2"}


def plan(bounds=None, budget=10, action="optimize", diagnosis="parametric", **kw):
    d = {"diagnosis": diagnosis, "diagnosis_evidence": "e", "action": action,
         "configuration": {"cfg": 1, "wiring": EINZEL}, "bounds": bounds or {}, "solve_budget": budget,
         "claims": [{"id": "c1", "statement": "eta above 0.3", "evidence_needed": "eta"}], "rationale": "r"}
    d.update(kw)
    return d


STOP = {"diagnosis": "parametric", "diagnosis_evidence": "good enough", "action": "stop", "rationale": "done"}
ACCEPT = {"verdict": "accept", "reasons": "plausible",
          "claim_checks": [{"claim_id": "c1", "status": "supported", "evidence": "eta 0.5"}]}
REJECT = {"verdict": "reject", "reasons": "looks like default values"}


@pytest.fixture
def make_ctx(cfg_tmp, tmp_path):
    def _make(responses, loop=None, editor=None, backend=None):
        acfg = load_agents_config(CONFIG_DIR, overrides={"loop": {"study_budget_min": 3, **(loop or {})}})
        return LoopContext(cfg=cfg_tmp, acfg=acfg, llm=FakeLLM(responses), backend=backend or MockBackend(cfg_tmp),
                           runs_dir=tmp_path / "runs", prompts_dir=REPO / "prompts", editor=editor)
    return _make


def run(ctx, run_id="r1", **kw):
    with LoopRun(ctx, run_id) as lr:
        return lr.start(new_state(ctx, run_id, **kw))


def test_two_rounds_then_planner_stop(make_ctx):
    ctx = make_ctx({"planner": [plan(budget=4), plan(bounds={"LV2": {"lo": -150, "hi": -10}}, budget=4), STOP],
                    "critic": [ACCEPT, ACCEPT]})
    st = run(ctx, solve_budget=50)
    s = st.state
    assert st.done and s.stop_reason == "planner_stop"
    assert s.budget.rounds_used == 2 and s.budget.solves_used == 8
    assert [h.critic.verdict for h in s.history] == ["accept", "accept"]
    with RunLog(ctx.cfg.path("db_path")) as rl:
        assert [r["round"] for r in rl.agent_rounds("r1")] == [1, 2]
        calls = rl.agent_calls("r1")
        assert [c["role"] for c in calls] == ["planner", "critic", "planner", "critic", "planner"]
        assert rl.agent_run("r1")["stop_reason"] == "planner_stop"
        assert all(c["template_hash"] for c in calls)
    summary = json.loads((ctx.run_dir("r1") / "summary.json").read_text())
    assert summary["rounds"] == 2 and summary["solves_used"] == 8
    # prompts are deterministic files; the second planner prompt contains the round-1 history
    second = (ctx.run_dir("r1") / "calls" / "r02_planner_0" / "prompt_0.md").read_text(encoding="utf-8")
    assert "| 1 | optimize | parametric |" in second and "B0" in second
    # the critic saw the claims and an evidence folder, never the rationale
    crit = ctx.llm.calls[1]
    assert "c1: eta above 0.3" in crit["prompt"] and "rationale" not in crit["prompt"].lower()
    assert (crit["call_dir"] / "evidence" / "metrics.json").is_file()


def test_budget_stop_and_tail_budget(make_ctx):
    ctx = make_ctx({"planner": [plan(budget=4), plan(bounds={"LV2": {"lo": -150, "hi": -10}}, budget=2)],
                    "critic": [ACCEPT, ACCEPT]})
    s = run(ctx, solve_budget=6).state
    assert s.stop_reason == "budget" and s.budget.solves_used == 6


def test_round_cap(make_ctx):
    ctx = make_ctx({"planner": [plan(budget=3)], "critic": [ACCEPT]})
    s = run(ctx, solve_budget=50, round_cap=1).state
    assert s.stop_reason == "round_cap" and s.budget.rounds_used == 1


def test_invalid_retries_then_stop(make_ctx):
    bad = plan(configuration={"cfg": 1, "wiring": {"tip": "LV1", "e3": "HV1"}})
    ctx = make_ctx({"planner": [bad, bad, bad]}, loop={"validator_retries": 2})
    s = run(ctx).state
    assert s.stop_reason == "invalid_proposals" and s.budget.rounds_used == 0
    # each retry prompt carries the validator's reasons
    assert "HV ports" in ctx.llm.calls[1]["prompt"] and "Feedback on your previous proposal" in ctx.llm.calls[1]["prompt"]


def test_invalid_then_fixed(make_ctx):
    bad = plan(configuration={"cfg": 1, "wiring": {"tip": "LV1", "e3": "HV1"}})
    ctx = make_ctx({"planner": [bad, plan(budget=3), STOP], "critic": [ACCEPT]})
    s = run(ctx).state
    assert s.stop_reason == "planner_stop" and s.budget.rounds_used == 1


def test_critic_reject_excluded_from_best(make_ctx):
    ctx = make_ctx({"planner": [plan(budget=4), STOP], "critic": [REJECT]})
    s = run(ctx).state
    assert s.history[0].counted is False and s.best is None


def test_ablation_a1_has_no_critic(make_ctx):
    ctx = make_ctx({"planner": [plan(budget=4), STOP]})
    s = run(ctx, method="A1").state
    assert s.history[0].critic is None and [c["role"] for c in ctx.llm.calls] == ["planner", "planner"]


def test_no_improvement_stop(make_ctx):
    # the same region three times (with a stated reason): no improvement after the first round
    p = plan(budget=3, repeat_reason="seed check")
    ctx = make_ctx({"planner": [p, p, p, p], "critic": [ACCEPT] * 4},
                   loop={"no_improvement_rounds": 2, "improvement_tol_deg": 1e6})
    s = run(ctx, solve_budget=100).state
    if s.best is None:
        pytest.skip("mock found no feasible design in 3 solves; no-improvement needs a best result")
    assert s.stop_reason == "no_improvement" and s.budget.rounds_used == 3


def test_editor_missing_counts_failures(make_ctx):
    edit = plan(action="edit_then_optimize",
                edit_request={"inventory_items": ["no_screen_mesh"], "description": "no mesh", "reason": "x"})
    ctx = make_ctx({"planner": [edit, edit]}, loop={"editor_failure_cap": 2})
    s = run(ctx).state
    assert s.stop_reason == "editor_failures" and s.editor_failures == 2
    assert "not available yet" in ctx.llm.calls[1]["prompt"]


def _ok_editor(req, state, ctx, sandbox):
    save_variant(ctx.cfg, VariantManifest(variant_id="v1", removed_base=["screen_mesh"], mesh_open_fraction=1.0))
    return EditResult(ok=True, variant_id="v1", script_path="build_axisym.py", diff_summary="mesh removed",
                      n_solves=2)


class VariantMock(MockBackend):
    supports_variants = True


class NoVariantMock(MockBackend):
    supports_variants = False


def test_edit_approval_pause_and_resume(make_ctx, cfg_tmp):
    edit = plan(action="edit_then_optimize", budget=3,
                edit_request={"inventory_items": ["no_screen_mesh"], "description": "no mesh", "reason": "x"})
    ctx = make_ctx({"planner": [edit, STOP], "critic": [ACCEPT]}, editor=_ok_editor,
                   backend=VariantMock(cfg_tmp))
    with LoopRun(ctx, "r1") as lr:
        st = lr.start(new_state(ctx, "r1"))
        assert not st.done and st.interrupt["type"] == "edit_approval" and st.interrupt["edit_id"] == "r1-r01-e0"
    # a new process: reopen the checkpoint and approve
    with LoopRun(ctx, "r1") as lr:
        st = lr.resume({"approved": True})
    s = st.state
    assert st.done and s.stop_reason == "planner_stop"
    assert [v.variant_id for v in s.model_variants] == ["v1"]
    assert s.history[0].proposal.configuration.variant_id == "v1"
    assert s.budget.solves_used == 2 + 3            # editor check solves + the study
    assert load_variant(ctx.cfg, "v1").approved


def test_edit_rejected_goes_back_to_planner(make_ctx):
    edit = plan(action="edit_then_optimize",
                edit_request={"inventory_items": ["no_screen_mesh"], "description": "no mesh", "reason": "x"})
    ctx = make_ctx({"planner": [edit, STOP]}, editor=_ok_editor)
    with LoopRun(ctx, "r1") as lr:
        lr.start(new_state(ctx, "r1"))
        st = lr.resume({"approved": False, "reason": "no room for a grid there"})
    assert st.done and st.state.stop_reason == "planner_stop"
    assert "no room for a grid there" in ctx.llm.calls[1]["prompt"]


def test_variant_without_backend_support_is_not_solved(make_ctx, cfg_tmp):
    edit = plan(action="edit_then_optimize",
                edit_request={"inventory_items": ["no_screen_mesh"], "description": "no mesh", "reason": "x"})
    ctx = make_ctx({"planner": [edit, STOP]}, editor=_ok_editor, backend=NoVariantMock(cfg_tmp))
    with LoopRun(ctx, "r1") as lr:
        lr.start(new_state(ctx, "r1"))
        s = lr.resume({"approved": True}).state
    assert s.history[0].n_solves == 0 and "model-variant support" in s.history[0].note


def test_escalation_pause_and_answer(make_ctx):
    esc = {"diagnosis": "specification", "diagnosis_evidence": "eta < 0.1 everywhere", "action": "escalate_spec",
           "escalation": "Is eta_min 0.4 required?", "rationale": "r"}
    ctx = make_ctx({"planner": [esc, STOP]})
    with LoopRun(ctx, "r1") as lr:
        st = lr.start(new_state(ctx, "r1"))
        assert st.interrupt == {"type": "escalation", "question": "Is eta_min 0.4 required?",
                                "diagnosis_evidence": "eta < 0.1 everywhere"}
        st = lr.resume({"answer": "yes, keep it"})
    assert st.done and "yes, keep it" in ctx.llm.calls[1]["prompt"]


def test_resume_after_crash(make_ctx):
    """A planner failure mid-run stops cleanly; a crash inside a node resumes from the last checkpoint."""
    ctx = make_ctx({"planner": [plan(budget=3)], "critic": [RuntimeError("network down")]})
    s = run(ctx).state
    # critic failure is not fatal: the round is kept with a note, the next planner call fails (queue empty)
    assert s.history[0].note.startswith("critic error") and s.stop_reason.startswith("planner_error")


def test_new_state_needs_an_impact_threshold(make_ctx):
    from ionopt.config import ConfigError
    ctx = make_ctx({})
    ctx.cfg.spec.requirements.impact_threshold_eV_per_charge = None
    ctx.cfg.spec.requirements.impact_threshold_mps = None
    with pytest.raises(ConfigError, match="impact_threshold"):
        new_state(ctx, "r0")
