"""Removed and moved stack parts (constraints.electrodes.removable / movable, author 2026-11-15)."""

import optuna
import pytest

from ionopt import units
from ionopt.backends.mock import MockBackend
from ionopt.config import ConfigError, ConfigurationDef
from ionopt.electrodes import (JobValidationError, expand, expected_potentials, geometry_electrodes,
                               layout_problems, part_gap, stack_layout, validate_job)
from ionopt.jobs import build_job
from ionopt.optimize import SearchSpace, optimize
from ionopt.runlog import RunLog

MM = units.MM
NOFIELD = ["constraints.electrical.max_field_kV_per_mm=null"]


def conf(cfg_id=1, wiring=None, removed=(), moved=(), cid="t"):
    return ConfigurationDef(config_id=cid, cfg=cfg_id, wiring=wiring or {"tip": "LV1", "e1": "LV2", "e3": "LV3"},
                            removed=list(removed), moved=list(moved))


def test_as_built_gaps(cfg):
    parts = stack_layout(cfg, 3, 0.0)
    gaps = {(a["name"], b["name"]): round(part_gap(a, b) / MM, 3) for a, b in zip(parts, parts[1:])}
    assert all(gaps[(f"e{k}", f"e{k + 1}")] == 2.23 for k in range(1, 9))     # packed at min_gap_mm
    assert gaps[("e9", "d1")] == 2.635
    assert [e["name"] for e in stack_layout(cfg, 3, 0.0, removed=["e2", "d2"])] == \
        ["e1", "e3", "e4", "e5", "e6", "e7", "e8", "e9", "d1"]


def test_layout_problems(cfg):
    assert layout_problems(cfg, 3, ["e2", "d1"], {}) == []
    assert "cannot remove ['e1']" in layout_problems(cfg, 3, ["e1"], {})[0]
    assert "not in the stack of cfg 1" in layout_problems(cfg, 1, ["d1"], {})[0]
    assert "cannot move ['e1']" in layout_problems(cfg, 3, [], {"e1": 0.0})[0]
    # e3 moved 1 mm toward e2: gap 1.23 mm < 2.23
    p = layout_problems(cfg, 3, [], {"e3": 21.46 * MM})
    assert len(p) == 1 and "e2-e3 gap 1.230 mm" in p[0]
    # with e2 removed the same position is fine
    assert layout_problems(cfg, 3, ["e2"], {"e3": 21.46 * MM}) == []


@pytest.mark.parametrize("c, bounds", [
    (conf(3, removed=["e2", "d1", "d2"], moved=["e3", "e9"]), {"e3_offset_mm": (15, 30)}),
    (conf(1, moved=["e9"]), {}),
    (conf(3, removed=["e5", "e6"], moved=["e4", "e7"]), {}),
])
def test_search_space_samples_valid_layouts(cfg, c, bounds):
    cfg = cfg.with_overrides(NOFIELD)
    sp = SearchSpace.from_config(cfg, c, bounds)
    rng = sp.variable_ranges()
    assert all(f"{m}_offset_mm" in rng for m in c.moved)
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=1))
    for _ in range(150):
        t = study.ask()
        ch, pos = sp.suggest(t)
        job = build_job(cfg, c, ch, pos)
        validate_job(job, cfg)                          # gaps, mesh fit, removed parts unwired
        assert sp.contains(ch, pos)
        for k, v in sp.to_params(ch, pos).items():      # warm starts reproduce the trial
            assert v == pytest.approx(t.params[k], abs=1e-9)
        study.tell(t, 0.0)


def test_packed_plates_have_no_room(cfg):
    sp = SearchSpace.from_config(cfg, conf(3, moved=["e4", "e5"]))
    assert all(hi - lo < 1e-9 for lo, hi in sp.offsets.values())
    with pytest.raises(ConfigError, match="not movable|cannot move"):
        SearchSpace.raw_ranges(cfg, conf(3, removed=["e4"], moved=["e4"]))


def test_job_parameters_and_selections(cfg):
    cfg = cfg.with_overrides(NOFIELD)
    c = conf(3, removed=["e2", "d1"], moved=["e3"])
    pos = {"lens_gap": 20 * MM, "z_mcp": 410.9 * MM, "mesh_gap": 30 * MM, "e3_offset": 15 * MM}
    job = build_job(cfg, c, {"LV1": 100, "LV2": -50, "LV3": -20, "HV1": -3000, "HV4": -500}, pos)
    validate_job(job, cfg)
    p = expand(job, cfg)
    assert p["on_e2"] == 0 and p["on_d1"] == 0 and p["on_e3"] == 1 and p["on_d2"] == 1
    assert p["dz_e3"] == pytest.approx((15 - 22.46) * MM) and p["dz_e4"] == 0.0
    assert "sel_e2" not in expected_potentials(job, cfg) and "sel_d1" not in expected_potentials(job, cfg)
    el = {e["name"]: e for e in geometry_electrodes(job, cfg)}
    assert "e2" not in el and el["e3"]["z_m"] == pytest.approx((20 + 15 + 7) * MM)
    # as built: every switch at its registry default (models without the switches still run the job)
    asb = expand(build_job(cfg, conf(3), {"LV1": 100, "LV2": -50, "LV3": -20, "HV1": -3000, "HV4": -500},
                           {k: v for k, v in pos.items() if k != "e3_offset"}), cfg)
    reg = cfg.registry()
    assert all(asb[k] == reg[k].default for k in asb if k.startswith(("on_", "dz_")))
    # a removed part cannot be wired; an unknown position key is rejected
    bad = build_job(cfg, conf(3, wiring={"tip": "LV1", "e1": "LV2", "e2": "LV3"}, removed=["e2"]),
                    {"LV1": 100, "LV2": -50, "LV3": -20, "HV1": -3000, "HV4": -500}, pos)
    with pytest.raises(JobValidationError, match="cannot be wired"):
        validate_job(bad, cfg)


def test_optimize_with_removed_and_moved_parts(cfg_tmp):
    cfg = cfg_tmp.with_overrides(NOFIELD)
    c = conf(1, removed=["e2"], moved=["e3"], cid="layout")
    res = optimize(cfg, "ignored", budget=4, backend=MockBackend(cfg), study_id="lay-1", conf=c)
    assert res.n_trials == 4 and "e3_offset" in res.best_positions
    with RunLog(cfg.path("db_path")) as rl:
        jobs = rl._rows("SELECT job_id FROM jobs WHERE study_id='lay-1'")
    import json
    meta = json.loads((cfg.path("results_dir") / jobs[0]["job_id"] / "job.json").read_text())
    assert meta["removed"] == ["e2"] and "e3_offset" in meta["positions"]
