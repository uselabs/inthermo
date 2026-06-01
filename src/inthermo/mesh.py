"""Mesh generation for the two-subdomain conductor cross-section.

Builds a 2D mesh of the conductor: a steel-core disk embedded in an aluminum
annulus, using ``gmsh``, then converts it to a ``dolfinx`` mesh with cell tags
(per material) and facet tags (outer boundary).

This module imports ``gmsh`` and ``dolfinx``; it only runs inside an
environment where FEniCSx is available (see the project README for the Docker
image). ``forcing.py`` and ``parameters.py`` have no such dependency.

Tag conventions (exported as module constants):

* ``ALUMINUM_TAG`` -- cell tag for the aluminum annulus
* ``STEEL_TAG``    -- cell tag for the steel core
* ``OUTER_BOUNDARY_TAG`` -- facet tag for the convective/solar outer surface
"""

from __future__ import annotations

from dataclasses import dataclass

from .parameters import ConductorGeometry

ALUMINUM_TAG = 1
STEEL_TAG = 2
OUTER_BOUNDARY_TAG = 10


@dataclass
class ConductorMesh:
    """Container for the generated mesh and its tags."""

    mesh: "object"  # dolfinx.mesh.Mesh
    cell_tags: "object"  # dolfinx.mesh.MeshTags (dim = 2)
    facet_tags: "object"  # dolfinx.mesh.MeshTags (dim = 1)


def generate_conductor_mesh(
    geometry: ConductorGeometry | None = None,
    mesh_size: float | None = None,
    core_mesh_size: float | None = None,
    comm=None,
    rank: int = 0,
) -> ConductorMesh:
    """Generate the two-material conductor mesh.

    Parameters
    ----------
    geometry:
        Conductor geometry; defaults to the Condor configuration.
    mesh_size:
        Target element size in the aluminum [m]. Defaults to ``r_outer / 12``.
    core_mesh_size:
        Target element size in the steel core [m]. Defaults to ``mesh_size``.
    comm:
        MPI communicator; defaults to ``MPI.COMM_WORLD``.
    rank:
        Rank that owns the gmsh model (mesh is built on this rank then
        distributed).
    """
    import gmsh
    from mpi4py import MPI

    # dolfinx >= 0.10 exposes the gmsh interface as ``dolfinx.io.gmsh``;
    # earlier versions name it ``dolfinx.io.gmshio``.
    try:
        from dolfinx.io import gmshio
    except ImportError:
        from dolfinx.io import gmsh as gmshio

    if comm is None:
        comm = MPI.COMM_WORLD
    if geometry is None:
        geometry = ConductorGeometry()
    if mesh_size is None:
        mesh_size = geometry.r_outer / 12.0
    if core_mesh_size is None:
        core_mesh_size = mesh_size

    gmsh.initialize()
    try:
        gmsh.model.add("conductor")

        if comm.rank == rank:
            occ = gmsh.model.occ
            # Two concentric disks; the core is cut/fragmented out of the outer
            # disk so the annulus and core share a conformal interface.
            outer = occ.addDisk(0, 0, 0, geometry.r_outer, geometry.r_outer)
            core = occ.addDisk(0, 0, 0, geometry.r_steel, geometry.r_steel)
            # Fragment keeps both surfaces and makes the shared edge conformal.
            frag, _ = occ.fragment([(2, outer)], [(2, core)])
            occ.synchronize()

            # Identify the resulting surfaces by their centre of mass distance
            # / area: the steel core is the smaller-radius disk.
            alu_surfaces = []
            steel_surfaces = []
            for dim, tag in gmsh.model.getEntities(2):
                # area of a disk = pi r^2; the core area is pi r_steel^2
                mass = occ.getMass(dim, tag)
                core_area = 3.141592653589793 * geometry.r_steel**2
                if abs(mass - core_area) / core_area < 0.05:
                    steel_surfaces.append(tag)
                else:
                    alu_surfaces.append(tag)

            gmsh.model.addPhysicalGroup(2, alu_surfaces, ALUMINUM_TAG)
            gmsh.model.setPhysicalName(2, ALUMINUM_TAG, "aluminum")
            gmsh.model.addPhysicalGroup(2, steel_surfaces, STEEL_TAG)
            gmsh.model.setPhysicalName(2, STEEL_TAG, "steel")

            # Outer boundary: the exterior of the union of both surfaces. Taking
            # the *combined* boundary cancels the shared core/annulus interface
            # edge and leaves only the true outer circle. (A centre-of-mass test
            # fails here because a full circle's centroid is at the origin.)
            all_surfaces = [(2, t) for t in alu_surfaces + steel_surfaces]
            exterior = gmsh.model.getBoundary(all_surfaces, combined=True, oriented=False)
            outer_edges = [tag for (dim, tag) in exterior]
            gmsh.model.addPhysicalGroup(1, outer_edges, OUTER_BOUNDARY_TAG)
            gmsh.model.setPhysicalName(1, OUTER_BOUNDARY_TAG, "outer")

            # Element sizing
            gmsh.option.setNumber("Mesh.MeshSizeMin", core_mesh_size)
            gmsh.option.setNumber("Mesh.MeshSizeMax", mesh_size)
            gmsh.model.mesh.generate(2)

        result = gmshio.model_to_mesh(gmsh.model, comm, rank, gdim=2)
    finally:
        gmsh.finalize()

    # dolfinx >= 0.9 returns a MeshData object; earlier versions return a
    # (mesh, cell_tags, facet_tags) tuple. Support both.
    if hasattr(result, "mesh"):
        mesh = result.mesh
        cell_tags = result.cell_tags
        facet_tags = result.facet_tags
    else:
        mesh, cell_tags, facet_tags = result

    return ConductorMesh(mesh=mesh, cell_tags=cell_tags, facet_tags=facet_tags)
