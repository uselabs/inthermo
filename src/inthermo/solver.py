"""Transient 2D heat-equation solver for the ACSR conductor (FEniCSx).

Solves

    rho*cp * dT/dt - div(k grad T) = q(t)

on the two-material cross-section, with a Robin (convective) + Neumann (solar)
condition on the outer boundary:

    -k dT/dn = h(t) (T - T_amb(t)) - q_solar(t)

Material coefficients ``k`` and ``rho*cp`` are piecewise-constant DG-0 fields
keyed off the mesh cell tags. The Joule source is applied only in the aluminum
subdomain. Time integration is backward Euler; each step is a linear solve.

Requires ``dolfinx``, ``ufl``, ``petsc4py`` (see README for the Docker image).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from . import forcing
from .mesh import ALUMINUM_TAG, OUTER_BOUNDARY_TAG, STEEL_TAG, ConductorMesh
from .parameters import ConductorConfig


@dataclass
class SimulationInputs:
    """Aligned time-series inputs driving the transient solve (see gemini_info.md).

    All arrays must share the same length as ``time``.
    """

    time: np.ndarray  # [s]
    ambient_temperature: np.ndarray  # T_amb [degC]
    wind_speed: np.ndarray  # v_wind [m/s]
    solar_radiation: np.ndarray  # Q_solar [W/m^2]
    current: np.ndarray  # I [A]
    wind_angle_deg: float = 90.0  # angle between wind and conductor axis
    elevation_m: float = 0.0

    def __post_init__(self):
        n = len(self.time)
        for name in (
            "ambient_temperature",
            "wind_speed",
            "solar_radiation",
            "current",
        ):
            arr = np.asarray(getattr(self, name), dtype=float)
            if len(arr) != n:
                raise ValueError(
                    f"'{name}' has length {len(arr)}, expected {n} to match 'time'"
                )
            setattr(self, name, arr)
        self.time = np.asarray(self.time, dtype=float)


@dataclass
class SimulationResult:
    """Diagnostics collected over the transient solve."""

    time: np.ndarray
    max_temperature: np.ndarray  # max over the domain at each step [degC]
    surface_temperature: np.ndarray  # mean outer-surface temperature [degC]
    core_temperature: np.ndarray  # centre temperature [degC]
    convection_coefficient: np.ndarray  # h used at each step [W/(m^2 K)]


@dataclass
class ConductorThermalSolver:
    """Assemble and run the transient conductor heat model."""

    conductor_mesh: ConductorMesh
    config: ConductorConfig = field(default_factory=ConductorConfig)
    initial_temperature: float = 20.0  # [degC]

    def solve(self, inputs: SimulationInputs, xdmf_path: str | None = None) -> SimulationResult:
        import ufl
        from dolfinx import fem, geometry
        from dolfinx.fem.petsc import LinearProblem
        from petsc4py import PETSc

        msh = self.conductor_mesh.mesh
        cell_tags = self.conductor_mesh.cell_tags
        facet_tags = self.conductor_mesh.facet_tags

        geom = self.config.geometry
        alu = self.config.aluminum
        steel = self.config.steel

        # --- Function spaces -------------------------------------------------
        V = fem.functionspace(msh, ("Lagrange", 1))
        Q = fem.functionspace(msh, ("DG", 0))  # piecewise-constant coefficients

        # --- Piecewise-constant material fields (keyed by cell tag) ----------
        k_field = fem.Function(Q, name="k")
        rhocp_field = fem.Function(Q, name="rho_cp")
        alu_indicator = fem.Function(Q, name="aluminum_indicator")

        alu_cells = cell_tags.find(ALUMINUM_TAG)
        steel_cells = cell_tags.find(STEEL_TAG)

        k_field.x.array[alu_cells] = alu.k
        k_field.x.array[steel_cells] = steel.k
        rhocp_field.x.array[alu_cells] = alu.rho_cp
        rhocp_field.x.array[steel_cells] = steel.rho_cp
        alu_indicator.x.array[alu_cells] = 1.0
        alu_indicator.x.array[steel_cells] = 0.0

        # --- Solution functions ---------------------------------------------
        T = fem.Function(V, name="temperature")
        T_n = fem.Function(V, name="temperature_prev")
        T.x.array[:] = self.initial_temperature
        T_n.x.array[:] = self.initial_temperature

        # --- Time-varying coefficients (updated each step) -------------------
        dt = fem.Constant(msh, PETSc.ScalarType(1.0))
        h_conv = fem.Constant(msh, PETSc.ScalarType(0.0))
        t_amb = fem.Constant(msh, PETSc.ScalarType(self.initial_temperature))
        q_solar = fem.Constant(msh, PETSc.ScalarType(0.0))
        q_joule = fem.Constant(msh, PETSc.ScalarType(0.0))

        # --- Variational form (backward Euler) -------------------------------
        u = ufl.TrialFunction(V)
        v = ufl.TestFunction(V)
        # Material variation is carried by the DG-0 coefficient fields, so the
        # volume integrals use the default measure; only the boundary term needs
        # the tagged facet measure.
        ds = ufl.Measure("ds", domain=msh, subdomain_data=facet_tags)
        ds_out = ds(OUTER_BOUNDARY_TAG)

        # rho*cp/dt * u v + k grad u . grad v + h u v|_out
        a = (
            rhocp_field / dt * u * v * ufl.dx
            + k_field * ufl.dot(ufl.grad(u), ufl.grad(v)) * ufl.dx
            + h_conv * u * v * ds_out
        )
        # rho*cp/dt * T_n v + q_joule (alu) v + (h T_amb + q_solar) v|_out
        L = (
            rhocp_field / dt * T_n * v * ufl.dx
            + q_joule * alu_indicator * v * ufl.dx
            + (h_conv * t_amb + q_solar) * v * ds_out
        )

        # dolfinx >= 0.10 requires an explicit PETSc options prefix.
        problem = LinearProblem(
            a,
            L,
            u=T,
            petsc_options_prefix="inthermo_",
            petsc_options={"ksp_type": "preonly", "pc_type": "lu"},
        )

        # --- Evaluation helpers for diagnostics ------------------------------
        bb_tree = geometry.bb_tree(msh, msh.topology.dim)
        center_pt = np.array([[0.0, 0.0, 0.0]])
        surface_pt = np.array([[geom.r_outer, 0.0, 0.0]])

        def point_value(point):
            cells = []
            cand = geometry.compute_collisions_points(bb_tree, point)
            coll = geometry.compute_colliding_cells(msh, cand, point)
            if len(coll.links(0)) > 0:
                cells.append(coll.links(0)[0])
            if not cells:
                return np.nan
            return float(T.eval(point, np.array(cells))[0])

        # --- Time loop -------------------------------------------------------
        n_steps = len(inputs.time)
        max_temp = np.zeros(n_steps)
        surf_temp = np.zeros(n_steps)
        core_temp = np.zeros(n_steps)
        h_history = np.zeros(n_steps)

        comm = msh.comm
        xdmf = None
        if xdmf_path is not None:
            from dolfinx.io import XDMFFile

            xdmf = XDMFFile(comm, xdmf_path, "w")
            xdmf.write_mesh(msh)

        # Record initial state
        max_temp[0] = comm.allreduce(T.x.array.max(), op=_MAX())
        surf_temp[0] = point_value(surface_pt)
        core_temp[0] = point_value(center_pt)
        h_history[0] = 0.0
        if xdmf is not None:
            xdmf.write_function(T, inputs.time[0])

        for i in range(1, n_steps):
            step_dt = float(inputs.time[i] - inputs.time[i - 1])
            dt.value = step_dt

            # Convection coefficient uses the previous surface temperature so the
            # per-step problem stays linear.
            t_surf_prev = surf_temp[i - 1]
            if not np.isfinite(t_surf_prev):
                t_surf_prev = float(inputs.ambient_temperature[i])
            h_val = float(
                forcing.ieee738_convection_coefficient(
                    t_surf_prev,
                    inputs.ambient_temperature[i],
                    inputs.wind_speed[i],
                    geom.d_outer,
                    wind_angle_deg=inputs.wind_angle_deg,
                    elevation_m=inputs.elevation_m,
                )
            )
            h_conv.value = h_val
            t_amb.value = float(inputs.ambient_temperature[i])
            q_solar.value = float(
                forcing.solar_surface_flux(
                    inputs.solar_radiation[i], self.config.radiative.solar_absorptivity
                )
            )
            q_joule.value = float(
                forcing.joule_volumetric_heat(
                    inputs.current[i],
                    self.config.electrical.r_ac_per_length,
                    geom.area_aluminum,
                )
            )

            problem.solve()
            T.x.scatter_forward()
            T_n.x.array[:] = T.x.array

            max_temp[i] = comm.allreduce(T.x.array.max(), op=_MAX())
            surf_temp[i] = point_value(surface_pt)
            core_temp[i] = point_value(center_pt)
            h_history[i] = h_val
            if xdmf is not None:
                xdmf.write_function(T, inputs.time[i])

        if xdmf is not None:
            xdmf.close()

        return SimulationResult(
            time=inputs.time.copy(),
            max_temperature=max_temp,
            surface_temperature=surf_temp,
            core_temperature=core_temp,
            convection_coefficient=h_history,
        )


def _MAX():
    """Return the MPI MAX op (imported lazily to keep the module import light)."""
    from mpi4py import MPI

    return MPI.MAX
