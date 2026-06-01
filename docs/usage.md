# Usage

## Pure-NumPy physics layer

{py:mod}`inthermo.parameters` and {py:mod}`inthermo.forcing` need only NumPy:

```python
from inthermo import CONDOR, forcing

g, e, r = CONDOR.geometry, CONDOR.electrical, CONDOR.radiative

# Volumetric Joule heat in the aluminum at 900 A [W/m^3]
q = forcing.joule_volumetric_heat(900.0, e.r_ac_per_length, g.area_aluminum)

# IEEE 738 convective film coefficient at 2 m/s wind [W/(m^2 K)]
h = forcing.ieee738_convection_coefficient(
    t_surface_c=75.0, t_ambient_c=40.0, wind_speed=2.0, diameter=g.d_outer
)

# Absorbed solar surface flux at 1000 W/m^2 incident [W/m^2]
qs = forcing.solar_surface_flux(1000.0, r.solar_absorptivity)
```

All forcing functions broadcast over NumPy arrays, so a whole time series can
be evaluated at once.

## Running a transient simulation

The mesh and solver require FEniCSx (see {doc}`installation`). They are loaded
lazily through {py:func}`inthermo.load_fenics_api` so that `import inthermo`
still works without dolfinx:

```python
import numpy as np
from inthermo import CONDOR, load_fenics_api

api = load_fenics_api()

# 1. Build the two-subdomain mesh
mesh = api["generate_conductor_mesh"](CONDOR.geometry)

# 2. Assemble aligned input time series
t = np.arange(0, 3600, 60.0)            # 1 hour at 60 s steps
inputs = api["SimulationInputs"](
    time=t,
    ambient_temperature=np.full_like(t, 25.0),
    wind_speed=np.full_like(t, 2.0),
    solar_radiation=np.full_like(t, 800.0),
    current=np.full_like(t, 900.0),
)

# 3. Solve
solver = api["ConductorThermalSolver"](
    conductor_mesh=mesh, config=CONDOR, initial_temperature=25.0
)
result = solver.solve(inputs, xdmf_path="conductor_temperature.xdmf")

print(result.max_temperature[-1])       # peak temperature at the final step
```

The returned {py:class}`inthermo.solver.SimulationResult` carries per-step
arrays for the maximum, surface and core temperatures and the convection
coefficient used. Passing `xdmf_path` also writes a field file for
[ParaView](https://www.paraview.org/).

## Worked example

`examples/run_simulation.py` runs a synthetic 24-hour profile (diurnal ambient
temperature, gusty wind, a solar bell curve and a daytime current ramp) and
prints the peak conductor temperature. Run it inside the FEniCSx environment as
shown in {doc}`installation`.
