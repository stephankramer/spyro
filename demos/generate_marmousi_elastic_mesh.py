from SeismicMesh.sizing.mesh_size_function import write_velocity_model
from mpi4py import MPI
import meshio

import sys

from SeismicMesh import get_sizing_function_from_segy, generate_mesh, Rectangle

comm = MPI.COMM_WORLD

"""
Build a mesh of the Marmousi elastic benchmark velocity model in serial or parallel
Takes roughly 1 minute with 2 processors and less than 1 GB of RAM.
"""

# Name of SEG-Y file containg velocity model (S-wave speed)
fname = "./velocity_models/elastic-marmousi-model/model/MODEL_S-WAVE_VELOCITY_1.25m.segy"   # in m/s
#fname = "./velocity_models/elastic-marmousi-model/model/MODEL_P-WAVE_VELOCITY_1.25m.segy"  # in m/s
#fname = "./velocity_models/elastic-marmousi-model/model/MODEL_DENSITY_1.25m.segy"          # in g/cm3

# Bounding box describing domain extents (corner coordinates)
bbox = (-3500.0, 0.0, 0.0, 17000.0) # this includes a 450-m thick water layer
#bbox = (-3500.0, -450.0, 0.0, 17000.0) # removing water layer

rectangle = Rectangle(bbox)

write_vel_mod=0
if write_vel_mod==1:
    write_velocity_model(fname)
    sys.exit("Mesh not generated") 

# Construct mesh sizing object from velocity model
mesh_adapted=1
if mesh_adapted==1:
    # with or without pad
    hmin = 25.0
    # FIXME forcing units=m/s because of a "np.amin(vp) < 1000.0" assumption in SeismicMesh 
    ef = get_sizing_function_from_segy(
        fname,
        bbox=bbox,
        hmin=hmin,          # minimum edge length in the domain 
        units="m-s",        # the units of the seismic velocity model (forcing m/s because of a <1000 assumption) FIXME 
        wl=5,               # number of cells per wavelength for a given f_max
        freq=5,             # f_max in hertz for which to estimate wl
        dt=0.001,           # theoretical maximum stable timestep in seconds given Courant number Cr
        grade=0.15,         # maximum allowable variation in mesh size in decimal percent
        domain_pad=0.,      # the width of the domain pad in -z, +x, -x, +y, -y directions
        pad_style="edge",   # the method (`edge`, `linear_ramp`, `constant`) to pad velocity in the domain pad region
    )
else:
    # no pad
    hmin = 50.0
    ef = get_sizing_function_from_segy(
        fname,
        bbox,
        hmin=hmin,
        wl=10,
        freq=4,
        dt=0.001,
        grade=0.15
    )

points, cells = generate_mesh(domain=rectangle, edge_length=ef)

if comm.rank == 0:
    # Write the mesh in a vtk format for visualization in ParaView
    # NOTE: SeismicMesh outputs assumes the domain is (z,x) so for visualization
    # in ParaView, we swap the axes so it appears as in the (x,z) plane.
    meshio.write_points_cells(
        "meshes/marmousi_elastic_with_water_layer_adapted.msh",
        points[:] / 1000, # do not swap here
        [("triangle", cells)],
        file_format="gmsh22",
        binary=False
    )
    meshio.write_points_cells(
        "meshes/marmousi_elastic_with_water_layer_adapted.vtk",
        points[:, [1, 0]] / 1000,
        [("triangle", cells)],
        file_format="vtk",
        binary=False
    )

