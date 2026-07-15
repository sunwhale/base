# -*- coding: utf-8 -*-
"""

"""
import os
import sys
from copy import deepcopy
from token import LEFTSHIFT

import numpy as np

try:
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    from pprint import pprint
except ImportError as e:
    print(e)

try:
    from abaqus import *
    from abaqusConstants import *
    from caeModules import *
    from caeModules import abaqus, assembly, connector, connectorBehavior, dgm, dgo, interaction, job, load, material, mesh, optimization, part, regionToolset, \
        section, sketch, step, visualization, xyPlot
    from driverUtils import executeOnCaeStartup
    import regionToolset
except ImportError as e:
    print(e)

# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    FLOW_PATH = r'F:\Github\base\base\utils\flow'
else:
    FLOW_PATH = r'/home/dell/base/base/utils/flow'

try:
    if os.path.isfile(sys.argv[3]):
        FLOW_PATH = os.path.dirname(sys.argv[3])
except:
    pass

sys.path.insert(0, FLOW_PATH)

import importlib
import utils

# 兼容 Python 2 和 3
if sys.version_info[0] == 2:
    reload(utils)
else:
    importlib.reload(utils)

from utils import ABAQUS_ENV, Circle3D, Counter, Cylinder, Ellipse, Line2D, Plane, add_spline, calc_arc, combine_surfaces, create_contact_of_instance_surface, create_face_set_from_surface, create_surface_by_intersection, create_surface_on_cylinder, \
    create_surface_on_plane, create_tie_of_instance_surface, degrees_to_radians, find_duplicates, generate_part_mesh, geometries, geometries_circle, geometries_hex, get_block_types, get_cells_adjacent_to_set_and_remove_set_names, get_cells_by_remove, \
    get_common_faces_between_sets, get_direction, get_faces_of_p_remove_given_surface_names, get_same_area_faces, get_same_volume_cells, get_tie_types, get_z_list, ignore_common_edges_of_faces, insert_COH3D8_at_face_set, is_cell_in_set, is_face_in_set, \
    is_unicode_all_uppercase, json, line_circle_intersection, load_json, major_version, math, min_difference, mirror_y_axis, move_along_direction, part_partition_by_cylinder, plot_geometries, plot_geometries_hex, plot_three_arcs, polar_to_cartesian, \
    radians_to_degrees, rotate_point_around_axis, rotate_point_around_origin_2d, rotate_point_around_vector, set_material, set_obj, solve_three_arcs, string_types, text_type, vertices_in_cells, get_mirror_faces, get_cells_from_faces, get_edges_from_faces, \
    get_xy_plane_mirror_cells, get_xy_plane_mirror_faces

PEN = 1e5
TOL = 1e-6
PENULT_CORRECTION = 1.0


# s.setPrimaryObject(option=STANDALONE)
# p.DatumPointByCoordinate(coords=(0, 0, 0))
# execfile('/home/dell/base/base/utils/flow/submersible.py', __main__.__dict__)


def create_sketch_outer_shell(model, sketch_name, l, r, thickness_outer_shell):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = (0, 0)
    p1 = [0, r]
    p2 = [l, r]
    p3 = [l, r - thickness_outer_shell]
    p4 = [0, r - thickness_outer_shell]
    s.Line(point1=p1, point2=p2)
    s.Line(point1=p2, point2=p3)
    s.Line(point1=p3, point2=p4)
    s.Line(point1=p4, point2=p1)

    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    return s


def create_sketch_inner_shell(model, sketch_name, l, r, thickness_outer_shell, thickness_inner_shell):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = (0, 0)

    p1 = [0, r - thickness_outer_shell]
    p2 = [l, r - thickness_outer_shell]
    p3 = [l, r - thickness_outer_shell - thickness_inner_shell]
    p4 = [0, r - thickness_outer_shell - thickness_inner_shell]

    p5 = [-(r - thickness_outer_shell - thickness_inner_shell), 0]
    p6 = [-(r - thickness_outer_shell), 0]

    s.ArcByCenterEnds(center=center, point1=p1, point2=p6, direction=COUNTERCLOCKWISE)
    s.ArcByCenterEnds(center=center, point1=p4, point2=p5, direction=COUNTERCLOCKWISE)

    s.Line(point1=p1, point2=p2)
    s.Line(point1=p2, point2=p3)
    s.Line(point1=p3, point2=p4)
    s.Line(point1=p5, point2=p6)

    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    return s


def create_part_base_rotation(model, part_name, sketch, rotate_angle_deg):
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    d = p.datums

    p.BaseSolidRevolve(sketch=sketch, angle=rotate_angle_deg, flipRevolveDirection=OFF)

    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)

    return p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis


def create_part_outer_shell(model, part_name, s, rotate_angle_deg):
    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis = create_part_base_rotation(model, part_name, s, rotate_angle_deg)

    # 创建面
    create_surface_rotation_part_common(p, rotate_angle_deg)

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体）
    set_name = 'SET-CELL-OUTER-SHELL'
    p.Set(cells=p.cells, name=set_name)

    # 创建集合（边）
    p_edges = get_edges_from_faces(p, p.surfaces['SURFACE-R1'].faces)
    p_edges_x0 = p.edges.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for edge in p_edges:
        edge_id = edge.index
        if edge.pointOn[0][0] == 0.0:
            p_edges_x0 += p.edges[edge_id:edge_id + 1]
    p.Set(edges=p_edges_x0, name='SET-EDGE-X0')

    # 赋予SECTION属性
    normalAxisRegion = p.surfaces['SURFACE-R1']
    primaryAxisRegion = p.sets['SET-EDGE-X0']
    compositeLayup = p.CompositeLayup(name='COMPOSITELAYUP-1', description='', elementType=SOLID, symmetric=False, thicknessAssignment=FROM_SECTION)

    material_name = 'MATERIAL-SHELL-COMPOSITE'
    num_int_points = 3
    region = p.sets['SET-CELL-OUTER-SHELL']
    shell_composite_layup = np.genfromtxt('shell_composite_layup.csv', delimiter=',')
    for i, layup_data in enumerate(shell_composite_layup):
        ply_name = 'PLY-' + str(i)
        orientation = layup_data[0]
        thickness = layup_data[1]
        compositeLayup.CompositePly(suppressed=False, plyName=ply_name, region=region,
                                    material=material_name, thicknessType=SPECIFY_THICKNESS, thickness=thickness,
                                    orientationType=SPECIFY_ORIENT, orientationValue=orientation,
                                    additionalRotationType=ROTATION_NONE, additionalRotationField='',
                                    axis=AXIS_3, angle=0.0, numIntPoints=num_int_points)

    compositeLayup.ReferenceOrientation(orientationType=DISCRETE, localCsys=None,
                                        additionalRotationType=ROTATION_NONE, angle=0.0,
                                        additionalRotationField='', axis=AXIS_3, stackDirection=STACK_3,
                                        normalAxisDefinition=SURFACE, normalAxisRegion=normalAxisRegion,
                                        normalAxisDirection=AXIS_3, flipNormalDirection=False,
                                        primaryAxisDefinition=EDGE, primaryAxisRegion=primaryAxisRegion,
                                        primaryAxisDirection=AXIS_2, flipPrimaryDirection=False)

    try:
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    except:
        pass

    # 生成网格
    generate_part_mesh(p, element_size=20.0)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_inner_shell(model, part_name, s, rotate_angle_deg, r, thickness_outer_shell):
    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis = create_part_base_rotation(model, part_name, s, rotate_angle_deg)

    # 创建面
    create_surface_rotation_part_common(p, rotate_angle_deg)

    point = [0, r - thickness_outer_shell, 0.0]
    point_rot = rotate_point_around_axis(point, [0, 0, 0], [1, 0, 0], 1.0)
    point_rot = rotate_point_around_axis(point_rot, [0, 0, 0], [0, 0, 1], 1.0)
    p.DatumPointByCoordinate(coords=point_rot)
    p_faces = p.faces.findAt((point_rot,))
    p.Surface(side1Faces=p_faces, name='SURFACE-FRONT-INNER')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体）
    set_name = 'SET-CELL-INNER-SHELL'
    p.Set(cells=p.cells, name=set_name)

    p.SectionAssignment(region=p.sets['SET-CELL-INNER-SHELL'], sectionName='SECTION-TI', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    try:
        p.PartitionCellByDatumPlane(datumPlane=d[yz_plane.id], cells=p.cells)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    except:
        pass

    # 生成网格
    generate_part_mesh(p, element_size=40.0)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_surface_rotation_part_common(p, rotate_angle_deg):
    if rotate_angle_deg < 360.0:
        p1 = (0.0, 0.0, 0.0)
        p2 = (1.0, 0.0, 0.0)
        p3 = (0.0, 1.0, 0.0)
        plane = Plane(p1, p2, p3)
        create_surface_on_plane(p, plane, 'SURFACE-T0')

        p1 = (0.0, 0.0, 0.0)
        p2 = (1.0, 0.0, 0.0)
        p3 = (0.0, 1.0, 0.0)
        p3_rot = rotate_point_around_axis(p3, (0, 0, 0), (1, 0, 0), rotate_angle_deg)
        plane = Plane(p1, p2, p3_rot)
        create_surface_on_plane(p, plane, 'SURFACE-T1')

    x_low = p.cells.getBoundingBox()['low'][0]
    x_high = p.cells.getBoundingBox()['high'][0]

    p1 = (x_low, 0.0, 0.0)
    p2 = (x_low, 1.0, 0.0)
    p3 = (x_low, 0.0, 1.0)
    plane = Plane(p1, p2, p3)
    create_surface_on_plane(p, plane, 'SURFACE-X0')

    p1 = (x_high, 0.0, 0.0)
    p2 = (x_high, 1.0, 0.0)
    p3 = (x_high, 0.0, 1.0)
    plane = Plane(p1, p2, p3)
    create_surface_on_plane(p, plane, 'SURFACE-X1')

    p_faces = p.faces.getByBoundingBox(x_low, 0.0, 0.0, x_high, PEN, TOL)
    r_low = p_faces.getBoundingBox()['low'][1]
    r_high = p_faces.getBoundingBox()['high'][1]

    cylinder = Cylinder((0, 0, 0), (1, 0, 0), r_low)
    create_surface_on_cylinder(p, cylinder, 'SURFACE-R0')

    cylinder = Cylinder((0, 0, 0), (1, 0, 0), r_high)
    create_surface_on_cylinder(p, cylinder, 'SURFACE-R1')


if __name__ == "__main__":
    l = 2500
    d = 1500
    r = d / 2.0
    thickness_outer_shell = 12.5
    thickness_inner_shell = 50.0
    rotate_angle_deg = 180.0

    if not ABAQUS_ENV:
        pass

    if ABAQUS_ENV:
        Mdb()
        model = mdb.models['Model-1']
        model.setValues(absoluteZero=-273.15)

        set_material(model.Material(name='MATERIAL-TI'), load_json('material_ti.json'))
        set_material(model.Material(name='MATERIAL-CZM'), load_json('material_czm.json'))
        set_material(model.Material(name='MATERIAL-SHELL-COMPOSITE'), load_json('material_shell_composite.json'))

        model.HomogeneousSolidSection(name='SECTION-TI', material='MATERIAL-TI', thickness=None)
        model.CohesiveSection(name='SECTION-CZM', material='MATERIAL-CZM', response=TRACTION_SEPARATION, outOfPlaneThickness=None)

        model.ContactProperty('IntProp-1')
        model.interactionProperties['IntProp-1'].TangentialBehavior(formulation=FRICTIONLESS)
        model.interactionProperties['IntProp-1'].CohesiveBehavior(defaultPenalties=OFF, table=((1000000.0, 1000000.0, 1000000.0),))
        model.interactionProperties['IntProp-1'].NormalBehavior(pressureOverclosure=HARD, allowSeparation=OFF, constraintEnforcementMethod=DEFAULT)

        s_outer_shell = create_sketch_outer_shell(model, 'SKETCH-OUTER-SHELL', l, r, thickness_outer_shell)
        s_inner_shell = create_sketch_inner_shell(model, 'SKETCH-INNER-SHELL', l, r, thickness_outer_shell, thickness_inner_shell)

        p_outer_shell = create_part_outer_shell(model, 'PART-OUTER-SHELL', s_outer_shell, rotate_angle_deg)
        p_inner_shell = create_part_inner_shell(model, 'PART-INNER-SHELL', s_inner_shell, rotate_angle_deg, r, thickness_outer_shell)

        model.StaticStep(name='Step-1', previous='Initial', nlgeom=OFF, timePeriod=1.0, maxNumInc=10000, initialInc=0.1, minInc=1e-06, maxInc=1.0)

        a = model.rootAssembly
        a.DatumCsysByDefault(CARTESIAN)
        cylindrical_datum = a.DatumCsysByThreePoints(name='Datum csys-2', coordSysType=CYLINDRICAL, origin=(0.0, 0.0, 0.0), point1=(0.0, 1.0, 0.0), point2=(0.0, 0.0, 1.0))

        a.Instance(name='INNER-SHELL', part=p_inner_shell, dependent=ON)
        a.Instance(name='OUTER-SHELL', part=p_outer_shell, dependent=ON)

        instance_name_1 = 'INNER-SHELL'
        surface_name_1 = 'SURFACE-R1'
        instance_name_2 = 'OUTER-SHELL'
        surface_name_2 = 'SURFACE-R0'
        create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

        instance_name = 'INNER-SHELL'
        set_name = 'SET-SURFACE-X1'
        bc_name = 'BC-' + instance_name + '-' + set_name
        model.ZsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

        instance_name = 'OUTER-SHELL'
        set_name = 'SET-SURFACE-X1'
        bc_name = 'BC-' + instance_name + '-' + set_name
        model.ZsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

        instance_name = 'INNER-SHELL'
        set_name = 'SET-SURFACE-T0'
        bc_name = 'BC-' + instance_name + '-' + set_name
        model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

        instance_name = 'INNER-SHELL'
        set_name = 'SET-SURFACE-T1'
        bc_name = 'BC-' + instance_name + '-' + set_name
        model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

        instance_name = 'OUTER-SHELL'
        set_name = 'SET-SURFACE-T0'
        bc_name = 'BC-' + instance_name + '-' + set_name
        model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

        instance_name = 'OUTER-SHELL'
        set_name = 'SET-SURFACE-T1'
        bc_name = 'BC-' + instance_name + '-' + set_name
        model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

        instance_name = 'OUTER-SHELL'
        surface_name = 'SURFACE-R1'
        load_name = 'LOAD-' + instance_name + '-' + surface_name
        model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=UNIFORM, field='', magnitude=30.0, amplitude=UNSET)

        instance_name = 'OUTER-SHELL'
        surface_name = 'SURFACE-X0'
        load_name = 'LOAD-' + instance_name + '-' + surface_name
        model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=UNIFORM, field='', magnitude=30.0, amplitude=UNSET)

        instance_name = 'INNER-SHELL'
        surface_name = 'SURFACE-FRONT-INNER'
        load_name = 'LOAD-' + instance_name + '-' + surface_name
        model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=UNIFORM, field='', magnitude=30.0, amplitude=UNSET)

        if major_version >= 2022:
            mdb.Job(name='Job-1', model='Model-1', description='', type=ANALYSIS,
                    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
                    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
                    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
                    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
                    scratch='', resultsFormat=ODB, numThreadsPerMpiProcess=1,
                    multiprocessingMode=DEFAULT, numCpus=4, numDomains=4, numGPUs=0)
        else:
            mdb.Job(name='Job-1', model='Model-1', description='', type=ANALYSIS,
                    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
                    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
                    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
                    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
                    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=4,
                    numDomains=4, numGPUs=0)
