import pytest

from ionopt.backends.mock import MockBackend
from ionopt.checker import check
from ionopt.fidelity import compare_runs, summarize

from helpers import einzel_job


def _pair(cfg):
    b = MockBackend(cfg)
    r2 = b.run(einzel_job(cfg, fidelity="2d"))
    r3 = b.run(einzel_job(cfg, fidelity="3d"))
    for r in (r2, r3):
        check(r.result_dir, cfg)
    return r2.result_dir, r3.result_dir


def test_axisymmetric_mock_2d_equals_3d(cfg_tmp):
    d2, d3 = _pair(cfg_tmp)
    c = compare_runs(d2, d3)
    assert c["fate_agreement"]["weighted"] == pytest.approx(1.0)
    assert c["eta"]["diff"] == pytest.approx(0.0, abs=1e-12)
    assert c["mapping"]["n_theta_both_landed"] > 2
    assert c["mapping"]["dr_max_mm"] == pytest.approx(0.0, abs=1e-9)
    assert c["spot"]["rms_axis_mm"]["diff"] == pytest.approx(0.0, abs=1e-9)
    s = summarize([c, c])
    assert s["n_settings"] == 2 and s["fate_agreement"]["median"] == pytest.approx(1.0)


def test_detects_a_difference(cfg_tmp):
    d2, _ = _pair(cfg_tmp)
    c3 = cfg_tmp.with_overrides(["backend.mock.f0=0.03"])        # different "optics" in the 3D run
    r3 = MockBackend(c3).run(einzel_job(c3, fidelity="3d"))
    check(r3.result_dir, c3)
    c = compare_runs(d2, r3.result_dir)
    assert c["mapping"]["dr_max_mm"] > 0.1


def test_run_fidelity_check_mock(cfg_tmp, tmp_path):
    import json

    from ionopt.fidelity import load_settings, run_fidelity_check
    f = tmp_path / "settings.json"
    f.write_text(json.dumps([{"name": "einzel", "cfg": 1, "wiring": {"tip": "LV1", "e3": "LV2"},
                              "channels": {"LV1": 100.0, "LV2": 85.0, "HV1": -5000.0, "HV4": -200.0},
                              "positions_mm": {"lens_gap": 13.482, "z_mcp": 145, "mesh_gap": 12.7}}]))
    rep = run_fidelity_check(cfg_tmp, load_settings(f), log=lambda *a: None)
    assert not rep["failed"] and len(rep["pairs"]) == 1
    assert rep["summary"]["fate_agreement"]["median"] == pytest.approx(1.0)


def test_resume_from_manifest(cfg_tmp, tmp_path):
    import json

    from ionopt.fidelity import load_settings, run_fidelity_check
    f = tmp_path / "settings.json"
    f.write_text(json.dumps([{"name": "einzel", "cfg": 1, "wiring": {"tip": "LV1", "e3": "LV2"},
                              "channels": {"LV1": 100.0, "LV2": 85.0, "HV1": -5000.0, "HV4": -200.0},
                              "positions_mm": {"lens_gap": 13.482, "z_mcp": 145, "mesh_gap": 12.7}}]))
    first = run_fidelity_check(cfg_tmp, load_settings(f), log=lambda *a: None)
    man = sorted((tmp_path / "results").glob("fidelity_*_jobs.json"))[-1]
    again = run_fidelity_check(cfg_tmp, [], log=lambda *a: None, resume=man)
    assert [p["job_3d"] for p in again["pairs"]] == [p["job_3d"] for p in first["pairs"]]
