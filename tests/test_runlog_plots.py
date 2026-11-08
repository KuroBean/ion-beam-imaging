import json

from ionopt.backends.mock import MockBackend
from ionopt.checker import check
from ionopt.plots import make_plots
from ionopt.runlog import RunLog

from helpers import einzel_job

EXPECTED_PLOTS = {"trajectories.png", "field_map.png", "axis_potential.png", "r_theta.png", "dtheta.png",
                  "fates.png", "landing.png"}


def _run(cfg, **kw):
    job = einzel_job(cfg, **kw)
    res = MockBackend(cfg).run(job)
    return job, res, check(res.result_dir, cfg)


def test_record_job_and_metrics(cfg_tmp, tmp_path):
    job, res, m = _run(cfg_tmp, tags={"study_id": "s1"})
    with RunLog(tmp_path / "log.sqlite") as log:
        log.record_job(job, res, cfg_tmp.config_hash())
        log.record_metrics(m)
        row = log.job(job.job_id)
        assert row["status"] == "success" and row["study_id"] == "s1" and row["config_id"] == "example_einzel"
        assert json.loads(row["config_json"])["wiring"]["e3"] == "LV2"
        assert row["config_hash"] == cfg_tmp.config_hash()
        mr = log.metrics(job.job_id)
        assert mr["score"] == m.score and mr["feasible"] == 1
        assert [r["job_id"] for r in log.jobs("s1")] == [job.job_id]


def test_recheck_adds_row_per_spec_hash(cfg_tmp, tmp_path):
    job, res, m = _run(cfg_tmp)
    strict = cfg_tmp.with_overrides(["spec.requirements.eta_min=0.99"])
    m2 = check(res.result_dir, strict)
    with RunLog(tmp_path / "log.sqlite") as log:
        log.record_job(job, res)
        log.record_metrics(m)
        log.record_metrics(m2)
        log.record_metrics(m2)                       # same spec again: replaced, not duplicated
        hist = log.metrics_history(job.job_id)
        assert len(hist) == 2
        assert log.metrics(job.job_id, m.spec_hash)["feasible"] == 1
        assert log.metrics(job.job_id, m2.spec_hash)["feasible"] == 0


def test_studies_and_promotions(cfg_tmp, tmp_path):
    with RunLog(tmp_path / "log.sqlite") as log:
        log.start_study("s1", "example_einzel", "tpe", 0, 20)
        log.finish_study("s1", "abc")
        st = log.study("s1")
        assert st["best_job_id"] == "abc" and st["budget"] == 20 and st["finished_at"]
        log.record_promotion("a2", "a3", 0.4, 0.45, 0.8, 0.79)
        assert log.promotions()[0]["score_3d"] == 0.45


def test_study_results_order(cfg_tmp, tmp_path):
    with RunLog(tmp_path / "log.sqlite") as log:
        for lv2 in (85.0, 40.0, 140.0):
            job, res, m = _run(cfg_tmp, channels={"LV2": lv2}, tags={"study_id": "s"})
            log.record_job(job, res)
            log.record_metrics(m)
        rows = log.study_results("s", cfg_tmp.spec_hash())
        scores = [r["score"] for r in rows]
        assert scores == sorted(scores)
        assert json.loads(rows[0]["config_json"])["channels"]["LV2"] == 85.0   # mock optimum


def test_make_plots_2d_and_3d(cfg_tmp):
    for fid in ("2d", "3d"):
        _, res, _ = _run(cfg_tmp, fidelity=fid)
        made = make_plots(res.result_dir, cfg_tmp)
        assert {p.name for p in made} == EXPECTED_PLOTS
        assert all(p.stat().st_size > 5000 for p in made)


def test_plots_for_failed_run_do_not_crash(cfg_tmp):
    _, res, _ = _run(cfg_tmp, tags={"mock_inject": "fail"})
    assert make_plots(res.result_dir, cfg_tmp) == []
