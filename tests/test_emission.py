import math

import numpy as np
import pytest

from ionopt import emission as em

TH = em.eval_grid()


def identity_map(max_deg=89.5, n=180):
    t = np.radians(np.linspace(0, max_deg, n))
    return em.AngleMap(t, t.copy())


def test_hwhm_sigma_roundtrip():
    assert em.sigma_to_hwhm(em.hwhm_to_sigma(0.3)) == pytest.approx(0.3)
    assert em.HWHM_PER_SIGMA == pytest.approx(math.sqrt(2 * math.log(2)))


def test_target_cdf_matches_quadrature():
    from scipy.integrate import quad
    s = em.hwhm_to_sigma(math.radians(20))
    f = lambda u: math.exp(-u * u / (2 * s * s)) * math.sin(u)   # dI/dOmega * sin = density in theta
    norm = quad(f, 0, math.pi / 2)[0]
    for deg in (5, 20, 35, 60):
        t = math.radians(deg)
        assert em.target_cdf(np.array([t]), s)[0] == pytest.approx(quad(f, 0, t)[0] / norm, abs=1e-5)


def test_identity_map_omega_family_recovers_target():
    m = identity_map()
    s_t = em.hwhm_to_sigma(math.radians(20))
    pars = em.hwhm_to_sigma(np.radians(np.arange(5, 40, 0.25)))
    r = em.sweep(m, "omega", pars, s_t, TH)
    assert math.degrees(em.sigma_to_hwhm(r["best"])) == pytest.approx(20, abs=0.3)
    assert r["best_rms"] < 2e-3
    assert math.degrees(r["best_equiv_hwhm"]) == pytest.approx(20, abs=0.3)


def test_identity_map_beam_family_small_angle():
    # small angles: Rayleigh slope with sigma_s == Gaussian dI/dOmega with sigma = sigma_s
    m = identity_map()
    s_t = em.hwhm_to_sigma(math.radians(3))
    r = em.sweep(m, "beam", np.linspace(0.01, 0.1, 361), s_t, TH)
    assert r["best"] == pytest.approx(s_t, rel=0.02)


def test_compressing_map_needs_wider_launch():
    # theta_ext = theta0 / 2  ->  launch spread must be twice the target
    t = np.radians(np.linspace(0, 89.5, 180))
    m = em.AngleMap(t, t / 2)
    s_t = em.hwhm_to_sigma(math.radians(10))
    pars = em.hwhm_to_sigma(np.radians(np.arange(5, 40, 0.25)))
    r = em.sweep(m, "omega", pars, s_t, TH)
    assert math.degrees(em.sigma_to_hwhm(r["best"])) == pytest.approx(20, abs=0.6)


def test_sample_cdf_matches_weighted():
    rng = np.random.default_rng(0)
    s = 0.2
    sx, sy = rng.normal(0, s, 200000), rng.normal(0, s, 200000)
    th0 = np.arctan(np.hypot(sx, sy))
    c_mc = em.sample_cdf(th0, TH)
    c_an, lost = em.extractor_cdf(identity_map(), "beam", s, TH)
    assert em.cdf_ks(c_mc, c_an) < 0.01 and lost < 1e-6


def test_plane_crossing_linear():
    t = np.linspace(0, 1, 11)
    z = np.vstack([10 * t, 5 * t, 20 * t])          # 3 particles; the 2nd never reaches z = 6
    v = np.vstack([t, t, t])
    (vc,) = em.plane_crossing(z, v, z_plane=6.0)
    assert vc[0] == pytest.approx(0.6) and math.isnan(vc[1]) and vc[2] == pytest.approx(0.3)
