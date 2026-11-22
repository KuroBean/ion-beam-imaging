"""Model variants (ionopt.variants): manifests, jobs, optimizer variables, mock runs (no COMSOL)."""

import json

import pytest

from ionopt import units
from ionopt.backends.mock import MockBackend
from ionopt.config import ConfigError, ConfigurationDef
from ionopt.electrodes import JobValidationError, expand, expected_potentials, validate_job
from ionopt.jobs import build_job
from ionopt.optimize import SearchSpace, optimize
from ionopt.variants import VariantManifest, load_variant, registry, save_variant

MM = units.MM
WIRING = {"tip": "LV1", "e3": "LV2"}
CH = {"LV1": 100.0, "LV2": 60.0, "HV1": -3000.0, "HV4": -200.0}
POS = {"lens_gap": 10 * MM, "z_mcp": 145 * MM, "mesh_gap": 12.7 * MM}


def wide_mesh():
    return VariantManifest(
        variant_id="v-wide-mesh", inventory_items=["screen_mesh_wide"], approved=True,
        parameters=[{"name": "mesh_open_diameter", "comsol_name": "d_mesh_open", "as_built": 11, "range": [10, 40],
                     "inventory_item": "screen_mesh_wide"},
                    {"name": "grid_on", "comsol_name": "G1_on", "role": "switch", "unit": "", "as_built": 0,
                     "range": [0, 1]}],
        parts=[{"name": "g1", "selection": "geom1_G1_bnd", "potential_param": "G1_v", "present_when": "grid_on"}],
        mesh_open_fraction=0.7)


def no_mesh():
    return VariantManifest(variant_id="v-no-mesh", inventory_items=["no_screen_mesh"], approved=True,
                           removed_base=["screen_mesh"], mesh_open_fraction=1.0)


@pytest.fixture
def vcfg(cfg_tmp):
    save_variant(cfg_tmp, wide_mesh())
    save_variant(cfg_tmp, no_mesh())
    return cfg_tmp


def test_manifest_rules():
    with pytest.raises(ValueError, match="lengths"):
        VariantManifest(variant_id="x", parameters=[{"name": "a", "comsol_name": "a", "unit": "", "as_built": 0,
                                                     "range": [0, 1]}])
    with pytest.raises(ValueError, match="switches"):
        VariantManifest(variant_id="x", parameters=[{"name": "a", "comsol_name": "a", "role": "switch", "unit": "",
                                                     "as_built": 2, "range": [0, 1]}])
    reg = registry(wide_mesh())
    assert reg["mesh_open_diameter"].comsol_name == "d_mesh_open" and reg["mesh_open_diameter"].default == 11
    assert reg["v_g1"].comsol_name == "G1_v"


def test_jobs_with_a_variant(vcfg):
    conf = ConfigurationDef(config_id="w", cfg=1, wiring={**WIRING, "g1": "LV2"}, variant_id="v-wide-mesh",
                            variant_settings={"grid_on": 1})
    job = build_job(vcfg, conf, CH, {**POS, "mesh_open_diameter": 30 * MM})
    validate_job(job, vcfg)
    p = expand(job, vcfg)
    assert p["mesh_open_diameter"] == pytest.approx(30 * MM) and p["grid_on"] == 1 and p["v_g1"] == 60.0
    assert expected_potentials(job, vcfg)["sel_g1"] == 60.0
    # grid switched off: g1 does not exist, so it cannot be wired
    off = build_job(vcfg, conf.model_copy(update={"variant_settings": {"grid_on": 0}}), CH,
                    {**POS, "mesh_open_diameter": 30 * MM})
    with pytest.raises(JobValidationError, match="not connectable"):
        validate_job(off, vcfg)
    # outside the inventory range
    bad = build_job(vcfg, conf, CH, {**POS, "mesh_open_diameter": 45 * MM})
    with pytest.raises(JobValidationError, match="inventory range"):
        validate_job(bad, vcfg)
    # no mesh: transmission 1, no mesh selections expected
    nm = build_job(vcfg, ConfigurationDef(config_id="n", cfg=1, wiring=WIRING, variant_id="v-no-mesh"), CH, POS)
    assert nm.mesh_open_fraction == 1.0 and "sel_mesh_plane" not in expected_potentials(nm, vcfg)
    with pytest.raises(ConfigError, match="unknown model variant"):
        load_variant(vcfg, "v-missing")


def test_search_space_with_variant_variables(vcfg):
    conf = ConfigurationDef(config_id="w", cfg=1, wiring=WIRING, variant_id="v-wide-mesh")
    raw = SearchSpace.raw_ranges(vcfg, conf)
    assert raw["mesh_open_diameter_mm"] == (10.0, 40.0)
    sp = SearchSpace.from_config(vcfg, conf, {"mesh_open_diameter_mm": (20, 40)})
    assert sp.variable_ranges()["mesh_open_diameter_mm"] == pytest.approx((20, 40))
    nm = SearchSpace.raw_ranges(vcfg, ConfigurationDef(config_id="n", cfg=1, wiring=WIRING, variant_id="v-no-mesh"))
    assert nm["HV4"][0] == nm["HV4"][1] and nm["mesh_gap_mm"][0] == nm["mesh_gap_mm"][1]


@pytest.mark.parametrize("vid, settings", [("v-wide-mesh", {}), ("v-no-mesh", {})])
def test_optimize_a_variant_on_the_mock(vcfg, vid, settings):
    conf = ConfigurationDef(config_id=vid, cfg=1, wiring=WIRING, variant_id=vid, variant_settings=settings)
    res = optimize(vcfg, "ignored", budget=4, backend=MockBackend(vcfg), study_id=f"s-{vid}", conf=conf)
    assert res.n_trials == 4 and res.n_failed == 0
    job = json.loads((vcfg.path("results_dir") / res.best_job_id / "job.json").read_text())
    assert job["variant_id"] == vid
    if vid == "v-wide-mesh":
        assert 10 * MM <= res.best_positions["mesh_open_diameter"] <= 40 * MM
    else:
        m = json.loads((vcfg.path("results_dir") / res.best_job_id / "metrics.json").read_text())
        assert m["requirements"]["mesh_open_fraction"] == 1.0
        assert m["fate_counts"].get("mesh_frame", 0) == 0


def test_mesh_removed_after_a_wide_mesh(vcfg):
    """A no-mesh variant built on a wide-mesh one (run 2): the opening diameter it inherited is held fixed,
    plots draw no mesh and say so, and the critic is told the model has no mesh."""
    from ionopt.agents.summaries import variant_note, variants_lines
    from ionopt.plots import _stats_text, make_plots, mesh_present
    from ionopt.results import load_job

    m = wide_mesh().model_copy(update={"variant_id": "v-wide-then-none", "parent": "v-wide-mesh",
                                       "inventory_items": ["no_screen_mesh", "screen_mesh_wide"],
                                       "removed_base": ["screen_mesh"], "mesh_open_fraction": 1.0})
    save_variant(vcfg, m)
    conf = ConfigurationDef(config_id="wn", cfg=1, wiring=WIRING, variant_id="v-wide-then-none")
    assert SearchSpace.raw_ranges(vcfg, conf)["mesh_open_diameter_mm"] == (11.0, 11.0)
    c = vcfg.with_overrides(["optimizer.write_plots=true"])
    res = optimize(c, "ignored", budget=3, backend=MockBackend(c), study_id="s-wn", conf=conf)
    assert res.n_failed == 0
    d = c.path("results_dir") / res.best_job_id
    assert res.best_positions["mesh_open_diameter"] == pytest.approx(11 * MM)   # never sampled
    geom = json.loads((d / "geometry.json").read_text())
    assert geom["mesh_present"] is False and not mesh_present(geom)
    assert not mesh_present({"r_mesh_open_m": None}) and mesh_present({"r_mesh_open_m": 0.005})  # old results
    make_plots(d, c)
    assert (d / "plots" / "summary.png").is_file()
    txt = _stats_text(load_job(d), c, json.loads((d / "metrics.json").read_text()), {}, {}, geom)
    assert "collected (no mesh)" in txt and "MESH  none" in txt and "mesh_gap" not in txt
    note = variant_note(c, "v-wide-then-none")
    assert "NO SCREEN MESH" in note and "mesh_open_diameter is inactive" in note
    assert "NO SCREEN MESH" not in variant_note(c, "v-wide-mesh")

    class _S:                                   # variants_lines only needs the run's own variants
        model_variants = []
    assert any("mesh_open_diameter_mm INACTIVE" in ln for ln in variants_lines(c, _S()))


def _real_cfg1(c):
    """cfg 1 with the author's values (constraints.yaml, 2026-11-22), not the tests' fixed-MCP pins."""
    return c.with_overrides(["constraints.chamber_setups.1.z_mcp_mm=[10, 183.704]",
                             "constraints.chamber_setups.1.mesh_gap_mm=[12.7, 52.7]",
                             "constraints.chamber_setups.1.lens_gap_mm=[10, 53.0]",
                             "constraints.chamber_setups.1.mcp_rod_margin_mm=10",
                             "constraints.electrical.max_field_kV_per_mm=null"])


@pytest.mark.parametrize("vid, removed, moved", [
    (None, [], []),                                         # full stack, with the screen mesh
    ("v-no-mesh", [], []),                                  # full stack, no mesh: MCP right behind E9
    ("v-no-mesh", ["e5", "e6", "e7", "e8", "e9"], ["e4"]),  # short stack, last plate moved
])
def test_cfg1_mcp_on_the_rods_always_valid(vcfg, vid, removed, moved):
    from ionopt.config import ConfigurationDef
    from ionopt.electrodes import rear_reach
    import optuna
    c = _real_cfg1(vcfg)
    conf = ConfigurationDef(config_id="t", cfg=1, wiring={"tip": "LV1", "e1": "LV2", "e3": "LV3"},
                            removed=removed, moved=moved, variant_id=vid or "base")
    sp = SearchSpace.from_config(c, conf)
    reach = sp.stack_length / MM
    lo_z, hi_z = sp.variable_ranges()["z_mcp_mm"]
    gap_lo = 12.7 if vid is None else 0.0
    assert lo_z == pytest.approx(10 + reach + gap_lo, abs=1e-4)
    assert hi_z == pytest.approx(53.0 + 130.698)
    if not moved and vid == "v-no-mesh":       # E9 lip + min gap
        assert reach == pytest.approx(93.84 + rear_reach("accel", "mcp") / MM + 2.23)
    study = optuna.create_study(sampler=optuna.samplers.RandomSampler(seed=3))
    zs, rel = [], []
    for _ in range(200):
        ch, pos = sp.suggest(study.ask())
        validate_job(build_job(c, conf, ch, pos), c)      # raises on a collision or an MCP past the rods
        assert sp.contains(ch, pos)
        zs.append(pos["z_mcp"] / MM)
        rel.append((pos["z_mcp"] - pos["lens_gap"]) / MM)
    assert min(zs) < lo_z + 20 and max(zs) > hi_z - 20     # the MCP explores its range
    assert max(rel) <= 130.698 + 1e-6


def test_cfg1_stack_too_long_for_the_rods(vcfg):
    """With the mesh, the full stack + 52.7 mm gap cannot fit, but the gap shrinks to what fits."""
    from ionopt.config import ConfigurationDef
    c = _real_cfg1(vcfg)
    conf = ConfigurationDef(config_id="t", cfg=1, wiring={"tip": "LV1", "e1": "LV2"})
    sp = SearchSpace.from_config(c, conf)
    assert sp.gap_dependent
    assert sp.mesh_gap_max(sp.z_mcp[1]) / MM == pytest.approx(130.698 - sp.stack_length / MM, abs=1e-3)
    c2 = c.with_overrides(["constraints.chamber_setups.1.mcp_rod_margin_mm=30"])   # 110.698 < 113.97 + 12.7
    with pytest.raises(ConfigError, match="does not fit on the rods"):
        SearchSpace.from_config(c2, conf)
