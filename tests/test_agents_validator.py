"""agents/schemas.py and agents/validator.py, plus the planner-bounds hooks in optimize.SearchSpace."""

import json

import optuna
import pytest
from pydantic import ValidationError

from conftest import CONFIG_DIR
from ionopt.agents.config import load_agents_config
from ionopt.agents.schemas import Configuration, PlannerProposal
from ionopt.agents.state import Budget, LoopState, RoundRecord, ValidationResult
from ionopt.agents.validator import to_configuration_def, validate
from ionopt.backends.mock import MockBackend
from ionopt.config import ConfigError
from ionopt.optimize import SearchSpace, optimize
from ionopt.runlog import RunLog

EINZEL = {"tip": "LV1", "e3": "LV2"}


@pytest.fixture
def acfg():
    return load_agents_config(CONFIG_DIR)


def state(solves=200, method="agent", history=()):
    return LoopState(run_id="t", method=method, budget=Budget(solves_total=solves, round_cap=8),
                     history=list(history))


def prop(**kw):
    d = {"diagnosis": "none", "diagnosis_evidence": "first round", "action": "optimize",
         "configuration": {"cfg": 1, "wiring": EINZEL}, "solve_budget": 20, "rationale": "r"}
    d.update(kw)
    return PlannerProposal.model_validate(d)


def test_schema_requires_consistent_action():
    with pytest.raises(ValidationError, match="needs a configuration"):
        prop(configuration=None)
    with pytest.raises(ValidationError, match="edit_request"):
        prop(action="edit_then_optimize")
    with pytest.raises(ValidationError, match="escalation"):
        prop(action="escalate_spec", configuration=None, solve_budget=0)
    with pytest.raises(ValidationError, match="lo"):
        prop(bounds={"LV1": {"lo": 5, "hi": 1}})
    prop(action="stop", configuration=None, solve_budget=0)


def test_ok_and_pass_through(cfg, acfg):
    assert validate(prop(), state(), cfg, acfg).status == "ok"
    assert validate(prop(action="stop", configuration=None, solve_budget=0), state(), cfg, acfg).status == "stop"
    esc = prop(action="escalate_spec", configuration=None, solve_budget=0, escalation="eta_min unreachable?")
    assert validate(esc, state(), cfg, acfg).status == "escalate"


@pytest.mark.parametrize("change, match", [
    ({"configuration": {"cfg": 1, "wiring": {"tip": "LV1", "e3": "HV1"}}}, "HV ports"),
    ({"configuration": {"cfg": 7, "wiring": EINZEL}}, "not a chamber setup"),
    ({"configuration": {"cfg": 1, "wiring": EINZEL, "variant_id": "v9"}}, "not an approved variant"),
    ({"configuration": {"cfg": 1, "wiring": EINZEL, "removed": ["e1"]}}, "cannot be removed or moved"),
    ({"configuration": {"cfg": 1, "wiring": EINZEL, "removed": ["d1"]}}, "not in the stack of cfg 1"),
    ({"configuration": {"cfg": 1, "wiring": EINZEL, "removed": ["e4"], "moved": ["e4"]}}, "both removed and moved"),
    ({"configuration": {"cfg": 1, "wiring": EINZEL, "moved": ["e1"]}}, "cannot be removed or moved"),
    ({"configuration": {"cfg": 1, "wiring": EINZEL, "removed": ["e3"]}}, "cannot be wired"),
    ({"bounds": {"LV7": {"lo": 0, "hi": 1}}}, "not a variable"),
    ({"bounds": {"LV2": {"lo": -500, "hi": 0}}}, "outside the allowed range"),
    ({"bounds": {"LV2": {"lo": -10, "hi": -5}}}, "narrower than"),
    ({"solve_budget": 5}, "solve_budget 5"),
    ({"solve_budget": 500}, "solve_budget 500"),
])
def test_invalid(cfg, acfg, change, match):
    v = validate(prop(**change), state(), cfg, acfg)
    assert v.status == "invalid"
    assert any(match in r for r in v.reasons), v.reasons


def test_budget_tail_allows_small_last_study(cfg, acfg):
    assert validate(prop(solve_budget=4), state(solves=4), cfg, acfg).status == "ok"
    assert "no solve budget" in validate(prop(), state(solves=0), cfg, acfg).reasons[0]


def test_bounds_breaking_rules_are_invalid(cfg, acfg):
    c = cfg.with_overrides(["spec.launch.preaccel=true"])
    wiring = {"tip": "LV1", "e1": "LV2"}
    # negative tip: the no-mirror rule keeps the tip above ground
    v = validate(prop(configuration={"cfg": 1, "wiring": wiring}, bounds={"LV1": {"lo": -300, "hi": -200}}),
                 state(), c, acfg)
    assert v.status == "invalid" and "usable range" in v.reasons[0]
    # each bound is fine alone, but the tip is below the whole E1 region: no accelerating extraction field
    v = validate(prop(configuration={"cfg": 1, "wiring": wiring},
                      bounds={"LV1": {"lo": 0, "hi": 100}, "LV2": {"lo": 150, "hi": 300}}), state(), c, acfg)
    assert v.status == "invalid" and "rule" in v.reasons[0], v.reasons


def test_duplicate_needs_reason(cfg, acfg):
    first = prop(bounds={"LV2": {"lo": -300, "hi": 0}})
    hist = [RoundRecord(round=1, proposal=first, validation=ValidationResult(status="ok"))]
    again = prop(bounds={"LV2": {"lo": -290, "hi": 0}})
    v = validate(again, state(history=hist), cfg, acfg)
    assert v.status == "invalid" and "repeats round 1" in v.reasons[0]
    v = validate(again.model_copy(update={"repeat_reason": "new seed"}), state(history=hist), cfg, acfg)
    assert v.status == "ok" and v.warnings
    # a clearly narrower region of the same configuration is not a duplicate
    assert validate(prop(bounds={"LV2": {"lo": -100, "hi": -20}}), state(history=hist), cfg, acfg).status == "ok"
    # grounded entries do not change the configuration identity
    same = prop(configuration={"cfg": 1, "wiring": {**EINZEL, "e5": "GND"}}, bounds={"LV2": {"lo": -290, "hi": 0}})
    assert validate(same, state(history=hist), cfg, acfg).status == "invalid"


def test_edit_paths(cfg, acfg):
    edit = prop(action="edit_then_optimize",
                edit_request={"inventory_items": ["screen_mesh_wide"], "description": "wider mesh", "reason": "x"})
    assert validate(edit, state(), cfg, acfg).status == "needs_edit"
    v = validate(edit, state(method="A2"), cfg, acfg)
    assert v.status == "invalid" and "A2" in v.reasons[0]
    bad = prop(action="edit_then_optimize",
               edit_request={"inventory_items": ["flux_capacitor"], "description": "?", "reason": "x", "supply": "HV1"})
    v = validate(bad, state(), cfg, acfg)
    assert v.status == "invalid" and any("not in the inventory" in r for r in v.reasons)
    assert any("LV channel or GND" in r for r in v.reasons)


def test_search_space_bounds(cfg):
    conf = to_configuration_def(Configuration(cfg=1, wiring=EINZEL), "adhoc")
    full = SearchSpace.from_config(cfg, conf).variable_ranges()
    sp = SearchSpace.from_config(cfg, conf, {"LV2": (-100, -20), "lens_gap_mm": (6, 9)})
    r = sp.variable_ranges()
    assert r["LV2"] == (-100, -20) and r["lens_gap_mm"] == (6, 9) and r["LV1"] == full["LV1"]
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=0))
    for _ in range(50):
        ch, pos = sp.suggest(study.ask())
        assert -100 <= ch["LV2"] <= -20 and 0.006 - 1e-12 <= pos["lens_gap"] <= 0.009 + 1e-12
        assert sp.contains(ch, pos)
    ch["LV2"] = -150
    assert not sp.contains(ch, pos)
    with pytest.raises(ConfigError, match="unknown variable"):
        SearchSpace.from_config(cfg, conf, {"LV9": (0, 1)})
    with pytest.raises(ConfigError, match="does not overlap"):
        SearchSpace.from_config(cfg, conf, {"LV2": (400, 500)})


def test_optimize_adhoc_configuration(cfg_tmp):
    conf = to_configuration_def(Configuration(cfg=1, wiring=EINZEL), "run1-r1")
    res = optimize(cfg_tmp, "ignored", budget=3, backend=MockBackend(cfg_tmp), study_id="run1-r1", conf=conf,
                   bounds={"LV2": (-100, -20)}, tags={"run_id": "run1", "round": "1"})
    assert res.n_trials == 3 and res.n_new == 3 and res.config_id == "run1-r1"
    with RunLog(cfg_tmp.path("db_path")) as rl:
        jobs = rl.jobs("run1-r1")
    assert len(jobs) == 3
    assert all(json.loads(j["config_json"])["tags"]["run_id"] == "run1" for j in jobs)
    again = optimize(cfg_tmp, "ignored", budget=3, backend=MockBackend(cfg_tmp), study_id="run1-r1", conf=conf)
    assert again.n_new == 0                                # resumed study: nothing new to run


def test_removed_and_moved_parts(cfg, acfg):
    c = {"cfg": 1, "wiring": EINZEL, "removed": ["e2", "e4"], "moved": ["e3"]}
    v = validate(prop(configuration=c, bounds={"e3_offset_mm": {"lo": 13, "hi": 30}}), state(), cfg, acfg)
    assert v.status == "ok", v.reasons
    v = validate(prop(configuration=c, bounds={"e5_offset_mm": {"lo": 50, "hi": 60}}), state(), cfg, acfg)
    assert v.status == "invalid" and any("not a variable" in r for r in v.reasons)


def test_require_removed_screen_mesh(cfg_tmp, acfg):
    """loop.require_removed (author rule for one run, e.g. no screen mesh): only variants without the part pass."""
    from ionopt.agents.summaries import required_removals_line
    from ionopt.variants import VariantManifest, save_variant
    save_variant(cfg_tmp, VariantManifest(variant_id="v-no-mesh", inventory_items=["no_screen_mesh"], approved=True,
                                          removed_base=["screen_mesh"], mesh_open_fraction=1.0))
    strict = acfg.model_copy(update={"loop": acfg.loop.model_copy(update={"require_removed": ["screen_mesh"]})})
    v = validate(prop(), state(), cfg_tmp, strict)
    assert v.status == "invalid" and any("still has ['screen_mesh']" in r and "v-no-mesh" in r for r in v.reasons)
    ok = prop(configuration={"cfg": 1, "wiring": EINZEL, "variant_id": "v-no-mesh"})
    assert validate(ok, state(), cfg_tmp, strict).status == "ok"
    assert validate(prop(), state(), cfg_tmp, acfg).status == "ok"          # no rule: base is fine
    assert "WITHOUT the screen mesh" in required_removals_line(strict) and required_removals_line(acfg) == ""
