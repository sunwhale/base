# -*- coding: utf-8 -*-
"""

"""
import math
from copy import deepcopy

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

import sys

# FLOW_PATH = r'F:\Github\base\base\utils\flow'
FLOW_PATH = r'/home/dell/base/base/utils/flow'
sys.path.insert(0, FLOW_PATH)

from utils import ABAQUS_ENV, Circle3D, Counter, Cylinder, Line2D, Plane, calc_arc, degrees_to_radians, find_duplicates, geometries, geometries_hex, get_direction, get_same_volume_cells, get_z_list, is_unicode_all_uppercase, line_circle_intersection, \
    load_json, min_difference, mirror_y_axis, plot_geometries, plot_geometries_hex, plot_three_arcs, polar_to_cartesian, radians_to_degrees, rotate_point_around_origin_2d, rotate_point_around_vector, set_material, set_obj, solve_three_arcs, \
    combine_surfaces, major_version, get_common_faces_between_sets, get_same_area_faces, generate_part_mesh, create_face_set_from_surface, insert_COH3D8_at_face_set, vertices_in_cells, is_cell_in_set, create_surface_from_p_remove_given_surface_names, \
    get_cells_adjacent_to_set_and_remove_set_names, ignore_common_edges_of_faces


def create_sketch_block(model, sketch_name, points, index_r, index_t):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 0], point2=points[index_r, 0]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[index_r, 0], point2=points[index_r, index_t], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[index_r, index_t], point2=points[0, index_t]))
    geom_list.append(s.Line(point1=points[0, index_t], point2=points[0, 0]))
    return s


def create_sketch_cut(model, sketch_name, x0, deep, a, b, angle_demolding_1, n):
    s_cut = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = [x0 + deep, 0.0]
    p1 = [x0 + deep, -a]
    p2 = [x0 + deep + b, 0.0]
    e1 = s_cut.EllipseByCenterPerimeter(center=center, axisPoint1=p1, axisPoint2=p2)
    l1 = Line2D(p1, np.tan(degrees_to_radians(angle_demolding_1)))
    l2 = Line2D([x0, 0.0], [x0, 1.0])
    p3 = l1.get_intersection(l2)
    p4 = [p3[0], 0.0]
    s_cut.Line(point1=p1, point2=p3)
    s_cut.Line(point1=p3, point2=p4)
    s_cut.Line(point1=center, point2=p2)
    s_cut.autoTrimCurve(curve1=e1, point1=[x0 + deep, a])
    s_cut.Line(point1=p4, point2=center)
    geom_list = []
    for g in s_cut.geometry.values():
        geom_list.append(g)
    s_cut.rotate(centerPoint=(0.0, 0.0), angle=180.0 / n, objectList=geom_list)
    return s_cut


def create_sketch_cut_front(model, sketch_name, x0, deep, a, b, angle_demolding_1, n, r_front):
    s_cut = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = [x0 + deep, 0.0]
    p1 = [x0 + deep, -a]
    p2 = [x0 + deep + b, 0.0]
    e1 = s_cut.EllipseByCenterPerimeter(center=center, axisPoint1=p1, axisPoint2=p2)
    l1 = Line2D(p1, np.tan(degrees_to_radians(angle_demolding_1)))
    l2 = Line2D([x0, 0.0], [x0, 1.0])
    p3 = l1.get_intersection(l2)
    p4 = [p3[0], 0.0]
    p1p = rotate_point_around_origin_2d(p1, degrees_to_radians(180.0 / n))
    s_cut.Spot(point=p1p)
    s_cut.Line(point1=p1, point2=p3)
    s_cut.Line(point1=p3, point2=p4)
    s_cut.Line(point1=center, point2=p2)
    s_cut.autoTrimCurve(curve1=e1, point1=[x0 + deep, a])
    s_cut.Line(point1=p4, point2=center)
    center_line = s_cut.ConstructionLine(point1=(x0 + deep - r_front, -1e4), point2=(x0 + deep - r_front, 1e4))
    geom_list = []
    for g in s_cut.geometry.values():
        geom_list.append(g)
    s_cut.rotate(centerPoint=(0.0, 0.0), angle=180.0 / n, objectList=geom_list)
    s_cut.assignCenterline(line=center_line)
    return s_cut, p1p


def create_sketch_block_cut_revolve(model, sketch_name, t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list, pen):
    s_block_cut_revolve = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)

    result = solve_three_arcs(p0, theta0_deg, p3, theta3_deg, r1, r2, r3)
    l1 = Line2D(p3, np.tan(degrees_to_radians(theta_in_deg)))
    l2 = Line2D([0.0, points[index_r, 0, 0]], [1.0, points[index_r, 0, 0]])
    l3 = Line2D((z_list[-1], 0.0), (z_list[-1], 1.0))
    if l1.get_intersection(l2)[0] > l1.get_intersection(l3)[0]:
        p4 = l1.get_intersection(l3)
        p5 = (pen, p4[1])
    else:
        p4 = l1.get_intersection(l2)
        p5 = (z_list[-1], p4[1])

    p1 = result['p1']
    p2 = result['p2']
    c1 = result['c1']
    c2 = result['c2']
    c3 = result['c3']
    delta1 = result['delta1']
    delta2 = result['delta2']
    delta3 = result['delta3']

    s_block_cut_revolve.ArcByCenterEnds(center=c1, point1=p0, point2=p1, direction=get_direction(delta1))
    s_block_cut_revolve.ArcByCenterEnds(center=c2, point1=p1, point2=p2, direction=get_direction(delta2))
    s_block_cut_revolve.ArcByCenterEnds(center=c3, point1=p2, point2=p3, direction=get_direction(delta3))
    s_block_cut_revolve.Line(point1=p0, point2=(p0[0], 1))
    s_block_cut_revolve.Line(point1=(p0[0], 1), point2=(-pen, 1))
    s_block_cut_revolve.Line(point1=(-pen, 1), point2=(-pen, pen))
    s_block_cut_revolve.Line(point1=(-pen, pen), point2=(p5[0], pen))
    s_block_cut_revolve.Line(point1=(p5[0], pen), point2=p5)
    s_block_cut_revolve.Line(point1=p5, point2=p4)
    s_block_cut_revolve.Line(point1=p3, point2=p4)
    center_line = s_block_cut_revolve.ConstructionLine(point1=(0.0, 0.0), point2=(pen, 0.0))
    s_block_cut_revolve.assignCenterline(line=center_line)

    return s_block_cut_revolve, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3


def create_sketch_block_cut_revolve_shift(model, sketch_name, t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3):
    s_block_cut_revolve_shift = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)
    geom_list = []
    geom_list.append(s_block_cut_revolve_shift.Line(point1=(p0[0], x0), point2=p0))
    geom_list.append(s_block_cut_revolve_shift.ArcByCenterEnds(center=c1, point1=p0, point2=p1, direction=get_direction(delta1)))
    geom_list.append(s_block_cut_revolve_shift.ArcByCenterEnds(center=c2, point1=p1, point2=p2, direction=get_direction(delta2)))
    geom_list.append(s_block_cut_revolve_shift.ArcByCenterEnds(center=c3, point1=p2, point2=p3, direction=get_direction(delta3)))
    geom_list.append(s_block_cut_revolve_shift.Line(point1=p3, point2=p4))
    geom_list.append(s_block_cut_revolve_shift.Line(point1=p4, point2=p5))
    # 逆序循环，保证轮廓线从外到内的顺序排列
    for i in range(index_r - 1, 0, -1):
        s_block_cut_revolve_shift.offset(distance=float(points[index_r, 0][0] - points[i, 0][0]), objectList=geom_list, side=RIGHT)
    return s_block_cut_revolve_shift


def create_sketch_block_cut_revolve_penult(model, sketch_name, t, x0, deep, block_length, z_list, block_insulation_thickness, a, b, pen):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)

    p0 = [block_length / 2.0 + z_list[-1] - z_list[-2], x0 + deep + b - 1.0]
    p1 = [block_length / 2.0, x0 + deep + b - 1.0]
    p2 = [block_length / 2.0 - block_insulation_thickness, x0 + deep + b - 1.0]
    l1 = Line2D(p2, np.tan(degrees_to_radians(45.0)))
    l2 = Line2D([0.0, 0.0], [1.0, 0.0])
    p3 = l1.get_intersection(l2)
    p4 = [block_length / 2.0 + z_list[-1] - z_list[-2], 0.0]

    s.Line(point1=p0, point2=p1)
    s.Line(point1=p1, point2=p2)
    s.Line(point1=p2, point2=p3)
    s.Line(point1=p3, point2=p4)
    s.Line(point1=p4, point2=p0)

    center_line = s.ConstructionLine(point1=(0.0, 0.0), point2=(pen, 0.0))
    s.assignCenterline(line=center_line)

    return s


def create_part_block(model, part_name, points, lines, faces, dimension):
    z_list = dimension['z_list']
    deep = dimension['deep']
    x0 = dimension['x0']
    length_up = dimension['length_up']
    width = dimension['width']
    angle_demolding_1 = dimension['angle_demolding_1']
    angle_demolding_2 = dimension['angle_demolding_2']
    fillet_radius = dimension['fillet_radius']
    a = dimension['a']
    b = dimension['b']
    size = dimension['size']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    element_size = dimension['element_size']
    origin = (0.0, 0.0, 0.0)
    length = z_list[-1] * 2.0
    pen = 1e4
    tol = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-BLOCK
    s_block = create_sketch_block(model, 'SKETCH-BLOCK', points, index_r, index_t)

    # Extrude
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    d = p.datums

    p.BaseSolidExtrude(sketch=s_block, depth=length / 2.0)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)

    # SKETCH-BLOCK-PARTITION
    s_block_partition = model.ConstrainedSketch(name='SKETCH-BLOCK-PARTITION', sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    # 拾取被切割平面上的线段，同一个theta
    for i in range(1, index_t):
        geom_list.append(s_block_partition.Line(point1=points[0, i], point2=points[index_r, i]))
    # 拾取被切割平面上的线段，同一个r
    for i in range(1, index_r):
        geom_list.append(s_block_partition.ArcByCenterEnds(center=center, point1=points[i, 0], point2=points[i, index_t], direction=COUNTERCLOCKWISE))

    # Partition
    p_faces = p.faces.getByBoundingBox(0, 0, 0, pen, pen, tol)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketchOrientation=BOTTOM, sketch=s_block_partition)

    # 拾取被切割平面上的线段，同一个r
    partition_edges = []
    line_keys = []
    for i in range(1, index_r):
        for j in range(0, index_t):
            line_key = '%s%s-%s%s' % (i, j, i, j + 1)
            line_keys.append(line_key)

    for line_key in line_keys:
        line_middle_point = lines[line_key][3]
        x, y = line_middle_point
        edge_sequence = p.edges.findAt(((x, y, 0),))
        if len(edge_sequence) > 0:
            partition_edges.append(edge_sequence[0])
    p.PartitionCellByExtrudeEdge(line=p.datums[z_axis.id], cells=p.cells, edges=partition_edges, sense=FORWARD)

    # 拾取被切割平面上的线段，同一个theta
    partition_edges = []
    line_keys = []

    for j in range(1, index_t):
        for i in range(0, index_r):
            line_key = '%s%s-%s%s' % (i, j, i + 1, j)
            line_keys.append(line_key)

    for line_key in line_keys:
        line_middle_point = lines[line_key][3]
        x, y = line_middle_point
        edge_sequence = p.edges.findAt(((x, y, 0),))
        if len(edge_sequence) > 0:
            partition_edges.append(edge_sequence[0])
    p.PartitionCellByExtrudeEdge(line=p.datums[z_axis.id], cells=p.cells, edges=partition_edges, sense=FORWARD)

    xy_plane_z = {}
    for i in range(1, len(z_list) - 1):
        xy_plane_z[i] = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=z_list[i])
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z[i].id], cells=p.cells)

    # SKETCH-CUT
    s_cut = create_sketch_cut(model, 'SKETCH-CUT', x0, deep, a, b, angle_demolding_1, n)

    # CutExtrude
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cut, flipExtrudeDirection=ON)

    # Mirror
    if size == '1':
        p.Mirror(mirrorPlane=d[xy_plane.id], keepOriginal=ON)
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    elif size == '1/2':
        p.Mirror(mirrorPlane=d[xy_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    set_names = create_block_sets_common(p, faces, dimension)

    create_block_surface_common(p, points, dimension)

    p1 = [x0 + deep + b, 0.0]
    x1 = p1[0] * np.cos(degrees_to_radians(180.0 / n))
    y1 = p1[0] * np.sin(degrees_to_radians(180.0 / n))
    p_faces = p.faces.getByBoundingBox(0, tol, 0, x1 * 1.1, y1, length / 2.0)
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-CUT')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-CUT'], 'SURFACE-INNER')

    create_face_set_from_surface(p)

    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')

    # Partition
    p1 = [x0 + deep, -a]
    offset = p1[0] * np.cos(degrees_to_radians(180.0 / n)) - p1[1] * np.sin(degrees_to_radians(180.0 / n))
    yz_plane_2 = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=offset)
    p.PartitionCellByDatumPlane(datumPlane=d[yz_plane_2.id], cells=p.cells)

    generate_part_mesh(p, element_size=element_size)

    insert_COH3D8_at_face_set(p, 'SET-FACES-GRAIN-INSULATION', 'COHESIVE-ELEMENTS-GRAIN-INSULATION')

    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_gap(model, part_name, points, lines, faces, dimension):
    z_list = dimension['z_list']
    deep = dimension['deep']
    x0 = dimension['x0']
    length_up = dimension['length_up']
    width = dimension['width']
    angle_demolding_1 = dimension['angle_demolding_1']
    angle_demolding_2 = dimension['angle_demolding_2']
    fillet_radius = dimension['fillet_radius']
    a = dimension['a']
    b = dimension['b']
    size = dimension['size']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    element_size = dimension['element_size']
    origin = (0.0, 0.0, 0.0)
    length = z_list[-2] * 2.0
    pen = 1e4
    tol = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-GAP
    s_gap_z = model.ConstrainedSketch(name='SKETCH-GAP-Z', sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s_gap_z.Line(point1=points[0, 2], point2=points[2, 2]))
    geom_list.append(s_gap_z.ArcByCenterEnds(center=center, point1=points[2, 2], point2=points[2, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s_gap_z.Line(point1=points[2, 3], point2=points[0, 3]))
    geom_list.append(s_gap_z.Line(point1=points[0, 3], point2=points[0, 2]))

    # Extrude
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(sketch=s_gap_z, depth=length / 2.0)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    xy_plane_z1 = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=length / 2.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums

    # SKETCH-GAP
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, length / 2.0))
    s_gap_t = model.ConstrainedSketch(name='SKETCH-GAP-T', sheetSize=4000.0, gridSpacing=100.0, transform=t)
    center = (0, 0)
    geom_list = []
    geom_list.append(s_gap_t.Line(point1=points[0, 0], point2=points[2, 0]))
    geom_list.append(s_gap_t.ArcByCenterEnds(center=center, point1=points[2, 0], point2=points[2, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s_gap_t.Line(point1=points[2, 3], point2=points[0, 3]))
    geom_list.append(s_gap_t.Line(point1=points[0, 3], point2=points[0, 0]))
    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_t, depth=(z_list[-1] - z_list[-2]), flipExtrudeDirection=OFF)

    # Partition
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z1.id], cells=p.cells)
    cut_edges = (
        p.edges.findAt((lines['02-12'][3][0], lines['02-12'][3][1], length / 2.0)),
    )
    p.PartitionCellByExtrudeEdge(line=d[z_axis.id], cells=p.cells, edges=cut_edges, sense=FORWARD)

    # SKETCH-CUT
    s_cut = create_sketch_cut(model, 'SKETCH-CUT', x0, deep, a, b, angle_demolding_1, n)

    # CutExtrude
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cut, flipExtrudeDirection=ON)

    # Mirror
    if size == '1':
        p.Mirror(mirrorPlane=d[xy_plane.id], keepOriginal=ON)
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    elif size == '1/2':
        p.Mirror(mirrorPlane=d[xy_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    create_gap_surface_common(p, points, dimension)

    p1 = [x0 + deep + b, 0.0]
    x1 = p1[0] * np.cos(degrees_to_radians(180.0 / n))
    y1 = p1[0] * np.sin(degrees_to_radians(180.0 / n))
    p_faces = p.faces.getByBoundingBox(0, tol, 0, x1 * 1.1, y1, z_list[-1])
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-CUT')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-CUT'], 'SURFACE-INNER')

    create_face_set_from_surface(p)

    set_name = 'SET-CELL-GLUE'
    p.Set(cells=p.cells, name=set_name)

    # Partition
    p1 = [x0 + deep, -a]
    offset = p1[0] * np.cos(degrees_to_radians(180.0 / n)) - p1[1] * np.sin(degrees_to_radians(180.0 / n))
    yz_plane_2 = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=offset)
    p.PartitionCellByDatumPlane(datumPlane=d[yz_plane_2.id], cells=p.cells)

    generate_part_mesh(p, element_size=element_size)

    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_front(model, part_name, points, lines, faces, dimension):
    z_list = dimension['z_list']
    deep = dimension['deep']
    x0 = dimension['x0']
    length_up = dimension['length_up']
    width = dimension['width']
    angle_demolding_1 = dimension['angle_demolding_1']
    angle_demolding_2 = dimension['angle_demolding_2']
    fillet_radius = dimension['fillet_radius']
    a = dimension['a']
    b = dimension['b']
    size = dimension['size']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    element_size = dimension['element_size']
    r_front = dimension['r_front']
    length_front = dimension['length_front']
    p0 = dimension['p0']
    theta0_deg = dimension['theta0_deg']
    p3 = dimension['p3']
    theta3_deg = dimension['theta3_deg']
    theta_in_deg = dimension['theta_in_deg']
    r1 = dimension['r1']
    r2 = dimension['r2']
    r3 = dimension['r3']

    origin = (0.0, 0.0, 0.0)
    length = z_list[-1] * 2.0
    pen = 1e4
    tol = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-BLOCK
    s_block = create_sketch_block(model, 'SKETCH-BLOCK', points, index_r, index_t)
    s_block_grain = create_sketch_block(model, 'SKETCH-BLOCK-GRAIN', points, index_r, 2)

    # Extrude
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(sketch=s_block, depth=length / 2.0)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums

    # 头部药块额外拉伸
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_block, depth=length_front, flipExtrudeDirection=ON)

    # 旋转切割头部外轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_block_cut_revolve, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_block_cut_revolve(model, 'SKETCH-BLOCK-CUT-REVOLVE', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list, pen)

    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_block_cut_revolve, angle=360.0, flipRevolveDirection=ON)

    # 草图切割环向面
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_block_cut_revolve_shift = create_sketch_block_cut_revolve_shift(model, 'SKETCH-BLOCK-CUT-REVOLVE-SHIFT', t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3)

    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for g in s_block_cut_revolve_shift.geometry.values()[:6]:
        z, x = g.pointOn
        point = (x, 0.0, z)
        angle = degrees_to_radians(180.0 / n / 2.0)
        point_rot = rotate_point_around_vector(point, [0, 0, 1], angle)
        p_faces += p.faces.findAt((point_rot,))
        # p.DatumPointByCoordinate(coords=point_rot)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    g = s_block_cut_revolve_shift.geometry
    faces_xz_plane = {}
    for i in range(1, index_r):
        faces_xz_plane[i] = []
        for j in [2, 3, 4, 5, 6, 7]:
            pa = (np.array(g[j + 6 * (i - 1)].pointOn) + np.array(g[j + 6 * i].pointOn)) / 2.0
            faces_xz_plane[i].append(pa)
            s_block_cut_revolve_shift.Spot(point=pa)

    for i in range(1, index_r):
        for j in [3, 4, 5, 6, 7]:
            pa = g[6 * (i - 1) + j].getVertices()[0].coords
            pb = g[6 * i + j].getVertices()[0].coords
            s_block_cut_revolve_shift.Line(point1=pa, point2=pb)

    p_faces = p.faces.getByBoundingBox(0, 0, -pen, pen, tol, pen)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketch=s_block_cut_revolve_shift)

    # 基于p4点所在的半径拾取sweep_edge
    x, y = polar_to_cartesian(p4[1], tol)
    # x = min(x, points[index_r, 0][0])
    sweep_edge = p.edges.findAt((x, y, z_list[-1]))

    # 拾取主体弧线
    partition_edges = []
    for g in s_block_cut_revolve_shift.geometry.values()[2:index_r * 6]:
        z, x = g.pointOn
        p.DatumPointByCoordinate(coords=(x, 0.0, z))
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # 基于p4点所在的半径拾取sweep_edge
    x, y = polar_to_cartesian(p4[1], tol)
    x = min(x, points[index_r, 0][0])
    sweep_edge = p.edges.findAt((x, y, z_list[-1]))

    # 拾取分段连线
    partition_edges = []
    for g in s_block_cut_revolve_shift.geometry.values()[index_r * 6:]:
        z, x = g.pointOn
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # 建立不同z的xy_plane
    xy_plane_z = {}
    for i in range(1, len(z_list)):
        xy_plane_z[i] = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=z_list[i])

    # SKETCH-BLOCK-PARTITION
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z[len(z_list) - 1].id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, z_list[-1]))
    s_block_partition = model.ConstrainedSketch(name='SKETCH-BLOCK-PARTITION', sheetSize=200.0, transform=t)
    geom_list = []
    # 拾取被切割平面上的线段，同一个theta
    for i in range(1, index_t):
        geom_list.append(s_block_partition.Line(point1=points[0, i], point2=points[index_r, i]))

    # Partition
    p_faces = p.faces.getByBoundingBox(0, 0, z_list[-1], pen, pen, pen)
    p.PartitionFaceBySketch(sketchUpEdge=d[y_axis.id], faces=p_faces, sketch=s_block_partition)

    # 拾取被切割平面上的线段，同一个theta
    partition_edges = []
    line_keys = []

    for j in range(1, index_t):
        for i in range(0, index_r):
            line_key = '%s%s-%s%s' % (i, j, i + 1, j)
            line_keys.append(line_key)

    for line_key in line_keys:
        line_middle_point = lines[line_key][3]
        x, y = line_middle_point
        edge_sequence = p.edges.findAt(((x, y, z_list[-1]),))
        if len(edge_sequence) > 0:
            partition_edges.append(edge_sequence[0])
    p.PartitionCellByExtrudeEdge(line=p.datums[z_axis.id], cells=p.cells, edges=partition_edges, sense=REVERSE)

    # SKETCH-CUT-FRONT
    s_cut, p1p = create_sketch_cut_front(model, 'SKETCH-CUT-FRONT', x0, deep, a, b, angle_demolding_1, n, r_front)

    # 切割头部燃道
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cut, flipExtrudeDirection=ON)
    p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cut, angle=90.0, flipRevolveDirection=OFF)

    for i in range(1, len(z_list) - 1):
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z[i].id], cells=p.cells)

    # Mirror
    if size == '1':
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
        # p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    elif size == '1/2':
        pass
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    # 建立GRAIN集合
    cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for rtz in [
        [0, 0, 0]
    ]:
        cells += p.cells.findAt(((faces[rtz[0], rtz[1]][0], faces[rtz[0], rtz[1]][1], z_centers[rtz[2]]),))
    cells = get_same_volume_cells(p, cells)
    for pa in faces_xz_plane[index_r - 1]:
        cells += p.cells.findAt(((pa[1], 0.0, pa[0]),))
        # center = (0.0, 0.0, pa[0])
        # p.DatumPointByCoordinate(coords=center)
        # plane_1 = Plane(center, (0.0, 0.0, 1.0))
        # circle = Circle3D(center, abs(pa[1]), plane_1)
        # for j in [1]:
        #     plane_2 = Plane(center, (0.0, 1.0, 0.0))
        #     pb = plane_2.intersection_with_circle(circle)
        #     if pb:
        #         p.DatumPointByCoordinate(coords=pb[0])
        #         p.DatumPointByCoordinate(coords=pb[1])
        # c = p.cells.findAt((pb[0],))
        # cells += c
    if cells:
        p.Set(cells=cells, name='SET-CELL-GRAIN')

    # 建立INSULATION集合
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-GRAIN', ['SET-CELL-GRAIN'])
    p.Set(cells=cells, name='SET-CELL-INSULATION')

    # 建立GLUE集合
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-INSULATION', ['SET-CELL-GRAIN', 'SET-CELL-INSULATION'])
    p.Set(cells=cells, name='SET-CELL-GLUE-A')

    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    p_edges = []
    for z_center in z_centers:
        p_edges.append(p.edges.findAt((p1p[0], p1p[1], z_center)))
    p_edges.append(p.edges.findAt((p1p[0], p1p[1], 0.0)))
    p.PartitionCellByExtrudeEdge(line=d[y_axis.id], cells=p.cells, edges=p_edges, sense=REVERSE)

    create_block_surface_common(p, points, dimension)

    p1 = [x0 + deep + b, 0.0]
    x1 = p1[0] * np.cos(degrees_to_radians(180.0 / n))
    y1 = p1[0] * np.sin(degrees_to_radians(180.0 / n))
    p_faces = p.faces.getByBoundingBox(0, tol, -r_front - b, x1 * 1.1, y1, length / 2.0)
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-CUT')

    xz_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=180.0 / n / 2.0)
    p.PartitionCellByDatumPlane(datumPlane=d[xz_plane_rot.id], cells=p.cells)

    if size == '1':
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
        xz_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=-180.0 / n / 2.0)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane_rot.id], cells=p.cells)

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    given_surface_names.remove('SURFACE-OUTER')
    create_surface_from_p_remove_given_surface_names(p, given_surface_names, 'SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-Z1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-CUT'], 'SURFACE-INNER')

    create_face_set_from_surface(p)

    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')

    generate_part_mesh(p, element_size=element_size)

    # insert_COH3D8_at_face_set(p, 'SET-FACES-GRAIN-INSULATION', 'COHESIVE-ELEMENTS-GRAIN-INSULATION')

    set_section_common(p)
    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_gap_front(model, part_name, points, lines, faces, dimension):
    z_list = dimension['z_list']
    deep = dimension['deep']
    x0 = dimension['x0']
    length_up = dimension['length_up']
    width = dimension['width']
    angle_demolding_1 = dimension['angle_demolding_1']
    angle_demolding_2 = dimension['angle_demolding_2']
    fillet_radius = dimension['fillet_radius']
    a = dimension['a']
    b = dimension['b']
    size = dimension['size']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    element_size = dimension['element_size']
    r_front = dimension['r_front']
    length_front = dimension['length_front']
    p0 = dimension['p0']
    theta0_deg = dimension['theta0_deg']
    p3 = dimension['p3']
    theta3_deg = dimension['theta3_deg']
    theta_in_deg = dimension['theta_in_deg']
    r1 = dimension['r1']
    r2 = dimension['r2']
    r3 = dimension['r3']

    origin = (0.0, 0.0, 0.0)
    length = z_list[-2] * 2.0
    pen = 1e4
    tol = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-GAP-Z
    s_gap_z = model.ConstrainedSketch(name='SKETCH-GAP-Z', sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s_gap_z.Line(point1=points[0, 2], point2=points[3, 2]))
    geom_list.append(s_gap_z.ArcByCenterEnds(center=center, point1=points[3, 2], point2=points[3, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s_gap_z.Line(point1=points[3, 3], point2=points[0, 3]))
    geom_list.append(s_gap_z.Line(point1=points[0, 3], point2=points[0, 2]))

    # Extrude
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(sketch=s_gap_z, depth=length / 2.0)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    xy_plane_z1 = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=length / 2.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums

    # 头部药块额外拉伸
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_z, depth=length_front, flipExtrudeDirection=ON)

    # SKETCH-BLOCK-CUT-REVOLVE
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_block_cut_revolve, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_block_cut_revolve(model, 'SKETCH-BLOCK-CUT-REVOLVE', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list, pen)
    # 旋转切割头部外轮廓
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_block_cut_revolve, angle=360.0, flipRevolveDirection=ON)

    # 草图切割环向面
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_block_cut_revolve_shift = create_sketch_block_cut_revolve_shift(model, 'SKETCH-BLOCK-CUT-REVOLVE-SHIFT', t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3)

    # SKETCH-GAP-T
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, length / 2.0))
    s_gap_t = model.ConstrainedSketch(name='SKETCH-GAP-T', sheetSize=4000.0, gridSpacing=100.0, transform=t)
    center = (0, 0)
    geom_list = []
    geom_list.append(s_gap_t.Line(point1=points[0, 0], point2=points[3, 0]))
    geom_list.append(s_gap_t.ArcByCenterEnds(center=center, point1=points[3, 0], point2=points[3, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s_gap_t.Line(point1=points[3, 3], point2=points[0, 3]))
    geom_list.append(s_gap_t.Line(point1=points[0, 3], point2=points[0, 0]))
    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_t, depth=(z_list[-1] - z_list[-2]), flipExtrudeDirection=OFF)

    # 旋转切割头部外轮廓
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_block_cut_revolve, angle=360.0, flipRevolveDirection=ON)

    # Partition
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z1.id], cells=p.cells)

    point1 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], length / 2.0))
    point2 = p.DatumPointByCoordinate(coords=(lines['02-12'][2][0], lines['02-12'][2][1], length / 2.0))
    point3 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], 0.0))
    partition_plane = p.DatumPlaneByThreePoints(point1=d[point1.id], point2=d[point2.id], point3=d[point3.id])
    p.PartitionCellByDatumPlane(datumPlane=d[partition_plane.id], cells=p.cells)

    # SKETCH-CUT-FRONT
    s_cut, p1p = create_sketch_cut_front(model, 'SKETCH-CUT-FRONT', x0, deep, a, b, angle_demolding_1, n, r_front)

    # 切割头部燃道
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cut, flipExtrudeDirection=ON)
    p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cut, angle=90.0, flipRevolveDirection=OFF)

    # Mirror
    if size == '1':
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    elif size == '1/2':
        pass
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    create_gap_surface_common(p, points, dimension)

    p1 = [x0 + deep + b, 0.0]
    x1 = p1[0] * np.cos(degrees_to_radians(180.0 / n))
    y1 = p1[0] * np.sin(degrees_to_radians(180.0 / n))
    p_faces = p.faces.getByBoundingBox(0, tol, -r_front - b, x1 * 1.1, y1, z_list[-1])
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-CUT')

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    create_surface_from_p_remove_given_surface_names(p, given_surface_names, 'SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-Z1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-CUT'], 'SURFACE-INNER')

    create_face_set_from_surface(p)

    # Partition
    p1 = [x0 + deep, -a]
    offset = p1[0] * np.cos(degrees_to_radians(180.0 / n)) - p1[1] * np.sin(degrees_to_radians(180.0 / n))
    yz_plane_2 = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=offset)
    p.PartitionCellByDatumPlane(datumPlane=d[yz_plane_2.id], cells=p.cells.getByBoundingBox(0, -pen, 0, pen, pen, pen))
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    # 拓扑层面忽略外表面的公共边
    p_faces = p.surfaces['SURFACE-OUTER'].faces.getByBoundingBox(0, -pen, -pen, pen, pen, 0)
    ignore_common_edges_of_faces(p, p_faces)

    set_name = 'SET-CELL-GLUE-A'
    p.Set(cells=p.cells, name=set_name)

    generate_part_mesh(p, element_size=element_size)

    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_penult(model, part_name, points, lines, faces, dimension):
    z_list = dimension['z_list']
    deep = dimension['deep']
    x0 = dimension['x0']
    length_up = dimension['length_up']
    width = dimension['width']
    angle_demolding_1 = dimension['angle_demolding_1']
    angle_demolding_2 = dimension['angle_demolding_2']
    fillet_radius = dimension['fillet_radius']
    a = dimension['a']
    b = dimension['b']
    size = dimension['size']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    element_size = dimension['element_size']
    origin = (0.0, 0.0, 0.0)
    length = z_list[-1] * 2.0
    pen = 1e4
    tol = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-BLOCK
    s_block = create_sketch_block(model, 'SKETCH-BLOCK', points, index_r, index_t)

    # Extrude
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    d = p.datums

    p.BaseSolidExtrude(sketch=s_block, depth=length / 2.0)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)

    # SKETCH-BLOCK-PARTITION
    s_block_partition = model.ConstrainedSketch(name='SKETCH-BLOCK-PARTITION', sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    # 拾取被切割平面上的线段，同一个theta
    for i in range(1, index_t):
        geom_list.append(s_block_partition.Line(point1=points[0, i], point2=points[index_r, i]))
    # 拾取被切割平面上的线段，同一个r
    for i in range(1, index_r):
        geom_list.append(s_block_partition.ArcByCenterEnds(center=center, point1=points[i, 0], point2=points[i, index_t], direction=COUNTERCLOCKWISE))

    # Partition
    p_faces = p.faces.getByBoundingBox(0, 0, 0, pen, pen, tol)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketchOrientation=BOTTOM, sketch=s_block_partition)

    # 拾取被切割平面上的线段，同一个r
    partition_edges = []
    line_keys = []
    for i in range(1, index_r):
        for j in range(0, index_t):
            line_key = '%s%s-%s%s' % (i, j, i, j + 1)
            line_keys.append(line_key)

    for line_key in line_keys:
        line_middle_point = lines[line_key][3]
        x, y = line_middle_point
        edge_sequence = p.edges.findAt(((x, y, 0),))
        if len(edge_sequence) > 0:
            partition_edges.append(edge_sequence[0])
    p.PartitionCellByExtrudeEdge(line=p.datums[z_axis.id], cells=p.cells, edges=partition_edges, sense=FORWARD)

    # 拾取被切割平面上的线段，同一个theta
    partition_edges = []
    line_keys = []

    for j in range(1, index_t):
        for i in range(0, index_r):
            line_key = '%s%s-%s%s' % (i, j, i + 1, j)
            line_keys.append(line_key)

    for line_key in line_keys:
        line_middle_point = lines[line_key][3]
        x, y = line_middle_point
        edge_sequence = p.edges.findAt(((x, y, 0),))
        if len(edge_sequence) > 0:
            partition_edges.append(edge_sequence[0])
    p.PartitionCellByExtrudeEdge(line=p.datums[z_axis.id], cells=p.cells, edges=partition_edges, sense=FORWARD)

    xy_plane_z = {}
    for i in range(1, len(z_list) - 1):
        xy_plane_z[i] = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=z_list[i])
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z[i].id], cells=p.cells)

    # SKETCH-CUT
    s_cut = create_sketch_cut(model, 'SKETCH-CUT', x0, deep, a, b, angle_demolding_1, n)

    # CutExtrude
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cut, flipExtrudeDirection=ON)

    # Mirror
    if size == '1':
        p.Mirror(mirrorPlane=d[xy_plane.id], keepOriginal=ON)
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    elif size == '1/2':
        p.Mirror(mirrorPlane=d[xy_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    set_names = create_block_sets_common(p, faces, dimension)

    create_block_surface_common(p, points, dimension)

    p1 = [x0 + deep + b, 0.0]
    x1 = p1[0] * np.cos(degrees_to_radians(180.0 / n))
    y1 = p1[0] * np.sin(degrees_to_radians(180.0 / n))
    p_faces = p.faces.getByBoundingBox(0, tol, 0, x1 * 1.1, y1, length / 2.0)
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-CUT')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-CUT'], 'SURFACE-INNER')

    create_face_set_from_surface(p)

    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')

    # Partition
    p1 = [x0 + deep, -a]
    offset = p1[0] * np.cos(degrees_to_radians(180.0 / n)) - p1[1] * np.sin(degrees_to_radians(180.0 / n))
    yz_plane_2 = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=offset)
    p.PartitionCellByDatumPlane(datumPlane=d[yz_plane_2.id], cells=p.cells)

    # 旋转切割内燃道
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_block_cut_revolve_penult = create_sketch_block_cut_revolve_penult(model, 'SKETCH-BLOCK-PENULT-CUT-REVOLVE', t, x0, deep, block_length, z_list, block_insulation_thickness, a, b, pen)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_block_cut_revolve_penult, angle=360.0, flipRevolveDirection=ON)

    generate_part_mesh(p, element_size=element_size)

    insert_COH3D8_at_face_set(p, 'SET-FACES-GRAIN-INSULATION', 'COHESIVE-ELEMENTS-GRAIN-INSULATION')

    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_gap_penult(model, part_name, points, lines, faces, dimension):
    z_list = dimension['z_list']
    deep = dimension['deep']
    x0 = dimension['x0']
    length_up = dimension['length_up']
    width = dimension['width']
    angle_demolding_1 = dimension['angle_demolding_1']
    angle_demolding_2 = dimension['angle_demolding_2']
    fillet_radius = dimension['fillet_radius']
    a = dimension['a']
    b = dimension['b']
    size = dimension['size']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    element_size = dimension['element_size']
    origin = (0.0, 0.0, 0.0)
    length = z_list[-2] * 2.0
    pen = 1e4
    tol = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-GAP
    s_gap_z = model.ConstrainedSketch(name='SKETCH-GAP-Z', sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s_gap_z.Line(point1=points[0, 2], point2=points[2, 2]))
    geom_list.append(s_gap_z.ArcByCenterEnds(center=center, point1=points[2, 2], point2=points[2, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s_gap_z.Line(point1=points[2, 3], point2=points[0, 3]))
    geom_list.append(s_gap_z.Line(point1=points[0, 3], point2=points[0, 2]))

    # Extrude
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(sketch=s_gap_z, depth=length / 2.0)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    xy_plane_z1 = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=length / 2.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums

    # SKETCH-GAP
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, length / 2.0))
    s_gap_t = model.ConstrainedSketch(name='SKETCH-GAP-T', sheetSize=4000.0, gridSpacing=100.0, transform=t)
    center = (0, 0)
    geom_list = []
    geom_list.append(s_gap_t.Line(point1=points[0, 0], point2=points[2, 0]))
    geom_list.append(s_gap_t.ArcByCenterEnds(center=center, point1=points[2, 0], point2=points[2, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s_gap_t.Line(point1=points[2, 3], point2=points[0, 3]))
    geom_list.append(s_gap_t.Line(point1=points[0, 3], point2=points[0, 0]))
    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_t, depth=(z_list[-1] - z_list[-2]), flipExtrudeDirection=OFF)

    # Partition
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z1.id], cells=p.cells)
    cut_edges = (
        p.edges.findAt((lines['02-12'][3][0], lines['02-12'][3][1], length / 2.0)),
    )
    p.PartitionCellByExtrudeEdge(line=d[z_axis.id], cells=p.cells, edges=cut_edges, sense=FORWARD)

    # SKETCH-CUT
    s_cut = create_sketch_cut(model, 'SKETCH-CUT', x0, deep, a, b, angle_demolding_1, n)

    # CutExtrude
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cut, flipExtrudeDirection=ON)

    # Mirror
    if size == '1':
        p.Mirror(mirrorPlane=d[xy_plane.id], keepOriginal=ON)
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    elif size == '1/2':
        p.Mirror(mirrorPlane=d[xy_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    create_gap_surface_common(p, points, dimension)

    p1 = [x0 + deep + b, 0.0]
    x1 = p1[0] * np.cos(degrees_to_radians(180.0 / n))
    y1 = p1[0] * np.sin(degrees_to_radians(180.0 / n))
    p_faces = p.faces.getByBoundingBox(0, tol, 0, x1 * 1.1, y1, z_list[-1])
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-CUT')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-CUT'], 'SURFACE-INNER')

    create_face_set_from_surface(p)

    set_name = 'SET-CELL-GLUE'
    p.Set(cells=p.cells, name=set_name)

    # Partition
    p1 = [x0 + deep, -a]
    offset = p1[0] * np.cos(degrees_to_radians(180.0 / n)) - p1[1] * np.sin(degrees_to_radians(180.0 / n))
    yz_plane_2 = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=offset)
    p.PartitionCellByDatumPlane(datumPlane=d[yz_plane_2.id], cells=p.cells)

    # 旋转切割内燃道
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_block_cut_revolve_penult = create_sketch_block_cut_revolve_penult(model, 'SKETCH-BLOCK-PENULT-CUT-REVOLVE', t, x0, deep, block_length, z_list, block_insulation_thickness, a, b, pen)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_block_cut_revolve_penult, angle=360.0, flipRevolveDirection=ON)

    generate_part_mesh(p, element_size=element_size)

    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_block_sets_common(p, faces, dimension):
    z_list = dimension['z_list']
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    set_names = []
    cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for rtz in [
        [0, 0, 0]
    ]:
        cells += p.cells.findAt(((faces[rtz[0], rtz[1]][0], faces[rtz[0], rtz[1]][1], z_centers[rtz[2]]),))
    cells = get_same_volume_cells(p, cells)
    if cells is not None:
        set_name = 'SET-CELL-GRAIN'
        p.Set(cells=cells, name=set_name)
        set_names.append(set_name)

    cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for rtz in [
        [1, 0, 0],
        [1, 1, 0],
        [1, 0, 1],
        [1, 1, 1],
        [0, 0, 1],
        [0, 1, 0],
        [0, 1, 1]
    ]:
        cells += p.cells.findAt(((faces[rtz[0], rtz[1]][0], faces[rtz[0], rtz[1]][1], z_centers[rtz[2]]),))
    cells = get_same_volume_cells(p, cells)
    if cells is not None:
        set_name = 'SET-CELL-INSULATION'
        p.Set(cells=cells, name=set_name)
        set_names.append(set_name)

    if faces.shape[0] >= 3 and faces.shape[1] >= 3:
        cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
        for rtz in [
            [0, 2, 0],
            [1, 2, 0],
            [0, 2, 1],
            [1, 2, 1],
            [0, 2, 2],
            [1, 2, 2],
            [0, 0, 2],
            [0, 1, 2],
            [1, 0, 2],
            [1, 1, 2]
        ]:
            cells += p.cells.findAt(((faces[rtz[0], rtz[1]][0], faces[rtz[0], rtz[1]][1], z_centers[rtz[2]]),))

        cells = get_same_volume_cells(p, cells)
        if cells is not None:
            set_name = 'SET-CELL-GLUE-A'
            p.Set(cells=cells, name=set_name)
            set_names.append(set_name)

    if faces.shape[0] >= 3 and faces.shape[1] >= 3:
        cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
        for rtz in [
            [2, 0, 0],
            [2, 1, 0],
            [2, 2, 0],
            [2, 0, 1],
            [2, 1, 1],
            [2, 2, 1],
            [2, 0, 2],
            [2, 1, 2],
            [2, 2, 2],
        ]:
            cells += p.cells.findAt(((faces[rtz[0], rtz[1]][0], faces[rtz[0], rtz[1]][1], z_centers[rtz[2]]),))
        cells = get_same_volume_cells(p, cells)
        if cells is not None:
            set_name = 'SET-CELL-GLUE-B'
            p.Set(cells=cells, name=set_name)
            set_names.append(set_name)

    return set_names


def create_block_surface_common(p, points, dimension):
    z_list = dimension['z_list']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    length = z_list[-1] * 2.0

    p1 = (points[0, 0][0], points[0, 0][1], 0.0)
    p2 = (points[0, 1][0], points[0, 1][1], 0.0)
    p3 = (points[0, 0][0], points[0, 0][1], 1.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-X0')

    p1 = (points[0, 0][0], points[0, 0][1], 0.0)
    p2 = (points[0, 1][0], points[0, 1][1], 0.0)
    p3 = (points[1, 0][0], points[1, 0][1], 0.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-Z0')

    p1 = (points[0, 0][0], points[0, 0][1], length / 2.0)
    p2 = (points[0, 1][0], points[0, 1][1], length / 2.0)
    p3 = (points[1, 0][0], points[1, 0][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-Z1')

    p1 = (points[0, 0][0], points[0, 0][1], -length / 2.0)
    p2 = (points[0, 1][0], points[0, 1][1], -length / 2.0)
    p3 = (points[1, 0][0], points[1, 0][1], -length / 2.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-Z-1')

    p1 = (points[0, 0][0], points[0, 0][1], 0.0)
    p2 = (points[2, 0][0], points[2, 0][1], 0.0)
    p3 = (points[0, 0][0], points[0, 0][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-T0')

    p1 = (points[0, index_t][0], points[0, index_t][1], 0.0)
    p2 = (points[index_r, index_t][0], points[index_r, index_t][1], 0.0)
    p3 = (points[0, index_t][0], points[0, index_t][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-T1')

    p1 = (points[0, index_t][0], -points[0, index_t][1], 0.0)
    p2 = (points[index_r, index_t][0], -points[index_r, index_t][1], 0.0)
    p3 = (points[0, index_t][0], -points[0, index_t][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-T-1')

    cylinder = Cylinder((0, 0, 0), (0, 0, 1), points[index_r, 0, 0])
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if cylinder.is_point_on_cylinder(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')


def create_gap_surface_common(p, points, dimension):
    z_list = dimension['z_list']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    length = z_list[-1] * 2.0

    p1 = (points[0, 0][0], points[0, 0][1], 0.0)
    p2 = (points[0, 1][0], points[0, 1][1], 0.0)
    p3 = (points[0, 0][0], points[0, 0][1], 1.0)
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-X0')

    p1 = (points[0, 0][0], points[0, 0][1], 0.0)
    p2 = (points[0, 1][0], points[0, 1][1], 0.0)
    p3 = (points[1, 0][0], points[1, 0][1], 0.0)
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-Z0')

    p1 = (points[0, 0][0], points[0, 0][1], z_list[-2])
    p2 = (points[0, 1][0], points[0, 1][1], z_list[-2])
    p3 = (points[1, 0][0], points[1, 0][1], z_list[-2])
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-Z1')

    p1 = (points[0, 0][0], points[0, 0][1], z_list[-1])
    p2 = (points[0, 1][0], points[0, 1][1], z_list[-1])
    p3 = (points[1, 0][0], points[1, 0][1], z_list[-1])
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-Z2')

    p1 = (points[0, 0][0], points[0, 0][1], -z_list[-2])
    p2 = (points[0, 1][0], points[0, 1][1], -z_list[-2])
    p3 = (points[1, 0][0], points[1, 0][1], -z_list[-2])
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-Z-1')

    p1 = (points[0, 0][0], points[0, 0][1], -z_list[-1])
    p2 = (points[0, 1][0], points[0, 1][1], -z_list[-1])
    p3 = (points[1, 0][0], points[1, 0][1], -z_list[-1])
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-Z-2')

    p1 = (points[0, 0][0], points[0, 0][1], 0.0)
    p2 = (points[2, 0][0], points[2, 0][1], 0.0)
    p3 = (points[0, 0][0], points[0, 0][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-T0')

    p1 = (points[0, 2][0], points[0, 2][1], 0.0)
    p2 = (points[2, 2][0], points[2, 2][1], 0.0)
    p3 = (points[0, 2][0], points[0, 2][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-T1')

    p1 = (points[0, 3][0], points[0, 3][1], 0.0)
    p2 = (points[2, 3][0], points[2, 3][1], 0.0)
    p3 = (points[0, 3][0], points[0, 3][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-T2')

    p1 = (points[0, 2][0], -points[0, 2][1], 0.0)
    p2 = (points[2, 2][0], -points[2, 2][1], 0.0)
    p3 = (points[0, 2][0], -points[0, 2][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-T-1')

    p1 = (points[0, 3][0], -points[0, 3][1], 0.0)
    p2 = (points[2, 3][0], -points[2, 3][1], 0.0)
    p3 = (points[0, 3][0], -points[0, 3][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-T-2')

    cylinder = Cylinder((0, 0, 0), (0, 0, 1), points[2, 0, 0])
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if cylinder.is_point_on_cylinder(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-OUTER')


def set_section_common(p):
    set_name = 'SET-CELL-GRAIN'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-GRAIN', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'SET-CELL-INSULATION'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-INSULATION', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'SET-CELL-GLUE-A'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-GLUE', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'COHESIVE-ELEMENTS-GRAIN-INSULATION'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-CZM', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)


if __name__ == "__main__":
    epsilon = 0.95
    n = 9
    beta = math.pi / n
    zeta = beta * 2.0 + 3.0 * math.pi / 180.0

    radius_insulation_thickness = 3.0
    radius_gap = 4.0
    shell_insulation_thickness = 10.0
    shell_thickness = 30.0

    d = (1767.5 - radius_insulation_thickness) * 2.0
    e = 862.9 - radius_insulation_thickness

    x0 = 500.0

    theta_insulation_thickness = 3.0
    theta_gap = 9.0

    block_length = 1229.0
    block_insulation_thickness = 3.0
    block_gap = 18.0
    block_number = 2
    z_list = get_z_list(block_length, block_insulation_thickness, block_gap, block_number)

    element_size = 40

    first_block_height = 1391.0
    shell_insulation_ref_z = 407.581146

    if not ABAQUS_ENV:
        points, lines, faces = geometries(d, x0, beta, [0, 100, 100, 100], [0, 50, 50])
        plot_geometries(points, lines, faces)

    if ABAQUS_ENV:
        Mdb()
        model = mdb.models['Model-1']
        model.setValues(absoluteZero=-273.15)

        size = '1'

        set_material(model.Material(name='MATERIAL-GRAIN'), load_json('material_grain_prony.json'))
        set_material(model.Material(name='MATERIAL-INSULATION'), load_json('material_insulation.json'))
        set_material(model.Material(name='MATERIAL-GLUE'), load_json('material_glue_prony.json'))
        set_material(model.Material(name='MATERIAL-SHELL'), load_json('material_shell.json'))
        set_material(model.Material(name='MATERIAL-CZM'), load_json('material_czm.json'))

        model.HomogeneousSolidSection(name='SECTION-GRAIN', material='MATERIAL-GRAIN', thickness=None)
        model.HomogeneousSolidSection(name='SECTION-INSULATION', material='MATERIAL-INSULATION', thickness=None)
        model.HomogeneousSolidSection(name='SECTION-GLUE', material='MATERIAL-GLUE', thickness=None)
        model.HomogeneousSolidSection(name='SECTION-SHELL', material='MATERIAL-SHELL', thickness=None)
        model.CohesiveSection(name='SECTION-CZM', material='MATERIAL-CZM', response=TRACTION_SEPARATION, outOfPlaneThickness=None)

        block_dimension = {
            'z_list': [0, block_length / 2 - block_insulation_thickness, block_length / 2],
            'deep': 380.0,
            'x0': x0,
            'length_up': 1039.2,
            'width': 100.0,
            'angle_demolding_1': 1.5,
            'angle_demolding_2': 10.0,
            'fillet_radius': 50.0,
            'a': 50.0,
            'b': 25.0,
            'size': size,
            'index_r': 2,
            'index_t': 2,
            'element_size': element_size
        }

        points, lines, faces = geometries(d, x0, beta, [0, 3], [0, 9, 3])
        # p_block = create_part_block(model, 'PART-BLOCK', points, lines, faces, block_dimension)

        gap_dimension = deepcopy(block_dimension)
        gap_dimension['z_list'] = [0, block_length / 2 - block_insulation_thickness, block_length / 2, block_length / 2 + block_gap / 2]
        gap_dimension['index_r'] = 2
        gap_dimension['index_t'] = 3
        # p_gap = create_part_gap(model, 'PART-GAP', points, lines, faces, gap_dimension)

        penult_block_dimension = deepcopy(block_dimension)
        p_block_penult = create_part_block_penult(model, 'PART-BLOCK-PENULT', points, lines, faces, penult_block_dimension)

        penult_gap_dimension = deepcopy(gap_dimension)
        p_gap_penult = create_part_gap_penult(model, 'PART-GAP-PENULT', points, lines, faces, penult_gap_dimension)

        points, lines, faces = geometries(d, x0, beta, [0, 3, 300], [0, 9, 3])
        front_ref_length = 509.0
        first_block_dimension = deepcopy(block_dimension)
        first_block_dimension['z_list'] = [0, front_ref_length, front_ref_length + block_insulation_thickness]
        first_block_dimension['index_r'] = 3
        first_block_dimension['index_t'] = 3

        first_block_dimension['r_front'] = 460.0
        first_block_dimension['length_front'] = 1500.0
        first_block_dimension['p0'] = (-1207.5, 794)
        first_block_dimension['theta0_deg'] = 90.0
        first_block_dimension['p3'] = (-350, 1762.5)
        first_block_dimension['theta3_deg'] = 0.0
        first_block_dimension['r1'] = 929.4
        first_block_dimension['r2'] = 1524.0
        first_block_dimension['r3'] = 655.2
        first_block_dimension['theta_in_deg'] = 0.16

        # p_block_front = create_part_block_front(model, 'PART-BLOCK-FRONT', points, lines, faces, first_block_dimension)
        #
        # first_gap_dimension = deepcopy(first_block_dimension)
        # first_gap_dimension['z_list'] = [0, front_ref_length, front_ref_length + block_insulation_thickness, front_ref_length + block_insulation_thickness + block_gap / 2]
        # p_gap_front = create_part_gap_front(model, 'PART-GAP-FRONT', points, lines, faces, first_gap_dimension)
