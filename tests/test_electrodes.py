import pytest

from ionopt.electrodes import (JobValidationError, check_structure, expand, expected_potentials,
                               geometry_electrodes, stack_layout, used_lv_channels, validate_job)
from helpers import MM, einzel_job


def test_valid_job_no_warnings(cfg):
    assert validate_job(einzel_job(cfg), cfg) == []


def test_structure_rules(cfg):
    assert check_structure(cfg, 1, {"tip": "LV1", "e1": "GND"}) == []
    assert check_structure(cfg, 1, {}) == []                       # everything grounded
    assert any("fixed roles" in p for p in check_structure(cfg, 1, {"tip": "HV1"}))
    assert any("must be one of" in p for p in check_structure(cfg, 1, {"tip": "LV7"}))
    assert any("not connectable" in p for p in check_structure(cfg, 1, {"e10": "LV1"}))
    assert any("not connectable" in p for p in check_structure(cfg, 3, {"d1a": "LV1"}))   # deflectors: GND only
    assert any("chamber setup" in p for p in check_structure(cfg, 7, {}))


def test_tied_electrodes_share_channel(cfg):
    conf = cfg.b0_configs.get("example_einzel_accel")
    assert used_lv_channels(cfg, conf.wiring) == ["LV1", "LV2", "LV3"]


def test_stack_layout_follows_lens_gap(cfg):
    a = stack_layout(cfg, 1, 10 * MM)
    b = stack_layout(cfg, 1, 15 * MM)
    assert [e["name"] for e in a] == [f"e{k}" for k in range(1, 10)]          # no deflectors in cfg 1
    assert a[0]["z_front_m"] == pytest.approx(10 * MM)
    assert a[8]["z_front_m"] == pytest.approx((10 + 93.84) * MM) and a[8]["z_back_m"] == pytest.approx((10 + 108.84) * MM)
    assert all(eb["z_front_m"] - ea["z_front_m"] == pytest.approx(5 * MM) for ea, eb in zip(a, b))
    c3 = stack_layout(cfg, 3, 10 * MM)
    assert [e["name"] for e in c3][-2:] == ["d1", "d2"] and c3[-1]["kind"] == "deflector"


def test_geometry_electrodes_contract(cfg):
    g = geometry_electrodes(einzel_job(cfg), cfg)
    assert len(g) == 9 and g[0]["selection"] == "sel_e1"
    assert g[0]["z_m"] == pytest.approx((13.482 + 7) * MM) and g[0]["thickness_m"] == pytest.approx(14 * MM)
    assert g[0]["r_in_m"] == pytest.approx(5 * MM) and g[0]["r_out_m"] == pytest.approx(32.5 * MM)


def test_expand_sets_gnd_and_unlisted_to_zero(cfg):
    p = expand(einzel_job(cfg), cfg)
    assert p["v_tip"] == 100 and p["v_e3"] == 85
    assert all(p[f"v_e{k}"] == 0 for k in (1, 2, 4, 5, 6, 7, 8, 9))
    assert all(p[f"v_d{i}{h}"] == 0 for i in (1, 2) for h in "ab")              # grounded, even if absent
    assert p["lens_gap"] == pytest.approx(13.482 * MM) and p["z_mcp"] == pytest.approx(0.145)
    assert p["v_mcp_front"] == -5000 and p["v_mesh"] == -200
    assert p["v_mcp_back"] == -4000 and p["v_phosphor"] == -1000        # offsets 1000, 3000
    assert p["ion_charge"] == 1 and p["ion_mass"] == pytest.approx(22.99 * 1.66053906660e-27)
    assert p["t_end"] == pytest.approx(100e-6) and p["dt_out"] == pytest.approx(100e-6 / cfg.backend.worker.output_steps)
    assert set(p) <= set(cfg.registry())


def test_expand_omits_hv_back_when_offset_tbd(cfg):
    c = cfg.with_overrides(["constraints.supplies.mcp_back_offset_V=null"])
    p = expand(einzel_job(c), c)
    assert "v_mcp_back" not in p and "v_phosphor" not in p


def test_expected_potentials(cfg):
    e = expected_potentials(einzel_job(cfg), cfg)
    assert e == {"sel_tip": 100, **{f"sel_e{k}": (85 if k == 3 else 0) for k in range(1, 10)},
                 "sel_mesh_plane": -200, "sel_mesh_frame": -200, "sel_mcp_face": -5000}
    c3 = cfg.with_overrides(["constraints.chamber_setups.3.z_mcp_mm=[145, 145]"])
    e3 = expected_potentials(einzel_job(c3).model_copy(update={"cfg": 3}), c3)
    assert e3["sel_d1"] == 0 and e3["sel_d2"] == 0


@pytest.mark.parametrize("kw, msg", [
    (dict(channels={"LV2": 500.0}), "outside constraints.supplies.low_voltage.range_V"),
    (dict(channels={"HV1": -1000.0}), "mcp_front_V"),
    (dict(channels={"HV2": -1.0}), "detector offsets"),
    (dict(channels={"LV9": 1.0}), "unknown channel"),
    (dict(positions={"z_mcp": 200 * MM}), "z_mcp_mm"),
    (dict(positions={"lens_gap": 20 * MM}), "lens_gap_mm"),
    (dict(positions={"z_e3": 21 * MM}), "unknown positions"),
    (dict(drop_positions=["lens_gap"]), "positions missing"),
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
    # LV2 (85 V) on E3 next to grounded E2/E4 across the 2 mm clearance: 0.0425 kV/mm
    validate_job(einzel_job(cfg), cfg.with_overrides(["constraints.electrical.max_field_kV_per_mm=0.05"]))
    c = cfg.with_overrides(["constraints.electrical.max_field_kV_per_mm=0.04"])
    with pytest.raises(JobValidationError, match="between e2 and e3"):
        validate_job(einzel_job(c), c)


def test_stack_vs_mesh(cfg):
    # stack ends at lens_gap + 108.84 mm; mesh at 145 - 12.7 = 132.3 mm
    c = cfg.with_overrides(["constraints.chamber_setups.1.lens_gap_mm=[5, 30]"])
    validate_job(einzel_job(c, positions={"lens_gap": 23 * MM}), c)
    with pytest.raises(JobValidationError, match="mesh plane"):
        validate_job(einzel_job(c, positions={"lens_gap": 24 * MM}), c)


def test_tbd_limits_give_warnings_not_errors(cfg):
    c = cfg.with_overrides(["constraints.supplies.low_voltage.range_V=[null, null]",
                            "constraints.electrodes.clearance_mm=null"])
    w = validate_job(einzel_job(c, channels={"LV2": 500.0}), c)
    assert any("low_voltage.range_V is TBD" in x for x in w)
    assert any("clearance_mm is TBD" in x for x in w)


def test_launch_preaccel_uses_tip_e1_and_lens_gap(cfg):
    from ionopt.electrodes import launch_preaccel
    from ionopt.launch import preacceleration
    assert launch_preaccel(einzel_job(cfg), cfg) == {"preaccel_eV": 0.0}       # pinned off in tests
    c = cfg.with_overrides(["spec.launch.preaccel=true"])
    job = einzel_job(c, positions={"lens_gap": 10 * MM})
    p = launch_preaccel(job, c)
    ref = preacceleration(job.launch, 100.0, 0.0, 10 * MM)        # tip on LV1 = 100 V, E1 grounded
    assert p == ref and p["preaccel_eV"] > 0
