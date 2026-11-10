"""Emission-model calibration: which launch angular spread gives a target spread at the extractor.

Target (phenomenological): at a plane just in front of the extractor (L1), the beam's angular
distribution is Gaussian-like in the polar angle theta from the axis,
    dI/dOmega ~ exp(-theta^2 / (2 sigma_t^2)),   HWHM = sigma_t * sqrt(2 ln 2).

Method: one simulation launches a fan of rays at initial polar angles theta0 (fixed kinetic energy)
and records each ray's angle theta_ext where it crosses the plane. That map theta_ext(theta0) is
independent of the launch distribution, so any candidate distribution of theta0 is evaluated by
reweighting the map, with no further simulation. Two candidate families:

  'beam'  COMSOL Particle Beam with Gaussian transverse sampling: slopes s_x = vx/vz and s_y = vy/vz
          are independent normal with std sigma_s (the speed is fixed by the beam energy), so
          tan(theta0) = |s| is Rayleigh(sigma_s).  Parameter: sigma_s (dimensionless slope).
  'omega' launch.py's grid: dI/dOmega ~ exp(-theta0^2 / (2 sigma0^2)) for theta0 <= theta_max.
          Parameter: sigma0 (rad); launch.hwhm_deg = degrees(sigma0) * sqrt(2 ln 2).

Distributions are compared through their cumulative distribution functions (CDF) of theta on
[0, 90 deg]: objective = RMS of the CDF difference; the KS distance (max difference) is reported too.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

FWHM_PER_SIGMA = 2.0 * math.sqrt(2.0 * math.log(2.0))
HWHM_PER_SIGMA = FWHM_PER_SIGMA / 2.0
HALF_PI = math.pi / 2.0


def hwhm_to_sigma(hwhm_rad: float) -> float:
    return hwhm_rad / HWHM_PER_SIGMA


def sigma_to_hwhm(sigma_rad: float) -> float:
    return sigma_rad * HWHM_PER_SIGMA


# --------------------------------------------------------------------------- distributions


def eval_grid(n: int = 901) -> np.ndarray:
    """Angles (rad) on which CDFs are compared: 0..90 deg."""
    return np.linspace(0.0, HALF_PI, n)


def target_cdf(theta: np.ndarray, sigma_t: float) -> np.ndarray:
    """CDF on [0, pi/2] of dI/dOmega ~ exp(-theta^2/2 sigma_t^2), i.e. density ~ exp(..) sin(theta)."""
    fine = np.linspace(0.0, HALF_PI, 4001)
    pdf = np.exp(-fine**2 / (2.0 * sigma_t**2)) * np.sin(fine)
    c = np.concatenate([[0.0], np.cumsum(0.5 * (pdf[1:] + pdf[:-1]) * np.diff(fine))])
    return np.interp(theta, fine, c / c[-1])


def pdf_beam(theta0: np.ndarray, sigma_s: float) -> np.ndarray:
    """Density of theta0 for the 'beam' family (Rayleigh slope magnitude), unnormalized."""
    s = np.tan(theta0)
    return s / sigma_s**2 * np.exp(-s**2 / (2.0 * sigma_s**2)) / np.cos(theta0) ** 2


def pdf_omega(theta0: np.ndarray, sigma0: float, theta_max: float) -> np.ndarray:
    """Density of theta0 for the 'omega' family (Gaussian dI/dOmega, cut at theta_max), unnormalized."""
    return np.where(theta0 <= theta_max, np.exp(-theta0**2 / (2.0 * sigma0**2)) * np.sin(theta0), 0.0)


@dataclass
class AngleMap:
    """theta_ext(theta0) from one fan-of-rays run (radians). Rays that did not cross are dropped."""
    theta0: np.ndarray
    theta_ext: np.ndarray

    def __post_init__(self):
        o = np.argsort(self.theta0)
        self.theta0 = np.asarray(self.theta0, float)[o]
        self.theta_ext = np.asarray(self.theta_ext, float)[o]
        ok = np.isfinite(self.theta_ext)
        self.theta0, self.theta_ext = self.theta0[ok], self.theta_ext[ok]

    def resample(self, n: int = 20001) -> tuple[np.ndarray, np.ndarray]:
        t0 = np.linspace(self.theta0[0], self.theta0[-1], n)
        return t0, np.interp(t0, self.theta0, self.theta_ext)


def weighted_cdf(values: np.ndarray, weights: np.ndarray, theta: np.ndarray) -> np.ndarray:
    o = np.argsort(values)
    v, w = values[o], weights[o]
    c = np.cumsum(w)
    c /= c[-1]
    return np.interp(theta, v, c, left=0.0, right=1.0)


def sample_cdf(values: np.ndarray, theta: np.ndarray) -> np.ndarray:
    v = np.sort(np.asarray(values, float)[np.isfinite(values)])
    return np.searchsorted(v, theta, side="right") / len(v)


def extractor_cdf(m: AngleMap, family: str, par: float, theta: np.ndarray,
                  theta_max: float = HALF_PI) -> tuple[np.ndarray, float]:
    """CDF of theta_ext for a launch family/parameter, and the launch probability outside the map range."""
    t0, te = m.resample()
    full = np.linspace(0.0, HALF_PI - 1e-9, 40001)
    if family == "beam":
        w, wf = pdf_beam(t0, par), pdf_beam(full, par)
    elif family == "omega":
        w, wf = pdf_omega(t0, par, theta_max), pdf_omega(full, par, theta_max)
    else:
        raise ValueError(f"unknown family {family!r}")
    lost = 1.0 - float(np.trapezoid(w, t0) / np.trapezoid(wf, full))
    w = np.where(np.isfinite(w), w, 0.0)
    return weighted_cdf(te, w, theta), max(lost, 0.0)


def cdf_rms(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def cdf_ks(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.max(np.abs(a - b)))


def equivalent_hwhm(cdf: np.ndarray, theta: np.ndarray) -> float:
    """HWHM (rad) of the Gaussian-dI/dOmega distribution whose CDF is closest (RMS) to cdf."""
    sig = np.radians(np.arange(0.2, 89.0, 0.05))
    err = [cdf_rms(cdf, target_cdf(theta, s)) for s in sig]
    return sigma_to_hwhm(float(sig[int(np.argmin(err))]))


def median_angle(cdf: np.ndarray, theta: np.ndarray) -> float:
    return float(np.interp(0.5, cdf, theta))


def sweep(m: AngleMap, family: str, pars: np.ndarray, sigma_t: float, theta: np.ndarray,
          theta_max: float = HALF_PI) -> dict:
    """Objective (CDF RMS vs target) over a parameter grid; returns arrays and the best entry."""
    tgt = target_cdf(theta, sigma_t)
    rms, ks, lost = [], [], []
    for p in pars:
        c, lo = extractor_cdf(m, family, float(p), theta, theta_max)
        rms.append(cdf_rms(c, tgt))
        ks.append(cdf_ks(c, tgt))
        lost.append(lo)
    i = int(np.argmin(rms))
    best_cdf, _ = extractor_cdf(m, family, float(pars[i]), theta, theta_max)
    return {"pars": np.asarray(pars), "rms": np.array(rms), "ks": np.array(ks), "lost": np.array(lost),
            "best": float(pars[i]), "best_rms": rms[i], "best_ks": ks[i], "best_lost": lost[i],
            "best_cdf": best_cdf, "best_equiv_hwhm": equivalent_hwhm(best_cdf, theta),
            "best_median": median_angle(best_cdf, theta), "at_edge": i in (0, len(pars) - 1)}


# --------------------------------------------------------------------------- trajectories


def plane_crossing(z: np.ndarray, *cols: np.ndarray, z_plane: float) -> tuple[np.ndarray, ...]:
    """First upward crossing of z = z_plane for trajectories sampled at output times.

    z and every col are [particle, time]. Returns, per particle, each col linearly interpolated
    to the crossing (NaN if the particle never reaches the plane).
    """
    z = np.asarray(z, float)
    n = z.shape[0]
    out = [np.full(n, np.nan) for _ in cols]
    above = np.nan_to_num(z, nan=-np.inf) >= z_plane
    for p in range(n):
        k = np.flatnonzero(above[p])
        if len(k) == 0:
            continue
        k = int(k[0])
        if k == 0:
            f, k0 = 0.0, 0
        else:
            k0 = k - 1
            f = (z_plane - z[p, k0]) / (z[p, k] - z[p, k0])
        for o, c in zip(out, cols):
            o[p] = c[p, k0] + f * (c[p, k] - c[p, k0]) if k > 0 else c[p, 0]
    return tuple(out)
