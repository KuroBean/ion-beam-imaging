import optuna
import pytest

from ionopt.backends.mock import MockBackend
from ionopt.checker import check
from ionopt.config import ConfigError, TBDError
from ionopt.electrodes import validate_job
from ionopt.jobs import build_job
from ionopt.optimize import SearchSpace, optimize
from ionopt.runlog import RunLog

from helpers import einzel_job


@pytest.fixture
def sharp(cfg_tmp):
    """Mock with a sharp optimum: small sigma_MCP, strong chromatic penalty."""
    return cfg_tmp.with_overrides(["spec.detector.sigma_mcp_um=5", "backend.mock.chroma_coeff_m_per_eV=1e-3",
                                   # fixed stack position: no position dimensions
                                   "constraints.chamber_setups.1.lens_gap_mm=[13.482, 13.482]"])


def test_search_space_always_valid(cfg):
    conf = cfg.b0_configs.get("example_einzel_accel")
    c = cfg.with_overrides(["constraints.chamber_setups.1.z_mcp_mm=[135, 145]",
                            "constraints.chamber_setups.1.mesh_gap_mm=[6, 12.7]",
                            "constraints.electrical.max_field_kV_per_mm=null"])
    sp = SearchSpace.from_config(c, conf)
    assert set(sp.channels) == {"LV1", "LV2", "LV3", "HV1", "HV4"}
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=1))
    seen = []
    for _ in range(300):
        ch, pos = sp.suggest(study.ask())
        validate_job(build_job(c, conf, ch, pos), c)          # raises if anything is violated
        seen.append(pos["lens_gap"])
    assert min(seen) < 0.0055 and max(seen) > 0.010           # lens_gap explores its range
    # extremes of the lens_gap fraction are valid too (worst case: mesh closest to the tip)
    for u in (0.0, 1.0):
        ch, pos = sp.suggest(optuna.trial.FixedTrial({"LV1": 0, "LV2": 0, "LV3": 0, "HV1": -5000, "HV4": 0,
                                                      "z_mcp_mm": 135, "mesh_gap_mm": 12.7, "u_lens_gap": u}))
        validate_job(build_job(c, conf, ch, pos), c)


def test_search_space_needs_bounds(cfg):
    conf = cfg.b0_configs.get("example_einzel")
    with pytest.raises(TBDError, match="low_voltage.range_V"):
        SearchSpace.from_config(cfg.with_overrides(["constraints.supplies.low_voltage.range_V=[null, null]"]), conf)


def test_search_space_rejects_impossible_fit(cfg):
    conf = cfg.b0_configs.get("example_einzel_accel")
    c = cfg.with_overrides(["constraints.chamber_setups.1.z_mcp_mm=[110, 145]"])
    with pytest.raises(ConfigError, match="does not fit"):
        SearchSpace.from_config(c, conf)


def test_optimizer_finds_known_optimum(sharp):
    m = sharp.backend.mock
    ref = check(MockBackend(sharp).run(einzel_job(sharp, channels={"LV2": m.lens_opt_V, "HV4": m.mesh_opt_V}))
                .result_dir, sharp)
    assert ref.feasible, ref.flags
    res = optimize(sharp, "example_einzel", budget=80)
    assert res.sampler in ("tpe", "gp")
    assert res.n_trials == 80 and res.best_job_id
    assert res.best_score <= 1.15 * ref.score
    assert abs(res.best_channels["LV2"] - m.lens_opt_V) < 15
    assert abs(res.best_channels["HV4"] - m.mesh_opt_V) < 150
    with RunLog(sharp.path("db_path")) as rl:
        assert len(rl.jobs(res.study_id)) == 80
        assert rl.study(res.study_id)["best_job_id"] == res.best_job_id


def test_failed_runs_are_logged_as_failed_trials(sharp):
    c = sharp.with_overrides(["backend.mock.failure_rate=0.3"])
    res = optimize(c, "example_einzel", budget=20)
    assert res.n_trials == 20 and 0 < res.n_failed < 20
    with RunLog(c.path("db_path")) as rl:
        statuses = [j["status"] for j in rl.jobs(res.study_id)]
    assert statuses.count("failed") == res.n_failed and len(statuses) == 20


def test_study_resumes(sharp):
    r1 = optimize(sharp, "example_einzel", budget=6)
    r2 = optimize(sharp, "example_einzel", budget=10)
    assert r1.study_id == r2.study_id and r2.n_trials == 10
    with RunLog(sharp.path("db_path")) as rl:
        assert len(rl.jobs(r2.study_id)) == 10


def test_infeasible_trials_not_best(sharp):
    c = sharp.with_overrides(["spec.requirements.eta_min=0.99"])     # mock eta = 0.8 * landed <= 0.8
    res = optimize(c, "example_einzel", budget=5)
    assert res.n_feasible == 0 and res.best_job_id is None


def test_optimizer_checks_tbd_before_solving(sharp):
    c = sharp.with_overrides(["spec.detector.sigma_mcp_um=null"])
    with pytest.raises(TBDError, match="sigma_mcp_um"):
        optimize(c, "example_einzel", budget=3)
    assert not c.path("db_path").exists()


@pytest.mark.parametrize("wiring", [{"tip": "LV1", "e1": "LV2", "e3": "LV3"},      # tip and E1 on channels
                                    {"tip": "LV1", "e3": "LV2"},                    # E1 grounded
                                    {"e1": "LV1", "e3": "LV2"}])                    # grounded tip
@pytest.mark.parametrize("charge", [1, -1])
def test_search_space_keeps_extraction_accelerating(cfg, wiring, charge):
    from ionopt.config import ConfigurationDef
    c = cfg.with_overrides(["spec.launch.preaccel=true", f"spec.launch.charge={charge}"])
    conf = ConfigurationDef(config_id="x", description="", cfg=1, wiring=wiring)
    space = SearchSpace.from_config(c, conf)
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=1))
    lo, hi = c.constraints.supplies.low_voltage.range_V
    for _ in range(200):
        ch, _ = space.suggest(study.ask())
        v_tip = ch.get(wiring.get("tip"), 0.0) if "tip" in wiring else 0.0
        v_e1 = ch.get(wiring.get("e1"), 0.0) if "e1" in wiring else 0.0
        assert charge * (v_tip - v_e1) >= c.optimizer.min_extraction_V - 1e-9
        assert all(lo - 1e-9 <= ch[k] <= hi + 1e-9 for k in ch if k.startswith("LV"))
    # without pre-acceleration the ranges are left alone
    assert SearchSpace.from_config(c.with_overrides(["spec.launch.preaccel=false"]), conf).tip_ch is None


def test_search_space_rejects_tip_and_e1_on_one_channel(cfg):
    from ionopt.config import ConfigurationDef
    c = cfg.with_overrides(["spec.launch.preaccel=true"])
    with pytest.raises(ConfigError, match="extraction"):
        SearchSpace.from_config(c, ConfigurationDef(config_id="x", description="", cfg=1, wiring={"tip": "LV1", "e1": "LV1"}))
    with pytest.raises(ConfigError, match="extraction"):
        SearchSpace.from_config(c, ConfigurationDef(config_id="x", description="", cfg=1, wiring={"e3": "LV1"}))


def test_to_params_inverts_suggest(cfg):
    from ionopt.config import ConfigurationDef
    c = cfg.with_overrides(["spec.launch.preaccel=true"])
    space = SearchSpace.from_config(c, ConfigurationDef(config_id="x", description="", cfg=1,
                                                        wiring={"tip": "LV1", "e1": "LV2", "e3": "LV3"}))
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=3))
    for _ in range(20):
        ch, pos = space.suggest(study.ask())
        ch2, pos2 = space.suggest(optuna.trial.FixedTrial(space.to_params(ch, pos)))
        assert ch2 == pytest.approx(ch) and pos2 == pytest.approx(pos)


def test_warm_start_runs_given_settings_first(sharp):
    import json
    ch = {"LV1": 120.0, "LV2": 85.0, "HV1": -5000.0, "HV4": -200.0}
    pos = {"lens_gap": 10e-3, "z_mcp": 145e-3, "mesh_gap": 12.7e-3}
    optimize(sharp, "example_einzel", budget=2, backend=MockBackend(sharp), study_id="warm", initial=[(ch, pos)])
    with RunLog(sharp.path("db_path")) as rl:
        first = min(rl.jobs("warm"), key=lambda j: j["created_at"])
    got = json.loads(first["config_json"])
    assert got["channels"] == pytest.approx(ch)
