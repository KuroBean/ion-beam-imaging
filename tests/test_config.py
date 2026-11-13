import math
import shutil

import pytest
import yaml

from ionopt.cli import main
from ionopt.config import ConfigError, TBDError, load_config, load_snapshot, write_snapshot

from conftest import CONFIG_DIR, DEV_OVERRIDES


def test_repo_config_loads_with_tbds():
    cfg = load_config(CONFIG_DIR)
    tbd = cfg.list_tbd()
    assert "spec.requirements.eta_min" in tbd
    assert "constraints.chamber_setups.1.z_mcp_mm" in tbd
    assert "parameters.parameters.v_phosphor.comsol_name" in tbd   # not modelled
    assert "spec.requirements.impact_threshold_eV_per_charge" in tbd
    assert "spec.launch.mass_Da" not in tbd
    assert not any(k.endswith(".unit") or k.endswith(".allowed") for k in tbd)
    assert "spec.analysis.spline_smoothing" not in tbd
    assert "spec.requirements.impact_threshold_mps" not in tbd
    assert cfg.spec.launch.mass_Da == pytest.approx(22.99)
    assert cfg.spec.detector.mcp_active_diameter_mm == 40


def test_require_names_exact_key():
    cfg = load_config(CONFIG_DIR)
    with pytest.raises(TBDError) as e:
        cfg.require("spec.requirements.eta_min")
    assert str(e.value) == "spec.requirements.eta_min is TBD; set it in config/spec.yaml"
    with pytest.raises(TBDError):
        cfg.require("constraints.chamber_setups.1.z_mcp_mm")   # [null, null]
    assert cfg.require("spec.launch.hwhm_deg") == 20


def test_set_override_parses_and_records():
    cfg = load_config(CONFIG_DIR, overrides=["spec.detector.sigma_mcp_um=80",
                                              "constraints.chamber_setups.2.z_mcp_mm=[100, 200]"])
    assert cfg.spec.detector.sigma_mcp_um == 80
    assert cfg.constraints.chamber_setups[2].z_mcp_mm == [100, 200]
    assert cfg.overrides == ["spec.detector.sigma_mcp_um=80", "constraints.chamber_setups.2.z_mcp_mm=[100, 200]"]
    assert "spec.detector.sigma_mcp_um" not in cfg.list_tbd()


def test_override_unknown_key_rejected():
    with pytest.raises(ConfigError, match="unknown config key"):
        load_config(CONFIG_DIR, overrides=["spec.detector.sigma_mcp=80"])
    with pytest.raises(ConfigError, match="first part"):
        load_config(CONFIG_DIR, overrides=["nope.x=1"])


def test_override_registry_item_by_name():
    cfg = load_config(CONFIG_DIR, overrides=["parameters.parameters.v_tip.comsol_name=V_tip"])
    assert cfg.registry()["v_tip"].comsol_name == "V_tip"


def test_range_min_gt_max_is_error():
    with pytest.raises(ConfigError, match="larger than max"):
        load_config(CONFIG_DIR, overrides=["constraints.supplies.mesh_V=[100, -100]"])


def test_type_and_range_validation():
    with pytest.raises(ConfigError, match="sigma_mcp_um"):
        load_config(CONFIG_DIR, overrides=["spec.detector.sigma_mcp_um=-1"])
    with pytest.raises(ConfigError, match="charge"):
        load_config(CONFIG_DIR, overrides=["spec.launch.charge=0"])
    with pytest.raises(ConfigError, match="theta_max_deg"):
        load_config(CONFIG_DIR, overrides=["spec.launch.theta_max_deg=abc"])


def test_unknown_key_in_file_rejected(tmp_path):
    d = tmp_path / "config"
    shutil.copytree(CONFIG_DIR, d)
    spec = yaml.safe_load((d / "spec.yaml").read_text())
    spec["detector"]["sigma_mcp"] = 5
    (d / "spec.yaml").write_text(yaml.safe_dump(spec))
    with pytest.raises(ConfigError, match="sigma_mcp"):
        load_config(d)


def test_override_file_strict(tmp_path):
    f = tmp_path / "o.yaml"
    f.write_text("spec:\n  detector:\n    sigma_mcpp_um: 3\n")
    with pytest.raises(ConfigError, match="unknown config key"):
        load_config(CONFIG_DIR, override_files=[f])


def test_registry_expansion():
    cfg = load_config(CONFIG_DIR)
    reg = cfg.registry()
    for k in range(1, 10):
        assert f"v_e{k}" in reg and reg[f"v_e{k}"].comsol_name == f"L{k}_v"
    assert "v_e{k}" not in reg and "z_e1" not in reg and "use_e1" not in reg
    assert reg["lens_gap"].comsol_name == "lens_gap" and reg["v_mesh"].comsol_name == "V_screen"


def test_sigma_from_hwhm():
    cfg = load_config(CONFIG_DIR)
    assert math.degrees(cfg.spec.launch.sigma_rad) == pytest.approx(16.99, abs=0.01)


def test_snapshot_roundtrip_and_hash(tmp_path):
    cfg = load_config(CONFIG_DIR, overrides=["spec.detector.sigma_mcp_um=80"], override_files=[DEV_OVERRIDES])
    h = write_snapshot(cfg, tmp_path / "snap.yaml")
    assert h == cfg.config_hash()
    back = load_snapshot(tmp_path / "snap.yaml")
    assert back.config_hash() == h
    assert back.overrides == cfg.overrides
    assert back.spec.detector.sigma_mcp_um == 80


def test_spec_hash_changes_only_with_spec():
    a = load_config(CONFIG_DIR)
    b = a.with_overrides(["constraints.supplies.mesh_V=[-1, 1]"])
    c = a.with_overrides(["spec.tolerances.eval_range_landed_frac=0.95"])
    assert a.spec_hash() == b.spec_hash() != c.spec_hash()
    assert a.config_hash() != b.config_hash()


def test_cli_config_check(capsys):
    assert main(["config-check", "--config-dir", str(CONFIG_DIR)]) == 0
    out = capsys.readouterr().out
    assert "TBD keys" in out and "spec.requirements.eta_min" in out
    assert main(["config-check", "--config-dir", str(CONFIG_DIR), "--set", "spec.bad=1"]) == 2
