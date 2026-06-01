#!/usr/bin/env bash
# Set up a FEniCSx (dolfinx) environment inside a WSL Ubuntu distro WITHOUT
# Docker. Installs Miniforge (conda) and the conda-forge dolfinx stack.
#
# Run as root inside the distro, e.g. from Windows PowerShell:
#   wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/.../inthermo/scripts/setup_wsl_dolfinx.sh
#
# Idempotent-ish: skips Miniforge download if already present.
set -euo pipefail

MINIFORGE_DIR=/opt/miniforge3
ENV_NAME=fenicsx

echo ">> Installing base packages (wget, bzip2, ca-certificates)..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq wget bzip2 ca-certificates >/dev/null

if [ ! -d "$MINIFORGE_DIR" ]; then
  echo ">> Downloading Miniforge..."
  wget -q "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh" -O /tmp/miniforge.sh
  echo ">> Installing Miniforge to $MINIFORGE_DIR..."
  bash /tmp/miniforge.sh -b -p "$MINIFORGE_DIR"
  rm -f /tmp/miniforge.sh
else
  echo ">> Miniforge already present at $MINIFORGE_DIR, skipping."
fi

source "$MINIFORGE_DIR/etc/profile.d/conda.sh"

echo ">> Creating '$ENV_NAME' env with dolfinx + gmsh + pyvista..."
conda create -y -n "$ENV_NAME" -c conda-forge \
  python=3.12 fenics-dolfinx mpich gmsh python-gmsh pyvista numpy scipy pytest

echo ">> dolfinx version check:"
conda run -n "$ENV_NAME" python -c "import dolfinx, gmsh; print('dolfinx', dolfinx.__version__)"

echo ">> Done. Activate with:  source $MINIFORGE_DIR/etc/profile.d/conda.sh && conda activate $ENV_NAME"
