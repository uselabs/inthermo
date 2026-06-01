# Installation & running

`inthermo` splits into a pure-NumPy layer and a FEniCSx layer. The NumPy layer
installs and runs anywhere; the FEniCSx solver runs on Linux.

## NumPy layer (native, any platform)

```powershell
pip install -e ".[test]"
pytest
```

This is enough to use {py:mod}`inthermo.parameters` and
{py:mod}`inthermo.forcing`, and to run the test suite.

## FEniCSx solver

FEniCSx has **no native Windows build** (no pip wheels, no Windows conda
packages), so the mesh + solver run on Linux. Two supported paths:

### Option A — WSL + Miniforge (no Docker)

This is the validated path (dolfinx 0.10).

```powershell
# One-time: install a Linux distro and the dolfinx stack
wsl --install -d Ubuntu-24.04 --no-launch
wsl -d Ubuntu-24.04 -u root -- bash "/mnt/c/.../inthermo/scripts/setup_wsl_dolfinx.sh"

# Run the example
wsl -d Ubuntu-24.04 -u root --cd "C:\...\inthermo" -- bash -lc `
  "source /opt/miniforge3/etc/profile.d/conda.sh && conda activate fenicsx && `
   pip install -e . && python examples/run_simulation.py"
```

The setup script (`scripts/setup_wsl_dolfinx.sh`) installs Miniforge and a
conda env named `fenicsx` containing `fenics-dolfinx`, `gmsh`, `pyvista`,
`numpy`, `scipy` and `pytest`.

### Option B — Docker

```powershell
docker run --rm -v "${PWD}:/work" -w /work dolfinx/dolfinx:stable `
    bash -c "pip install -e . && python examples/run_simulation.py"
```

A `Dockerfile` based on `dolfinx/dolfinx:stable` is included.

## Building these docs

```powershell
pip install -e ".[docs]"
cd docs
.\make.bat html        # Linux/macOS: make html
```

The rendered site is written to `docs/_build/html/index.html`.
