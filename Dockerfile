# FEniCSx runtime for the inthermo conductor thermal model.
#
# The official dolfinx image bundles dolfinx, gmsh, petsc4py, mpi4py and
# pyvista -- everything the mesh + solver layers need. Build and run:
#
#   docker build -t inthermo .
#   docker run --rm -v "${PWD}:/work" -w /work inthermo \
#       python examples/run_simulation.py
#
# Or run the upstream image directly without building (installs the package
# into the container on each run):
#
#   docker run --rm -v "${PWD}:/work" -w /work dolfinx/dolfinx:stable \
#       bash -c "pip install -e . && python examples/run_simulation.py"
FROM dolfinx/dolfinx:stable

WORKDIR /work
COPY . /work
RUN pip install --no-cache-dir -e .

CMD ["python", "examples/run_simulation.py"]
