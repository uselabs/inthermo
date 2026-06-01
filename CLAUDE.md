# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project status

`inthermo` implements a transient 2-D FEniCSx thermal model of the Condor ACSR
conductor. The physical spec lives in `src/inthermo/gemini_info.md` — read it
before changing the physics. Real weather-station inputs (solar `G`, ambient
`Tamb`, wind `v_w`/`ang_w`) are in `src/inthermo/WS_measurements.json` (43,840
records, ~16 s sampling, contains NaN gaps; no current `I(t)` column).

## Module split — dolfinx vs. pure NumPy (important)

The package is deliberately layered so it imports without FEniCSx installed:

- `parameters.py`, `forcing.py` — **pure NumPy**, no dolfinx. Import and test
  these natively on Windows.
- `mesh.py`, `solver.py` — **require dolfinx/gmsh/petsc4py**. They are NOT
  imported at package top level; reach them via `inthermo.load_fenics_api()`,
  which returns `generate_conductor_mesh`, `ConductorThermalSolver`,
  `SimulationInputs`, `SimulationResult`. Keep this lazy boundary intact so
  `import inthermo` keeps working in the dolfinx-free Windows env.

## Build & test

hatchling build backend; pytest with `pythonpath = ["src"]` (no install needed
to import the package). The NumPy test suite runs natively on Windows:

```powershell
pip install -e ".[test]"
pytest                                   # all tests (testpaths = tests/)
pytest tests/test_forcing.py::test_solar_flux_is_diameter_independent
```

## Running the FEniCSx solver

FEniCSx has no native Windows build. The validated environment is **WSL Ubuntu
24.04 + Miniforge** (no Docker), with dolfinx **0.10** in a conda env named
`fenicsx`. Setup script: `scripts/setup_wsl_dolfinx.sh`. Run the example:

```powershell
wsl -d Ubuntu-24.04 -u root --cd "<repo path>" -- bash -lc `
  "source /opt/miniforge3/etc/profile.d/conda.sh && conda activate fenicsx && python examples/run_simulation.py"
```

`Dockerfile` (image `dolfinx/dolfinx:stable`) is the alternative path.

### dolfinx 0.10 API gotchas (already handled — keep in mind when editing)

- gmsh interface moved: `dolfinx.io.gmsh` in 0.10, `dolfinx.io.gmshio` before.
  `mesh.py` imports with a try/except fallback.
- `model_to_mesh` returns a `MeshData` object (`.mesh`/`.cell_tags`/
  `.facet_tags`), not a tuple. `mesh.py` handles both.
- `fem.petsc.LinearProblem` requires the `petsc_options_prefix` kwarg in 0.10.
- Outer-boundary detection uses `getBoundary(..., combined=True)` (NOT a
  centre-of-mass radius test — a full circle's centroid is at the origin).

## Physics the code implements (from gemini_info.md)

A **2D transient heat-equation model of the Condor ACSR conductor** (220 kV /
50 Hz). Key modeling facts a contributor must respect:

- **Two solid subdomains**: an aluminum layer (k=205, ρ=2700, Cp=900) surrounding a galvanized steel core (k=50, ρ=7850, Cp=480). `solver.py` maps these as DG-0 fields keyed off the mesh cell tags.
- **Heat generation is Joule heating in the aluminum only** — `q_alu = I(t)²·R_AC / A_alu` (volumetric); the steel core generates no heat (no current).
- **Outer boundary condition** balances convection loss against solar gain: `-k·∂T/∂n = q_conv(t) − q_solar(t)`, implemented as a Robin term (`h·(T−T_amb)`) plus a Neumann solar inflow. `h` comes from `forcing.ieee738_convection_coefficient` and is recomputed each step from wind + previous surface temperature (keeps each step linear).
- Note: the datasheet's `q_solar = αQ/(πD)` is dimensionally W/m³; `forcing.solar_surface_flux` uses the consistent surface flux `αQ/π` (see its docstring).
- **Time-loop inputs** are five aligned arrays (`SimulationInputs`): time, `T_amb`, wind speed, solar flux, current. Sanity result: small high-conductivity conductor → core and surface temperatures track within ~0.02 °C.

`docs/condor_datasheet.pdf` is the source datasheet behind the numeric parameters in `gemini_info.md`.

## Notes

- `pyproject.toml` lists `Juan Manuel Mauricio` as author; the git committer is `arnozal`. Requires Python ≥ 3.9.
- FEniCSx is intentionally NOT a declared dependency in `pyproject.toml` (not pip-installable on most platforms); it is provided by the conda/Docker runtime. Only `numpy` (runtime) and `pytest` (test extra) are declared.
