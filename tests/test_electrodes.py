import pytest

from ionopt.electrodes import (JobValidationError, check_structure, expand, expected_potentials, used_lv_channels,
                               validate_job)
from ionopt.jobs import build_job

MM = 1e-3


def einzel_job(cfg, **kw):
    conf = cfg.b0_configs.get("example_einzel")
    channels = {"LV1": 100.0, "LV2": 85.0, "HV1": -5000.0, "HV4": -200.0}
    positions = {"z_mcp": 145 * MM, "mesh_gap": 12.7 * MM, "z_e1": 5 * MM, "z_e2": 20 * MM,
                 "z_e3": 30 * MM, "z_e4": 40 * MM}
    channels.update(kw.pop("channels", {}))
    positions.update(kw.pop("positions", {}))
    for k in kw.pop("drop_positions", []):
        positions.pop(k)
    return build_job(cfg, conf, channels, positions, **kw)


def test_valid_job_no_warnings(cfg):
    assert validate_job(einzel_job(cfg), cfg) == []


def test_structure_rules(cfg):
    ok = {"tip": "LV1", "e1": "GND"}
    assert check_structure(cfg, 1, [1], ok) == []
    assert any("E1" in p for p in check_structure(cfg, 1, [2], {"tip": "LV1", "e2": "GND"}))
    assert any("missing" in p for p in check_structure(cfg, 1, [1, 2], ok))
    assert any("not the tip or a used electrode" in p for p in check_structure(cfg, 1, [1], {**ok, "e5": "GND"}))
    assert any("fixed roles" in p for p in check_structure(cfg, 1, [1], {"tip": "HV1", "e1": "GND"}))
    assert any("must be one of" in p for p in check_structure(cfg, 1, [1], {"tip": "LV7", "e1": "GND"}))
    assert any("1..9" in p for p in check_structure(cfg, 1, [1, 10], {**ok, "e10": "GND"}))
    assert any("chamber setup" in p for p in check_structure(cfg, 7, [1], ok))
    assert any("duplicates" in p for p in check_structure(cfg, 1, [1, 1], ok))


def test_tied_electrodes_share_channel(cfg):
    conf = cfg.b0_configs.get("example_einzel_accel")
    assert used_lv_channels(cfg, conf.wiring) == ["LV1", "LV2", "LV3"]


def test_expand_sets_gnd_and_unused_to_zero(cfg):
    job = einzel_job(cfg)
    p = expand(job, cfg)
    assert p["v_tip"] == 100 and p["v_e3"] == 85 and p["v_e1"] == 0 and p["v_e2"] == 0
    assert p["use_e1"] and p["use_e4"] and not p["use_e5"] and p["v_e5"] == 0
    assert "z_e5" not in p and p["z_e3"] == pytest.approx(0.030)
    assert p["v_mcp_front"] == -5000 and p["v_mesh"] == -200
    assert p["v_mcp_back"] == -4000 and p["v_phosphor"] == -1000        # offsets 1000, 3000
    assert set(p) <= set(cfg.registry())


def test_expand_omits_hv_back_when_offset_tbd(cfg):
    c = cfg.with_overrides(["constraints.supplies.mcp_back_offset_V=null"])
    p = expand(einzel_job(c), c)
    assert "v_mcp_back" not in p and "v_phosphor" not in p


def test_expected_potentials(cfg):
    e = expected_potentials(einzel_job(cfg), cfg)
    assert e == {"sel_tip": 100, "sel_e1": 0, "sel_e2": 0, "sel_e3": 85, "sel_e4": 0,
                 "sel_mesh_plane": -200, "sel_mesh_frame": -200, "sel_mcp_face": -5000}


@pytest.mark.parametrize("kw, msg", [
    (dict(channels={"LV2": 500.0}), "outside constraints.supplies.low_voltage.range_V"),
    (dict(channels={"HV1": -1000.0}), "mcp_front_V"),
    (dict(channels={"HV2": -1.0}), "detector offsets"),
    (dict(channels={"LV9": 1.0}), "unknown channel"),
    (dict(positions={"z_e3": 21 * MM}), "min_gap_mm"),
    (dict(positions={"z_e3": 15 * MM}), "must be larger"),
    (dict(positions={"z_e1": 20 * MM, "z_e2": 25 * MM}), "e1_z_mm"),
    (dict(positions={"z_mcp": 200 * MM}), "z_mcp_mm"),
    (dict(positions={"z_e5": 50 * MM}), "removed electrodes have no position"),
    (dict(drop_positions=["z_e4"]), "positions missing"),
    (dict(positions={"z_e4": 131.5 * MM}), "electrode_z_mm"),
])
def test_violations(cfg, kw, msg):
    with pytest.raises(JobValidationError, match=msg):
        validate_job(einzel_job(cfg, **kw), cfg)


def test_missing_channel_voltage(cfg):
    job = einzel_job(cfg)
    del job.channels["LV2"]
    with pytest.raises(JobValidationError, match="LV2 has no voltage"):
        validate_job(job, cfg)


def test_field_limit(cfg):
    c = cfg.with_overrides(["constraints.electrical.max_field_kV_per_mm=0.01"])
    with pytest.raises(JobValidationError, match="kV/mm"):
        validate_job(einzel_job(c), c)


def test_last_electrode_vs_mesh(cfg):
    c = cfg.with_overrides(["constraints.chamber_setups.1.electrode_z_mm=[3, 140]"])
    with pytest.raises(JobValidationError, match="mesh plane"):
        validate_job(einzel_job(c, positions={"z_e4": 132 * MM}), c)


def test_tbd_limits_give_warnings_not_errors(cfg):
    c = cfg.with_overrides(["constraints.supplies.low_voltage.range_V=[null, null]",
                            "constraints.electrodes.min_gap_mm=null"])
    w = validate_job(einzel_job(c, channels={"LV2": 500.0}), c)
    assert any("low_voltage.range_V is TBD" in x for x in w)
    assert any("spacing not checked" in x for x in w)
