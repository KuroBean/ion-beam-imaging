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
        ch, pos = sp.suggest(optuna.trial.FixedTrial({"LV1": 0, "u_LV2": 0.5, "u_LV3": 0.5, "HV1": -5000, "u_HV4": 1.0,
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
    # the mock's score ignores the tip, so the no-mirror coupling of LV2 to the tip only slows it down
    res = optimize(sharp.with_overrides(["optimizer.no_mirror=false"]), "example_einzel", budget=80)
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


@pytest.mark.parametrize("wiring", [{"tip": "LV1", "e1": "LV2", "e3": "LV3"},      # tip and E1 on channels
                                    {"tip": "LV1", "e3": "LV2"},                    # E1 grounded: tip constant
                                    {"e1": "LV1", "e3": "LV2"}])                    # grounded tip: E1 constant
@pytest.mark.parametrize("charge", [1, -1])
def test_fixed_extraction_voltage(cfg, wiring, charge):
    from ionopt.config import ConfigurationDef
    dv = 120.0
    c = cfg.with_overrides(["spec.launch.preaccel=true", f"spec.launch.charge={charge}",
                            f"optimizer.fixed_extraction_V={dv}"])
    conf = ConfigurationDef(config_id="x", description="", cfg=1, wiring=wiring)
    space = SearchSpace.from_config(c, conf)
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=2))
    lo, hi = c.constraints.supplies.low_voltage.range_V
    tips = []
    for _ in range(100):
        t = study.ask()
        ch, pos = space.suggest(t)
        assert not any(k == f"u_{wiring.get('e1')}" for k in t.params)   # E1 is never sampled
        v_tip = ch[wiring["tip"]] if "tip" in wiring else 0.0
        v_e1 = ch[wiring["e1"]] if "e1" in wiring else 0.0
        assert charge * (v_tip - v_e1) == pytest.approx(dv)
        assert all(lo - 1e-9 <= ch[k] <= hi + 1e-9 for k in ch if k.startswith("LV"))
        assert space.contains(ch, pos)
        tips.append(v_tip)
    if "tip" in wiring and "e1" in wiring:
        assert max(tips) - min(tips) > 50                 # the tip still varies; E1 rides along
    with pytest.raises(ConfigError, match="min_extraction_V"):
        SearchSpace.from_config(c.with_overrides(["optimizer.min_extraction_V=200"]), conf)


@pytest.mark.parametrize("wiring", [{"tip": "LV1", "e1": "LV2", "e3": "LV3"},      # tip and E1 on channels
                                    {"tip": "LV1", "e3": "LV2"},                    # E1 grounded
                                    {"e1": "LV1", "e3": "LV2"}])                    # grounded tip
@pytest.mark.parametrize("charge", [1, -1])
def test_extraction_voltage_window(cfg, wiring, charge):
    from ionopt.config import ConfigurationDef
    c = cfg.with_overrides(["spec.launch.preaccel=true", f"spec.launch.charge={charge}",
                            "optimizer.min_extraction_V=120", "optimizer.max_extraction_V=300"])
    conf = ConfigurationDef(config_id="x", description="", cfg=1, wiring=wiring)
    space = SearchSpace.from_config(c, conf)
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=4))
    lo, hi = c.constraints.supplies.low_voltage.range_V
    dvs = []
    for _ in range(200):
        ch, pos = space.suggest(study.ask())
        v_tip = ch[wiring["tip"]] if "tip" in wiring else 0.0
        v_e1 = ch[wiring["e1"]] if "e1" in wiring else 0.0
        dv = charge * (v_tip - v_e1)
        assert 120 - 1e-9 <= dv <= 300 + 1e-9
        assert all(lo - 1e-9 <= ch[k] <= hi + 1e-9 for k in ch if k.startswith("LV"))
        assert space.contains(ch, pos)
        dvs.append(dv)
    assert max(dvs) - min(dvs) > 100                      # the window is explored, not pinned
    with pytest.raises(ConfigError, match="max_extraction_V"):
        SearchSpace.from_config(c.with_overrides(["optimizer.max_extraction_V=50"]), conf)


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


@pytest.mark.parametrize("wiring", [{"tip": "LV1", "e1": "LV2", "e3": "LV3", "e5": "LV4"},
                                    {"e1": "LV1", "e3": "LV2"}])                   # grounded tip
@pytest.mark.parametrize("charge", [1, -1])
@pytest.mark.parametrize("preaccel", [True, False])
def test_search_space_has_no_ion_mirrors(cfg, wiring, charge, preaccel):
    from ionopt.config import ConfigurationDef
    c = cfg.with_overrides([f"spec.launch.preaccel={str(preaccel).lower()}", f"spec.launch.charge={charge}",
                            "spec.launch.E0_eV=2", "spec.launch.dE_eV=0"])
    space = SearchSpace.from_config(c, ConfigurationDef(config_id="x", description="", cfg=1, wiring=wiring))
    s = c.constraints.supplies
    mesh, mcp = s.hv_port("mesh"), s.hv_port("mcp_front")
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=2))
    for _ in range(200):
        ch, pos = space.suggest(study.ask())
        v_tip = ch[wiring["tip"]] if "tip" in wiring else 0.0
        others = [ch[v] for k, v in wiring.items() if k not in ("tip", "e1")] + [ch[mesh]]
        assert all(charge * (v - v_tip) <= 1e-9 for v in others) and charge * v_tip >= -1e-9
        assert all(space.channels[k][0] - 1e-9 <= ch[k] <= space.channels[k][1] + 1e-9 for k in ch)
        ch2, _ = space.suggest(optuna.trial.FixedTrial(space.to_params(ch, pos)))
        assert ch2 == pytest.approx(ch)
    assert mcp not in space.capped
    assert not SearchSpace.from_config(c.with_overrides(["optimizer.no_mirror=false"]),
                                       ConfigurationDef(config_id="x", description="", cfg=1, wiring=wiring)).capped


def test_mirror_warning_for_hand_made_settings(sharp, caplog):
    import logging
    from ionopt.electrodes import mirror_warnings
    assert not mirror_warnings(einzel_job(sharp), sharp)                       # tip +100, E3 +85, mesh -200
    with caplog.at_level(logging.WARNING, logger="ionopt.jobs"):
        job = einzel_job(sharp, channels={"LV2": 150.0, "HV4": 120.0})
    w = mirror_warnings(job, sharp)
    assert len(w) == 1 and "e3 +150 V" in w[0] and "mesh +120 V" in w[0] and "above the tip (+100 V)" in w[0]
    assert "above the tip" in caplog.text
    # a tip below ground puts the grounded plates and deflectors above it
    assert "e1 +0 V" in mirror_warnings(einzel_job(sharp, channels={"LV1": -20.0, "LV2": -50.0}), sharp)[0]
