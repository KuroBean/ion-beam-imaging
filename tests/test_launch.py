import numpy as np
import pytest
from scipy import integrate

from ionopt import units
from ionopt.config import TBDError
from ionopt.launch import energy_grid, make_launch, write_release_file


def test_weights_sum_to_one(cfg):
    for fid in ("2d", "3d"):
        df = make_launch(cfg.spec.launch, fid)
        assert df["weight"].sum() == pytest.approx(1.0)
        assert (df["weight"] >= 0).all()
        assert df["ion_id"].tolist() == list(range(len(df)))


def test_grid_sizes(cfg):
    L = cfg.spec.launch
    assert len(make_launch(L, "2d")) == L.n_theta * L.n_E
    assert len(make_launch(L, "3d")) == ((L.n_theta - 1) * L.n_phi + 1) * L.n_E
    conv = make_launch(L, "2d", ion_level="convergence")
    assert conv["theta_deg"].nunique() == (L.n_theta - 1) * L.convergence_ion_factor + 1
    # search grid points are a subset of the convergence grid
    assert set(np.round(make_launch(L, "2d")["theta_deg"], 9)) <= set(np.round(conv["theta_deg"], 9))


def test_intensity_per_solid_angle_has_target_hwhm(cfg):
    L = cfg.with_overrides(["spec.launch.n_theta=201"]).spec.launch
    df = make_launch(L, "2d")
    g = df.groupby("theta_deg")["weight"].sum()
    th = np.radians(g.index.to_numpy())
    dth = np.full(len(th), th[1] - th[0])
    dth[[0, -1]] *= 0.5
    intensity = g.to_numpy()[1:] / (np.sin(th[1:]) * dth[1:])     # dI/dOmega up to a constant
    intensity /= intensity[0] / np.exp(-th[1] ** 2 / (2 * L.sigma_rad ** 2))   # normalize to theta -> 0
    half = np.interp(0.5, intensity[::-1], np.degrees(th[1:])[::-1])
    assert half == pytest.approx(L.hwhm_deg, abs=0.05)


def test_weighted_theta_histogram_matches_analytic_marginal(cfg):
    L = cfg.with_overrides(["spec.launch.n_theta=101"]).spec.launch
    df = make_launch(L, "3d")
    th = np.radians(df["theta_deg"].to_numpy())
    mean_num = np.sum(df["weight"] * th)
    tmax, s = np.radians(L.theta_max_deg), L.sigma_rad
    p = lambda t: np.exp(-t**2 / (2 * s**2)) * np.sin(t)
    mean_ref = integrate.quad(lambda t: t * p(t), 0, tmax)[0] / integrate.quad(p, 0, tmax)[0]
    assert mean_num == pytest.approx(mean_ref, rel=1e-3)


def test_ke_recovered_from_velocity(cfg):
    L = cfg.spec.launch
    df = make_launch(L, "3d")
    v = np.sqrt(df["vx_mps"]**2 + df["vy_mps"]**2 + df["vz_mps"]**2)
    ke = units.speed_to_ke_eV(v, L.mass_Da * units.DALTON)
    np.testing.assert_allclose(ke, df["KE0_eV"], rtol=1e-12)
    # direction matches theta / phi
    th = np.degrees(np.arccos(df["vz_mps"] / v))
    np.testing.assert_allclose(th, df["theta_deg"], atol=1e-9)


def test_energy_grid_uniform_and_custom():
    ke, w = energy_grid(2.0, 2.0, 4)
    np.testing.assert_allclose(ke, [1.25, 1.75, 2.25, 2.75])
    np.testing.assert_allclose(w, 0.25)
    ke, w = energy_grid(2.0, 2.0, 4, energy_weight=lambda e: e)
    assert w.sum() == pytest.approx(1) and w[-1] > w[0]
    assert energy_grid(2.0, 2.0, 1)[0].tolist() == [2.0]


def test_tbd_launch_value_names_key(cfg):
    L = cfg.with_overrides(["spec.launch.E0_eV=null"]).spec.launch
    with pytest.raises(TBDError, match=r"spec\.launch\.E0_eV is TBD"):
        make_launch(L, "2d")
    L = cfg.with_overrides(["spec.launch.n_phi=null"]).spec.launch
    make_launch(L, "2d")                    # n_phi only needed in 3D
    with pytest.raises(TBDError, match="n_phi"):
        make_launch(L, "3d")


def test_release_file_2d_format(cfg, tmp_path):
    df = make_launch(cfg.spec.launch, "2d")
    f = tmp_path / "rel.txt"
    write_release_file(df, f, "2d", z_shift_m=0.105, axis_offset_m=1e-9)
    a = np.loadtxt(f, comments="%")
    assert a.shape == (len(df), 4)
    assert a[:, 0].min() == pytest.approx(1e-6)           # r in mm, at least the axis offset
    np.testing.assert_allclose(a[:, 1], 105.0 + df["z_m"] * 1e3)
    np.testing.assert_allclose(a[:, 2], np.hypot(df["vx_mps"], df["vy_mps"]), rtol=1e-9)
    np.testing.assert_allclose(a[:, 3], df["vz_mps"], rtol=1e-9)


def test_negative_charge_allowed(cfg):
    L = cfg.with_overrides(["spec.launch.charge=-1"]).spec.launch
    df = make_launch(L, "2d")
    assert (df["vz_mps"] > 0).all()


def test_preacceleration_formula(cfg):
    import math

    from ionopt.launch import emission_distance_m, preacceleration
    L = cfg.spec.launch.model_copy(update={"hwhm_deg": 20.0, "emitter_radius_nm": 50.0,
                                           "model_tip_radius_um": 100.0, "emission_distance_um": None})
    s = emission_distance_m(L)
    assert s == pytest.approx(100e-6 / math.tan(math.radians(20)))
    D, re = 13.482e-3, 50e-9
    p = preacceleration(L, 100.0, 0.0, D)
    # exact axial potential of a hyperboloid emitter facing a plane (prolate spheroidal coordinates)
    eta0 = 1 / math.sqrt(1 + re / D)
    f = lambda e: math.log((1 + e) / (1 - e))   # noqa: E731
    exact = 1 - f((D - s) * eta0 / D) / f(eta0)
    assert p["potential_fraction"] == pytest.approx(exact, rel=2e-3)
    assert p["preaccel_eV"] == pytest.approx(100.0 * p["potential_fraction"])
    # signed charge and potential difference; explicit distance overrides the cone construction
    assert preacceleration(L.model_copy(update={"charge": -1}), 0.0, 100.0, D)["preaccel_eV"] == pytest.approx(p["preaccel_eV"])
    assert preacceleration(L.model_copy(update={"emission_distance_um": 10.0}), 100.0, 0.0, D)["emission_distance_m"] == pytest.approx(10e-6)
    with pytest.raises(ValueError):
        preacceleration(L.model_copy(update={"emission_distance_um": 2e4}), 100.0, 0.0, D)


def test_make_launch_preaccel_shift(cfg):
    L = cfg.spec.launch
    base = make_launch(L, "3d")
    shifted = make_launch(L, "3d", preaccel_eV=50.0)
    assert np.allclose(shifted["KE0_eV"], base["KE0_eV"] + 50.0)
    assert np.allclose(shifted["weight"], base["weight"])
    with pytest.raises(ValueError, match="retarding"):
        make_launch(L, "3d", preaccel_eV=-L.E0_eV)
