"""Physical parameters for the Condor ACSR conductor thermal model.

All values are taken from ``src/inthermo/gemini_info.md`` (Nexans "Condor"
datasheet, re-rated to 220 kV / 50 Hz). SI units throughout unless noted.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    """Macroscopic thermal properties of a solid subdomain."""

    name: str
    k: float  # thermal conductivity [W/(m*K)]
    rho: float  # density [kg/m^3]
    cp: float  # specific heat capacity [J/(kg*K)]

    @property
    def rho_cp(self) -> float:
        """Volumetric heat capacity [J/(m^3*K)]."""
        return self.rho * self.cp


# Aluminum 1350-H19 outer layer
ALUMINUM = Material(name="aluminum", k=205.0, rho=2700.0, cp=900.0)

# Galvanized steel core
STEEL = Material(name="steel", k=50.0, rho=7850.0, cp=480.0)


@dataclass(frozen=True)
class ConductorGeometry:
    """Cross-sectional geometry of the stranded conductor.

    The stranded bundle is modelled as two concentric solid circular domains:
    a steel core surrounded by an aluminum annulus.
    """

    d_outer: float = 0.02772  # total nominal diameter [m]
    d_steel: float = 0.00924  # steel core diameter [m]
    area_aluminum: float = 4.0233e-4  # aluminum cross-section [m^2]

    @property
    def r_outer(self) -> float:
        return self.d_outer / 2.0

    @property
    def r_steel(self) -> float:
        return self.d_steel / 2.0


@dataclass(frozen=True)
class ElectricalProperties:
    """Electrical parameters re-rated for 50 Hz operation."""

    # AC resistance at 50 Hz, 75 C, per unit length [ohm/m]
    r_ac_per_length: float = 8.5e-5
    grid_voltage: float = 220e3  # [V]
    frequency: float = 50.0  # [Hz]
    max_ampacity: float = 900.0  # [A]


@dataclass(frozen=True)
class RadiativeProperties:
    """Surface optical properties for the radiation/solar balance."""

    solar_absorptivity: float = 0.5  # alpha, aluminum surface


# Convenient bundle of the default Condor configuration.
@dataclass(frozen=True)
class ConductorConfig:
    geometry: ConductorGeometry = ConductorGeometry()
    aluminum: Material = ALUMINUM
    steel: Material = STEEL
    electrical: ElectricalProperties = ElectricalProperties()
    radiative: RadiativeProperties = RadiativeProperties()


CONDOR = ConductorConfig()
