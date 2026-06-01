"""Tests for the pure-numpy forcing/physics layer (no dolfinx required)."""

import numpy as np

from inthermo import forcing
from inthermo.parameters import CONDOR


def test_joule_matches_per_length_power():
    g = CONDOR.geometry
    e = CONDOR.electrical
    q = forcing.joule_volumetric_heat(900.0, e.r_ac_per_length, g.area_aluminum)
    # q * A_alu should equal I^2 * R per unit length
    assert np.isclose(q * g.area_aluminum, 900.0**2 * e.r_ac_per_length)


def test_joule_scales_quadratically():
    g = CONDOR.geometry
    e = CONDOR.electrical
    q1 = forcing.joule_volumetric_heat(450.0, e.r_ac_per_length, g.area_aluminum)
    q2 = forcing.joule_volumetric_heat(900.0, e.r_ac_per_length, g.area_aluminum)
    assert np.isclose(q2 / q1, 4.0)


def test_solar_flux_is_diameter_independent():
    q = forcing.solar_surface_flux(1000.0, CONDOR.radiative.solar_absorptivity)
    assert np.isclose(q, 0.5 * 1000.0 / np.pi)


def test_convection_increases_with_wind():
    g = CONDOR.geometry
    h = forcing.ieee738_convection_coefficient(
        75.0, 40.0, np.array([0.0, 1.0, 5.0]), g.d_outer
    )
    assert h[0] < h[1] < h[2]
    assert np.all(h > 0)


def test_natural_convection_floor_with_no_wind():
    g = CONDOR.geometry
    # With zero wind, forced term collapses and natural convection dominates.
    h = forcing.ieee738_convection_coefficient(75.0, 40.0, 0.0, g.d_outer)
    assert 3.0 < float(h) < 15.0


def test_convection_broadcasts_over_arrays():
    g = CONDOR.geometry
    ts = np.array([50.0, 75.0])
    ta = np.array([30.0, 40.0])
    ws = np.array([2.0, 2.0])
    h = forcing.ieee738_convection_coefficient(ts, ta, ws, g.d_outer)
    assert h.shape == (2,)
