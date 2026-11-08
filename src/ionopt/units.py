"""Physical constants and unit conversions.

Internal convention: SI for lengths (m), times (s), velocities (m/s), potentials (V),
masses (kg). Kinetic energies are carried in eV (column/key names always say so).
Config files use the units named in their keys; convert with the helpers below.
"""
from __future__ import annotations

E_CHARGE = 1.602176634e-19  # C (exact)
DALTON = 1.66053906660e-27  # kg

MM = 1e-3
UM = 1e-6
NM = 1e-9
US = 1e-6
DEG = 3.141592653589793 / 180.0


def ke_eV_to_speed(ke_eV, mass_kg):
    """Speed (m/s) from kinetic energy in eV. Works on floats and numpy arrays."""
    import numpy as np

    return np.sqrt(2.0 * np.asarray(ke_eV) * E_CHARGE / mass_kg)


def speed_to_ke_eV(speed, mass_kg):
    import numpy as np

    return 0.5 * mass_kg * np.asarray(speed) ** 2 / E_CHARGE
