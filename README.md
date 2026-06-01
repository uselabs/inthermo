# inthermo

Transient 2-D thermal model of an ACSR overhead-line conductor (Nexans
"Condor", 220 kV / 50 Hz), solved with [FEniCSx](https://fenicsproject.org/).

The conductor cross-section is modelled as two concentric solid domains — a
galvanized **steel core** inside an **aluminum annulus** — governed by the
transient heat equation

```
rho*cp dT/dt - div(k grad T) = q(t)
```

with Joule heating in the aluminum, and a combined convective + solar boundary
condition on the outer surface. See `src/inthermo/gemini_info.md` for the full
physical specification and the datasheet parameters.

## Package layout

| Module | Depends on dolfinx? | Purpose |
| --- | --- | --- |
| `parameters.py` | no | Condor geometry, material & electrical properties (dataclasses) |
| `forcing.py` | no | IEEE 738 convection coefficient, solar flux, Joule heat (pure NumPy) |
| `mesh.py` | yes (gmsh) | Two-subdomain mesh with material cell tags + outer-boundary facet tag |
| `solver.py` | yes | Backward-Euler transient solver, Robin/Neumann boundary, diagnostics |

`parameters` and `forcing` import with plain NumPy, so they can be used and
unit-tested anywhere. The FEniCSx entry points are loaded lazily via
`inthermo.load_fenics_api()` so `import inthermo` works without dolfinx.

## Running the model

FEniCSx has no native Windows build (no pip wheels, no Windows conda
packages), so the solver runs on Linux. Two supported options:

### Option A — WSL + Miniforge (no Docker)

```powershell
# One-time: install a real Linux distro and the dolfinx stack
wsl --install -d Ubuntu-24.04 --no-launch
wsl -d Ubuntu-24.04 -u root -- bash "/mnt/c/.../inthermo/scripts/setup_wsl_dolfinx.sh"

# Run the example (validated with dolfinx 0.10)
wsl -d Ubuntu-24.04 -u root --cd "C:\...\inthermo" -- bash -lc `
  "source /opt/miniforge3/etc/profile.d/conda.sh && conda activate fenicsx && `
   pip install -e . && python examples/run_simulation.py"
```

### Option B — Docker

```powershell
docker run --rm -v "${PWD}:/work" -w /work dolfinx/dolfinx:stable `
    bash -c "pip install -e . && python examples/run_simulation.py"
```

Either way, `examples/run_simulation.py` runs a synthetic 24-hour profile and
writes `conductor_temperature.xdmf` (open in [ParaView](https://www.paraview.org/)).

## Tests

The pure-NumPy physics layer is tested without dolfinx and runs natively:

```powershell
pip install -e ".[test]"
pytest
```
