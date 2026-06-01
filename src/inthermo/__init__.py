"""inthermo -- transient thermal CFD model of an ACSR power-line conductor."""

__version__ = "0.0.1"

# Lightweight, dependency-free modules are always importable.
from . import forcing, parameters
from .parameters import (
    ALUMINUM,
    CONDOR,
    STEEL,
    ConductorConfig,
    ConductorGeometry,
    ElectricalProperties,
    Material,
    RadiativeProperties,
)

__all__ = [
    "__version__",
    "forcing",
    "parameters",
    "Material",
    "ConductorGeometry",
    "ElectricalProperties",
    "RadiativeProperties",
    "ConductorConfig",
    "ALUMINUM",
    "STEEL",
    "CONDOR",
    # FEniCSx-dependent entry points (importable via inthermo.mesh / .solver
    # only where dolfinx is installed):
    "load_fenics_api",
]


def load_fenics_api():
    """Import and return the FEniCSx-dependent symbols.

    Kept out of the top-level import so ``import inthermo`` works in
    environments without dolfinx (e.g. for using :mod:`inthermo.forcing`).
    Returns a dict with the mesh + solver entry points.
    """
    from .mesh import ConductorMesh, generate_conductor_mesh
    from .solver import (
        ConductorThermalSolver,
        SimulationInputs,
        SimulationResult,
    )

    return {
        "generate_conductor_mesh": generate_conductor_mesh,
        "ConductorMesh": ConductorMesh,
        "ConductorThermalSolver": ConductorThermalSolver,
        "SimulationInputs": SimulationInputs,
        "SimulationResult": SimulationResult,
    }
