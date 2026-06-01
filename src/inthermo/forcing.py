"""Time-dependent boundary forcing and heat sources.

These are pure-``numpy`` helpers (no FEniCSx dependency) so they can be unit
tested and reused for plotting/diagnostics. They implement the physics that
``solver.py`` feeds into the FEniCSx variational problem each time step:

* :func:`joule_volumetric_heat` -- internal heat generation in the aluminum.
* :func:`solar_surface_flux`    -- solar gain on the outer boundary.
* :func:`ieee738_convection_coefficient` -- convective film coefficient ``h``.

Convention: ``q_conv`` and ``q_solar`` are *surface* fluxes [W/m^2] applied on
the outer boundary; ``q_joule`` is a *volumetric* source [W/m^3] in the
aluminum subdomain. Temperatures are in degrees Celsius unless stated.
"""

from __future__ import annotations

import numpy as np

# ----------------------------------------------------------------------------
# Internal heat generation (Joule effect, aluminum only)
# ----------------------------------------------------------------------------


def joule_volumetric_heat(current, r_ac_per_length, area_aluminum):
    """Volumetric Joule heat source in the aluminum subdomain [W/m^3].

    ``q_alu = I^2 * R_AC / A_alu`` where ``R_AC`` is per unit length [ohm/m] so
    ``I^2 * R_AC`` is power per unit length [W/m]; dividing by the aluminum
    cross-section gives a volumetric source. The steel core source is zero.
    """
    current = np.asarray(current, dtype=float)
    return current**2 * r_ac_per_length / area_aluminum


# ----------------------------------------------------------------------------
# Solar gain on the outer boundary
# ----------------------------------------------------------------------------


def solar_surface_flux(q_solar, solar_absorptivity):
    """Absorbed solar flux averaged over the conductor perimeter [W/m^2].

    A horizontal cylinder of diameter ``D`` intercepts ``alpha * Q_solar * D``
    watts per metre of length (projected area = diameter). Spreading that over
    the perimeter ``pi * D`` gives a uniform surface flux::

        q_solar_surface = alpha * Q_solar / pi

    The ``D`` cancels, so the result is independent of diameter. (The datasheet
    in ``gemini_info.md`` writes ``alpha * Q / (pi * D)``; that expression is
    dimensionally W/m^3 -- the ``D`` is a typo. The form used here is the
    dimensionally consistent surface flux.)
    """
    q_solar = np.asarray(q_solar, dtype=float)
    return solar_absorptivity * q_solar / np.pi


# ----------------------------------------------------------------------------
# IEEE 738 convective cooling
# ----------------------------------------------------------------------------


def _air_properties(t_film_c, elevation_m=0.0):
    """Air properties at the film temperature (IEEE 738-2012 fits).

    Parameters in degrees Celsius. Returns ``(k_f, mu_f, rho_f)`` with units
    W/(m*K), kg/(m*s), kg/m^3.
    """
    t_film_c = np.asarray(t_film_c, dtype=float)
    # Thermal conductivity of air [W/(m*K)]
    k_f = 2.424e-2 + 7.477e-5 * t_film_c - 4.407e-9 * t_film_c**2
    # Dynamic viscosity [kg/(m*s)] (T in Kelvin inside the fit)
    t_k = t_film_c + 273.15
    mu_f = (1.458e-6 * t_k**1.5) / (t_k + 110.4)
    # Air density [kg/m^3] accounting for elevation
    rho_f = (1.293 - 1.525e-4 * elevation_m + 6.379e-9 * elevation_m**2) / (
        1.0 + 0.00367 * t_film_c
    )
    return k_f, mu_f, rho_f


def ieee738_convection_coefficient(
    t_surface_c,
    t_ambient_c,
    wind_speed,
    diameter,
    wind_angle_deg=90.0,
    elevation_m=0.0,
):
    """Convective film coefficient ``h`` [W/(m^2*K)] per IEEE Std 738.

    Combines forced and natural convection and returns the larger, expressed as
    a film coefficient suitable for a Robin boundary condition
    ``q_conv = h * (T_surface - T_ambient)``.

    The IEEE 738 standard gives the convective heat *loss per unit length*
    ``q_c`` [W/m]. For a cylinder ``q_c = h * pi * D * (Ts - Ta)``, hence
    ``h = q_c / (pi * D * dT)``. The ``dT`` cancels analytically so ``h`` stays
    finite as ``Ts -> Ta``.
    """
    t_surface_c = np.asarray(t_surface_c, dtype=float)
    t_ambient_c = np.asarray(t_ambient_c, dtype=float)
    wind_speed = np.asarray(wind_speed, dtype=float)

    t_film = 0.5 * (t_surface_c + t_ambient_c)
    k_f, mu_f, rho_f = _air_properties(t_film, elevation_m)

    # Reynolds number based on conductor diameter
    n_re = diameter * rho_f * wind_speed / mu_f

    # Wind-direction factor (Phi = angle between wind and conductor axis)
    phi = np.deg2rad(wind_angle_deg)
    k_angle = 1.194 - np.cos(phi) + 0.194 * np.cos(2 * phi) + 0.368 * np.sin(2 * phi)

    # Forced convection: IEEE 738 uses the larger of the two empirical fits.
    # q_c = K_angle * f(Re) * k_f * dT, and h = q_c / (pi * D * dT).
    f_low = 1.01 + 1.35 * np.power(n_re, 0.52)
    f_high = 0.754 * np.power(n_re, 0.6)
    f_forced = np.maximum(f_low, f_high)
    h_forced = k_angle * f_forced * k_f / (np.pi * diameter)

    # Natural convection: q_cn = 3.645 * rho_f^0.5 * D^0.75 * dT^1.25 [W/m].
    # As a film coefficient: h_nat = q_cn / (pi * D * dT)
    #   = 3.645 * rho_f^0.5 * D^-0.25 * dT^0.25 / pi.
    dt = np.maximum(t_surface_c - t_ambient_c, 0.0)
    h_nat = 3.645 * np.sqrt(rho_f) * np.power(diameter, -0.25) * np.power(dt, 0.25) / np.pi

    return np.maximum(h_forced, h_nat)
