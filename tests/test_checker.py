import math

import numpy as np
import pandas as pd
import pytest

from ionopt.backends.mock import MockBackend
from ionopt.checker import check, convergence_check, recheck, weighted_quantile
from ionopt.config import ConfigError, TBDError
from ionopt.schemas import FATES, FILES

from helpers import einzel_job

Z_MCP, F0, SIG_MCP = 0.145, 0.02, 80e-6


def run(cfg, **job_kw):
    res = MockBackend(cfg).run(einzel_job(cfg, **job_kw))
    return res, check(res.result_dir, cfg)


def no_chroma(cfg, *extra):
    return cfg.with_overrides(["backend.mock.chroma_min_m_per_eV=0", "backend.mock.chroma_coeff_m_per_eV=0", *extra])


def test_weighted_quantile():
    x = np.array([1.0, 2.0, 3.0, 4.0])
    assert weighted_quantile(x, np.ones(4), 0.5) == 2.0
    assert weighted_quantile(x, np.array([0, 0, 0, 1.0]), 0.1) == 4.0
    assert math.isnan(weighted_quantile(np.array([]), np.array([]), 0.5))


def test_score_matches_analytic_pure_mcp_resolution(cfg_tmp):
    c = no_chroma(cfg_tmp)
    _, m = run(c)
    assert m.valid and m.feasible, m.flags
    h = math.radians(c.spec.launch.theta_max_deg / (c.spec.launch.n_theta - 1))
    # forward difference at theta = 0 is the smallest slope: z f tan(h)/h
    expect = math.degrees(SIG_MCP / (Z_MCP * F0 * math.tan(h) / h))
    assert m.score == pytest.approx(expect, rel=1e-9)
    mp = m.mapping
    np.testing.assert_allclose(mp["r_mm"], Z_MCP * F0 * np.tan(np.radians(mp["theta_deg"])) * 1e3, rtol=1e-9)
    assert max(mp["sigma_E_mm"]) == pytest.approx(0, abs=1e-12)
    assert mp["monotonic"] and mp["n_eval"] == c.spec.launch.n_theta


def test_chromatic_spread(cfg_tmp):
    _, m = run(cfg_tmp)   # lens and mesh at the mock optimum -> chroma = chroma_min
    L = cfg_tmp.spec.launch
    std_E = L.dE_eV / L.n_E * math.sqrt((L.n_E ** 2 - 1) / 12)        # discrete uniform grid
    expect_mm = cfg_tmp.backend.mock.chroma_min_m_per_eV * std_E * 1e3
    np.testing.assert_allclose(m.mapping["sigma_E_mm"][3:], expect_mm, rtol=1e-9)


def test_fates_and_eta_with_mesh_clipping(cfg_tmp):
    c = no_chroma(cfg_tmp, "backend.mock.f0=0.3")
    res, m = run(c)
    launch = pd.read_csv(res.files["ions_launch"])
    z_mesh = Z_MCP - 0.0127
    clipped = z_mesh * 0.3 * np.tan(np.radians(launch["theta_deg"])) > 0.005
    w = launch["weight"]
    assert m.fates["mesh_frame"] == pytest.approx(w[clipped].sum())
    assert m.fates["mcp_active"] == pytest.approx(w[~clipped].sum())
    assert sum(m.fates.values()) == pytest.approx(1.0)
    assert sum(m.fate_counts[f] for f in FATES) == len(launch)
    assert m.requirements["eta"] == pytest.approx(0.8 * w[~clipped].sum())
    assert m.mapping["n_eval"] == 4                     # theta = 0, 2, 4, 6 deg land; 8 deg is clipped
    assert m.mapping["eval_theta_max_deg"] == pytest.approx(6.0)
    assert not m.feasible and any("collection efficiency" in f for f in m.flags)


def test_spot_statistics_hand_computed(cfg_tmp):
    res, m = run(cfg_tmp, fidelity="3d")
    dv = pd.read_csv(f"{res.result_dir}/{FILES['ions_derived']}")
    a = dv[dv["fate"] == "mcp_active"]
    w = a["weight"].to_numpy()
    r = a["r_land_mm"].to_numpy()
    assert m.spot["rms_axis_mm"] == pytest.approx(np.sqrt(np.sum(w * r ** 2) / w.sum()))
    assert m.spot["r_max_mm"] == pytest.approx(r.max())
    assert m.spot["fill_fraction"] == pytest.approx(m.spot["r90_mm"] / 20.0)
    assert abs(m.spot["centroid_x_mm"]) < 1e-6 and abs(m.spot["centroid_y_mm"]) < 1e-6
    assert m.spot["impact_KE_mean_eV"] == pytest.approx(np.sum(w * a["impact_KE_eV"]) / w.sum())
    # landing energy = KE0 + q (V_tip - V_mcp) = KE0 + 100 + 5000
    assert m.spot["impact_KE_min_eV"] == pytest.approx(cfg_tmp.spec.launch.E0_eV - 1 + 2 / 6 + 5100)
    assert m.spot["frac_above_threshold"] == 1.0


def test_fold_fails_monotonicity(cfg_tmp):
    c = no_chroma(cfg_tmp, "backend.mock.fold_theta_deg=30")
    _, m = run(c)
    assert m.valid and not m.mapping["monotonic"] and not m.feasible
    assert any("not monotonic" in f for f in m.flags)


@pytest.mark.parametrize("inject, key", [
    ("missing_file", "files_present"),
    ("in_flight", "no_in_flight"),
    ("potential_mismatch", "potentials_match"),
    ("energy_error", "energy_conserved"),
])
def test_injected_problems_make_run_invalid(cfg_tmp, inject, key):
    _, m = run(cfg_tmp, tags={"mock_inject": inject})
    assert not m.valid and not m.feasible
    assert m.validity.get(key) is False, (m.validity, m.flags)


def test_failed_run_is_invalid(cfg_tmp):
    _, m = run(cfg_tmp, tags={"mock_inject": "timeout"})
    assert not m.valid and m.score is None and "timeout" in m.flags[0]


def test_missing_ions_detected(cfg_tmp):
    res = MockBackend(cfg_tmp).run(einzel_job(cfg_tmp))
    f = pd.read_csv(res.files["ions_final"])
    f.iloc[:-3].to_csv(res.files["ions_final"], index=False)
    m = check(res.result_dir, cfg_tmp)
    assert not m.validity["fate_counts_complete"] and m.fate_counts["missing"] == 3


def test_recheck_changes_verdict_without_rerun(cfg_tmp):
    res, m = run(cfg_tmp)
    assert m.feasible
    mtime = (pd.io.common.Path(res.files["ions_final"])).stat().st_mtime
    strict = cfg_tmp.with_overrides(["spec.requirements.eta_min=0.95"])
    (m2,) = recheck(cfg_tmp.path("results_dir"), strict)
    assert not m2.feasible and m2.spec_hash != m.spec_hash
    assert pd.io.common.Path(res.files["ions_final"]).stat().st_mtime == mtime
    # threshold change flips the fast-fraction requirement
    m3 = check(res.result_dir, cfg_tmp.with_overrides(["spec.requirements.impact_threshold_eV_per_charge=6000"]))
    assert m3.requirements["frac_fast"] == 0 and not m3.feasible


def test_speed_threshold_uses_threshold_species_mass(cfg_tmp):
    res, _ = run(cfg_tmp)
    # landing KE ~5102 eV; Na+ speed ~2.06e5 m/s, a 1000 Da ion only ~3.1e4 m/s
    base = ["spec.requirements.impact_threshold_eV_per_charge=null", "spec.requirements.impact_threshold_mps=1e5"]
    assert check(res.result_dir, cfg_tmp.with_overrides(base)).requirements["frac_fast"] == 1.0
    heavy = cfg_tmp.with_overrides(base + ["spec.requirements.threshold_species_mass_Da=1000"])
    assert check(res.result_dir, heavy).requirements["frac_fast"] == 0.0


def test_optional_constraints(cfg_tmp):
    res, _ = run(cfg_tmp)
    m = check(res.result_dir, cfg_tmp.with_overrides(["spec.requirements.optional_constraints={min_fill_fraction: 0.9}"]))
    assert not m.feasible and m.requirements["opt_min_fill_fraction"] is False
    with pytest.raises(ConfigError, match="unknown statistic"):
        check(res.result_dir, cfg_tmp.with_overrides(["spec.requirements.optional_constraints={min_nope: 1}"]))


def test_tbd_value_stops_checker(cfg_tmp):
    res, _ = run(cfg_tmp)
    with pytest.raises(TBDError, match="sigma_mcp_um"):
        check(res.result_dir, cfg_tmp.with_overrides(["spec.detector.sigma_mcp_um=null"]))


def test_spline_method(cfg_tmp):
    c = no_chroma(cfg_tmp, "spec.analysis.drdtheta_method=spline")
    _, m = run(c)
    expect = math.degrees(SIG_MCP / (Z_MCP * F0))         # exact slope at theta = 0
    assert m.score == pytest.approx(expect, rel=1e-3)


def test_convergence_check(cfg_tmp):
    res, m = run(cfg_tmp)
    conv_job = einzel_job(cfg_tmp, ion_level="convergence")
    m2 = check(MockBackend(cfg_tmp).run(conv_job).result_dir, cfg_tmp)
    out = convergence_check(m, m2, cfg_tmp)
    assert out["rel_change_eta"] < 0.05
    assert "passed" in out


def test_energy_abs_tolerance(cfg_tmp):
    # +10% injected error: fails the relative limit; passes only if the absolute floor covers it
    res, m = run(cfg_tmp, tags={"mock_inject": "energy_error"})
    from pathlib import Path
    d = pd.read_csv(Path(res.result_dir) / "ions_derived.csv")
    worst = float(d["energy_error_eV"].abs().max())
    assert not m.validity["energy_conserved"]
    loose = check(res.result_dir, cfg_tmp.with_overrides([f"spec.tolerances.energy_conservation_abs_eV={worst * 1.01}"]))
    assert loose.validity["energy_conserved"]
    tight = check(res.result_dir, cfg_tmp.with_overrides([f"spec.tolerances.energy_conservation_abs_eV={worst * 0.5}"]))
    assert not tight.validity["energy_conserved"]
