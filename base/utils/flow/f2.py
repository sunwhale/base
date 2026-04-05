# -*- coding: utf-8 -*-
"""

"""
import math
import os
import sys
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

FLOW_PATH = r'F:\Github\base\base\utils\flow'
# FLOW_PATH = r'/home/dell/base/base/utils/flow'

try:
    if os.path.isfile(sys.argv[3]):
        FLOW_PATH = os.path.dirname(sys.argv[3])
except:
    pass

sys.path.insert(0, FLOW_PATH)

from utils import ABAQUS_ENV, Circle3D, Counter, Cylinder, Line2D, Plane, calc_arc, degrees_to_radians, find_duplicates, geometries, geometries_hex, get_direction, get_same_volume_cells, get_z_list, is_unicode_all_uppercase, line_circle_intersection, \
    load_json, min_difference, mirror_y_axis, plot_geometries, plot_geometries_hex, plot_three_arcs, polar_to_cartesian, radians_to_degrees, rotate_point_around_origin_2d, rotate_point_around_vector, set_material, set_obj, solve_three_arcs, \
    combine_surfaces, major_version, get_common_faces_between_sets, get_same_area_faces, generate_part_mesh, create_face_set_from_surface, insert_COH3D8_at_face_set, vertices_in_cells, is_cell_in_set, get_faces_of_p_remove_given_surface_names, \
    get_cells_adjacent_to_set_and_remove_set_names, ignore_common_edges_of_faces, rotate_point_around_axis

PEN = 1e4
TOL = 1e-6


def create_sketch_cross_section(model, sketch_name, points, index_r, index_t):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 0], point2=points[index_r, 0]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[index_r, 0], point2=points[index_r, index_t], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[index_r, index_t], point2=points[0, index_t]))
    geom_list.append(s.Line(point1=points[0, index_t], point2=points[0, 0]))
    return s


def create_sketch_burn_x0(model, sketch_name, x0, PEN, burn_offset=0.0):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)

    p1 = [0.0, 0.0]
    p2 = [x0 + burn_offset, 0.0]
    p3 = [x0 + burn_offset, PEN]
    p4 = [0, PEN]

    s.Line(point1=p1, point2=p2)
    s.Line(point1=p2, point2=p3)
    s.Line(point1=p3, point2=p4)
    s.Line(point1=p4, point2=p1)

    return s


def create_sketch_slot(model, sketch_name, x0, deep, a, b, angle_demolding_1, n, r_cut, burn_offset=0.0):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = [x0 + deep, 0.0]
    p1 = [x0 + deep, -a]
    p2 = [x0 + deep + b, 0.0]
    e1 = s.EllipseByCenterPerimeter(center=center, axisPoint1=p1, axisPoint2=p2)
    l1 = Line2D(p1, np.tan(degrees_to_radians(angle_demolding_1)))
    l2 = Line2D([x0 + deep - r_cut, 0.0], [x0 + deep - r_cut, 1.0])
    p3 = l1.get_intersection(l2)
    p4 = [p3[0], 0.0]

    s.Line(point1=p1, point2=p3)
    s.Line(point1=p3, point2=p4)
    s.Line(point1=center, point2=p2)
    s.autoTrimCurve(curve1=e1, point1=[x0 + deep, a])
    s.Line(point1=p4, point2=center)

    if burn_offset > 0:
        s.offset(distance=burn_offset, objectList=(s.geometry[4], s.geometry[7]), side=RIGHT)
        s.Line(point1=s.vertices[3].coords, point2=s.vertices[7].coords)
        s.Line(point1=s.vertices[5].coords, point2=s.vertices[8].coords)
        s.delete(objectList=(s.geometry[4], s.geometry[7]))

    center_line = s.ConstructionLine(point1=(x0 + deep - r_cut, -1e4), point2=(x0 + deep - r_cut, 1e4))
    geom_list = []
    for g in s.geometry.values():
        geom_list.append(g)
    s.rotate(centerPoint=(0.0, 0.0), angle=180.0 / n, objectList=geom_list)
    s.assignCenterline(line=center_line)

    if burn_offset > 0:
        p1p = s.vertices[6].coords
        p2p = s.vertices[8].coords
    else:
        p1p = rotate_point_around_origin_2d(p1, degrees_to_radians(180.0 / n))
        p2p = rotate_point_around_origin_2d(p2, degrees_to_radians(180.0 / n))
    s.Spot(point=p1p)
    s.Spot(point=p2p)

    return s, p1p, p2p


def create_sketch_front_outer(model, sketch_name, t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list, PEN):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)

    result = solve_three_arcs(p0, theta0_deg, p3, theta3_deg, r1, r2, r3)
    l1 = Line2D(p3, np.tan(degrees_to_radians(theta_in_deg)))
    l2 = Line2D([0.0, points[index_r, 0, 0]], [1.0, points[index_r, 0, 0]])
    l3 = Line2D((z_list[-1], 0.0), (z_list[-1], 1.0))
    if l1.get_intersection(l2)[0] > l1.get_intersection(l3)[0]:
        p4 = l1.get_intersection(l3)
        p5 = (PEN, p4[1])
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

    s.ArcByCenterEnds(center=c1, point1=p0, point2=p1, direction=get_direction(delta1))
    s.ArcByCenterEnds(center=c2, point1=p1, point2=p2, direction=get_direction(delta2))
    s.ArcByCenterEnds(center=c3, point1=p2, point2=p3, direction=get_direction(delta3))
    s.Line(point1=p0, point2=(p0[0], 1))
    s.Line(point1=(p0[0], 1), point2=(-PEN, 1))
    s.Line(point1=(-PEN, 1), point2=(-PEN, PEN))
    s.Line(point1=(-PEN, PEN), point2=(p5[0], PEN))
    s.Line(point1=(p5[0], PEN), point2=p5)
    s.Line(point1=p5, point2=p4)
    s.Line(point1=p3, point2=p4)
    center_line = s.ConstructionLine(point1=(0.0, 0.0), point2=(PEN, 0.0))
    s.assignCenterline(line=center_line)

    return s, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3


def create_sketch_behind_outer(model, sketch_name, t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list, PEN):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)

    result = solve_three_arcs(p0, theta0_deg, p3, theta3_deg, r1, r2, r3)
    l1 = Line2D(p3, np.tan(degrees_to_radians(-theta_in_deg)))
    l2 = Line2D([0.0, points[index_r, 0, 0]], [1.0, points[index_r, 0, 0]])
    l3 = Line2D((-z_list[-1], 0.0), (-z_list[-1], 1.0))
    if l1.get_intersection(l2)[0] < l1.get_intersection(l3)[0]:
        p4 = l1.get_intersection(l3)
        p5 = (-PEN, p4[1])
    else:
        p4 = l1.get_intersection(l2)
        p5 = (-z_list[-1], p4[1])

    p1 = result['p1']
    p2 = result['p2']
    c1 = result['c1']
    c2 = result['c2']
    c3 = result['c3']
    delta1 = result['delta1']
    delta2 = result['delta2']
    delta3 = result['delta3']

    s.ArcByCenterEnds(center=c1, point1=p0, point2=p1, direction=get_direction(delta1))
    s.ArcByCenterEnds(center=c2, point1=p1, point2=p2, direction=get_direction(delta2))
    s.ArcByCenterEnds(center=c3, point1=p2, point2=p3, direction=get_direction(delta3))
    s.Line(point1=p0, point2=(p0[0], 1))
    s.Line(point1=(p0[0], 1), point2=(PEN, 1))
    s.Line(point1=(PEN, 1), point2=(PEN, PEN))
    s.Line(point1=(PEN, PEN), point2=(p5[0], PEN))
    s.Line(point1=(p5[0], PEN), point2=p5)
    s.Line(point1=p5, point2=p4)
    s.Line(point1=p3, point2=p4)
    center_line = s.ConstructionLine(point1=(0.0, 0.0), point2=(PEN, 0.0))
    s.assignCenterline(line=center_line)

    return s, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3


def create_sketch_behind_outer_offset(model, sketch_name, t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)
    geom_list = []
    geom_list.append(s.Line(point1=(p0[0], x0), point2=p0))
    geom_list.append(s.ArcByCenterEnds(center=c1, point1=p0, point2=p1, direction=get_direction(delta1)))
    geom_list.append(s.ArcByCenterEnds(center=c2, point1=p1, point2=p2, direction=get_direction(delta2)))
    geom_list.append(s.ArcByCenterEnds(center=c3, point1=p2, point2=p3, direction=get_direction(delta3)))
    geom_list.append(s.Line(point1=p3, point2=p4))
    geom_list.append(s.Line(point1=p4, point2=p5))
    # 逆序循环，保证轮廓线从外到内的顺序排列
    for i in range(index_r - 1, 0, -1):
        s.offset(distance=float(points[index_r, 0][0] - points[i, 0][0]), objectList=geom_list, side=LEFT)

    return s


def create_sketch_front_outer_offset(model, sketch_name, t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)
    geom_list = []
    geom_list.append(s.Line(point1=(p0[0], x0), point2=p0))
    geom_list.append(s.ArcByCenterEnds(center=c1, point1=p0, point2=p1, direction=get_direction(delta1)))
    geom_list.append(s.ArcByCenterEnds(center=c2, point1=p1, point2=p2, direction=get_direction(delta2)))
    geom_list.append(s.ArcByCenterEnds(center=c3, point1=p2, point2=p3, direction=get_direction(delta3)))
    geom_list.append(s.Line(point1=p3, point2=p4))
    geom_list.append(s.Line(point1=p4, point2=p5))
    # 逆序循环，保证轮廓线从外到内的顺序排列
    for i in range(index_r - 1, 0, -1):
        s.offset(distance=float(points[index_r, 0][0] - points[i, 0][0]), objectList=geom_list, side=RIGHT)
    return s


def create_sketch_penult_inner(model, sketch_name, t, x0, deep, block_length, z_list, block_insulation_thickness_z, a, b, PEN):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)

    p0 = [block_length / 2.0 + z_list[-1] - z_list[-2], x0 + deep + b - 1.0]
    p1 = [block_length / 2.0, x0 + deep + b - 1.0]
    p2 = [block_length / 2.0 - block_insulation_thickness_z, x0 + deep + b - 1.0]
    l1 = Line2D(p2, np.tan(degrees_to_radians(45.0)))
    l2 = Line2D([0.0, 0.0], [1.0, 0.0])
    p3 = l1.get_intersection(l2)
    p4 = [block_length / 2.0 + z_list[-1] - z_list[-2], 0.0]

    s.Line(point1=p0, point2=p1)
    s.Line(point1=p1, point2=p2)
    s.Line(point1=p2, point2=p3)
    s.Line(point1=p3, point2=p4)
    s.Line(point1=p4, point2=p0)

    center_line = s.ConstructionLine(point1=(0.0, 0.0), point2=(PEN, 0.0))
    s.assignCenterline(line=center_line)

    return s


def create_sketch_behind_inner(model, sketch_name, t, x0, deep, a, b, PEN, burn_offset=0.0):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)

    p1 = [-PEN, x0 + deep + b + burn_offset]
    p2 = [PEN, x0 + deep + b + burn_offset]
    p3 = [PEN, 0]
    p4 = [-PEN, 0]

    s.Line(point1=p1, point2=p2)
    s.Line(point1=p2, point2=p3)
    s.Line(point1=p3, point2=p4)
    s.Line(point1=p4, point2=p1)

    center_line = s.ConstructionLine(point1=(0.0, 0.0), point2=(PEN, 0.0))
    s.assignCenterline(line=center_line)

    return s


def create_sketch_gap_z_front_behind(model, sketch_name, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 2], point2=points[3, 2]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[3, 2], point2=points[3, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[3, 3], point2=points[0, 3]))
    geom_list.append(s.Line(point1=points[0, 3], point2=points[0, 2]))

    return s


def create_sketch_gap_z(model, sketch_name, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 2], point2=points[2, 2]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[2, 2], point2=points[2, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[2, 3], point2=points[0, 3]))
    geom_list.append(s.Line(point1=points[0, 3], point2=points[0, 2]))

    return s


def create_sketch_gap_t_front_behind(model, sketch_name, t, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, gridSpacing=100.0, transform=t)

    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 0], point2=points[3, 0]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[3, 0], point2=points[3, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[3, 3], point2=points[0, 3]))
    geom_list.append(s.Line(point1=points[0, 3], point2=points[0, 0]))

    return s


def create_sketch_gap_t(model, sketch_name, t, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, gridSpacing=100.0, transform=t)

    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 0], point2=points[2, 0]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[2, 0], point2=points[2, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[2, 3], point2=points[0, 3]))
    geom_list.append(s.Line(point1=points[0, 3], point2=points[0, 0]))

    return s


def get_local_variables(dimension):
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
    insert_czm = dimension['insert_czm']
    burn_offset = dimension['burn_offset']

    return (z_list,
            deep,
            x0,
            length_up,
            width,
            angle_demolding_1,
            angle_demolding_2,
            fillet_radius,
            a,
            b,
            size,
            index_r,
            index_t,
            element_size,
            insert_czm,
            burn_offset)


def get_local_variables_front(dimension):
    r_cut = dimension['r_cut']
    length_front = dimension['length_front']
    p0 = dimension['p0']
    theta0_deg = dimension['theta0_deg']
    p3 = dimension['p3']
    theta3_deg = dimension['theta3_deg']
    theta_in_deg = dimension['theta_in_deg']
    beta = dimension['beta']
    r1 = dimension['r1']
    r2 = dimension['r2']
    r3 = dimension['r3']

    return (r_cut,
            length_front,
            p0,
            theta0_deg,
            p3,
            theta3_deg,
            theta_in_deg,
            beta,
            r1,
            r2,
            r3)


def create_part_base(model, part_name, sketch, length):
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    d = p.datums

    p.BaseSolidExtrude(sketch=sketch, depth=length / 2.0)

    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    xy_plane_z1 = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=length / 2.0)

    return p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis, xy_plane_z1


def part_partition_cross_section(model, p, d, x_axis, z_axis, index_t, index_r):
    s_cross_section_partition = model.ConstrainedSketch(name='SKETCH-CROSS-SECTION-PARTITION', sheetSize=200.0)
    center = (0, 0)
    geom_list = []

    # 面切割
    # 拾取被切割平面上的线段，同一个theta
    for i in range(1, index_t):
        geom_list.append(s_cross_section_partition.Line(point1=points[0, i], point2=points[index_r, i]))
    # 拾取被切割平面上的线段，同一个r
    for i in range(1, index_r):
        geom_list.append(s_cross_section_partition.ArcByCenterEnds(center=center, point1=points[i, 0], point2=points[i, index_t], direction=COUNTERCLOCKWISE))

    p_faces = p.faces.getByBoundingBox(0, 0, 0, PEN, PEN, TOL)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketchOrientation=BOTTOM, sketch=s_cross_section_partition)

    # 体切割
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


def part_partition_z(p, d, z_list):
    xy_plane_z = {}
    for i in range(1, len(z_list) - 1):
        xy_plane_z[i] = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=z_list[i])
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z[i].id], cells=p.cells)
    return xy_plane_z


def create_part_block(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    z_list, deep, x0, length_up, width, angle_demolding_1, angle_demolding_2, fillet_radius, a, b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables(dimension)

    # 基本参数
    origin = (0.0, 0.0, 0.0)
    length = z_list[-1] * 2.0
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-CROSS-SECTION
    s_cross_section = create_sketch_cross_section(model, 'SKETCH-CROSS-SECTION', points, index_r, index_t)

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis, xy_plane_z1 = create_part_base(model, part_name, s_cross_section, length)

    # 截面剖分
    part_partition_cross_section(model, p, d, x_axis, z_axis, index_t, index_r)

    # z剖分
    part_partition_z(p, d, z_list)

    # 创建集合（体）
    set_names = create_block_sets_common(p, faces, dimension)

    # 星槽切割
    p1p = cut_slot(p, d, x0, deep, a, b, angle_demolding_1, n, burn_offset, PEN, xy_plane, y_axis)

    # 镜像
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

    # 创建面
    create_block_surface_common(p, points, dimension)

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT'], 'SURFACE-INNER')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 更新集合（体），处理镜像
    create_block_sets_same_volume(p)

    # 创建集合（面），粘接界面
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')

    # 剖分
    part_partition_p1p(p, d, p1p)

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    # 插入内聚力单元
    if insert_czm:
        insert_COH3D8_at_face_set(p, 'SET-FACES-GRAIN-INSULATION', 'COHESIVE-ELEMENTS-GRAIN-INSULATION')

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_gap(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    z_list, deep, x0, length_up, width, angle_demolding_1, angle_demolding_2, fillet_radius, a, b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables(dimension)

    # 基本参数
    origin = (0.0, 0.0, 0.0)
    length = z_list[-2] * 2.0
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-GAP-Z
    s_gap_z = create_sketch_gap_z(model, 'SKETCH-GAP-Z', points)

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis, xy_plane_z1 = create_part_base(model, part_name, s_gap_z, length)

    # SKETCH-GAP-T
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, length / 2.0))
    s_gap_t = create_sketch_gap_t(model, 'SKETCH-GAP-T', t, points)

    # 生成基础体
    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_t, depth=(z_list[-1] - z_list[-2]), flipExtrudeDirection=OFF)

    # z剖分
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z1.id], cells=p.cells)
    cut_edges = (
        p.edges.findAt((lines['02-12'][3][0], lines['02-12'][3][1], length / 2.0)),
    )
    p.PartitionCellByExtrudeEdge(line=d[z_axis.id], cells=p.cells, edges=cut_edges, sense=FORWARD)

    # 星槽切割
    p1p = cut_slot(p, d, x0, deep, a, b, angle_demolding_1, n, burn_offset, PEN, xy_plane, y_axis)

    # 镜像
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

    # 创建面
    create_gap_surface_common(p, points, dimension)

    p1 = [x0 + deep + b, 0.0]
    x1 = p1[0] * np.cos(degrees_to_radians(180.0 / n))
    y1 = p1[0] * np.sin(degrees_to_radians(180.0 / n))
    p_faces = p.faces.getByBoundingBox(0, TOL, 0, x1 * 1.1, y1, z_list[-1])
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-SLOT')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT'], 'SURFACE-INNER')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体）
    set_name = 'SET-CELL-GLUE-A'
    p.Set(cells=p.cells, name=set_name)

    # 剖分
    part_partition_p1p(p, d, p1p)

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_front(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    z_list, deep, x0, length_up, width, angle_demolding_1, angle_demolding_2, fillet_radius, a, b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables(dimension)
    r_cut, length_front, p0, theta0_deg, p3, theta3_deg, theta_in_deg, beta, r1, r2, r3 = get_local_variables_front(dimension)

    # 基本参数
    origin = (0.0, 0.0, 0.0)
    length = z_list[-1] * 2.0
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-CROSS-SECTION
    s_cross_section = create_sketch_cross_section(model, 'SKETCH-CROSS-SECTION', points, index_r, index_t)

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis, xy_plane_z1 = create_part_base(model, part_name, s_cross_section, length)

    # 头部药块额外拉伸
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cross_section, depth=length_front, flipExtrudeDirection=ON)

    # 旋转切割头部外轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_front_outer, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_front_outer(model, 'SKETCH-FRONT-OUTER', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list, PEN)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_front_outer, angle=360.0, flipRevolveDirection=ON)

    # 草图切割环向面
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_front_outer_offset = create_sketch_front_outer_offset(model, 'SKETCH-FRONT-OUTER-OFFSET', t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3)

    # 创建面SURFACE-OUTER
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for g in s_front_outer_offset.geometry.values()[:6]:
        z, x = g.pointOn
        point = (x, 0.0, z)
        angle = beta / 2.0
        point_rot = rotate_point_around_vector(point, [0, 0, 1], angle)
        p_faces += p.faces.findAt((point_rot,))
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    # 面切割
    g = s_front_outer_offset.geometry
    faces_xz_plane = {}
    for i in range(1, index_r):
        faces_xz_plane[i] = []
        for j in [2, 3, 4, 5, 6, 7]:
            pa = (np.array(g[j + 6 * (i - 1)].pointOn) + np.array(g[j + 6 * i].pointOn)) / 2.0
            faces_xz_plane[i].append(pa)
            s_front_outer_offset.Spot(point=pa)

    for i in range(1, index_r):
        for j in [3, 4, 5, 6, 7]:
            pa = g[6 * (i - 1) + j].getVertices()[0].coords
            pb = g[6 * i + j].getVertices()[0].coords
            s_front_outer_offset.Line(point1=pa, point2=pb)

    p_faces = p.faces.getByBoundingBox(0, 0, -PEN, PEN, TOL, PEN)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketch=s_front_outer_offset)

    # 基于p4点所在的半径拾取sweep_edge
    x, y = polar_to_cartesian(p4[1], TOL)
    # x = min(x, points[index_r, 0][0])
    sweep_edge = p.edges.findAt((x, y, z_list[-1]))

    # 拾取主体弧线
    partition_edges = []
    for g in s_front_outer_offset.geometry.values()[2:index_r * 6]:
        z, x = g.pointOn
        # p.DatumPointByCoordinate(coords=(x, 0.0, z))
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # 基于p4点所在的半径拾取sweep_edge
    x, y = polar_to_cartesian(p4[1], TOL)
    x = min(x, points[index_r, 0][0])
    sweep_edge = p.edges.findAt((x, y, z_list[-1]))

    # 拾取分段连线
    partition_edges = []
    for g in s_front_outer_offset.geometry.values()[index_r * 6:]:
        z, x = g.pointOn
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # 建立不同z的xy_plane
    xy_plane_z = {}
    for i in range(1, len(z_list)):
        xy_plane_z[i] = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=z_list[i])

    # SKETCH-CROSS-SECTION-PARTITION
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z[len(z_list) - 1].id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, z_list[-1]))
    s_cross_section_partition = model.ConstrainedSketch(name='SKETCH-CROSS-SECTION-PARTITION', sheetSize=200.0, transform=t)
    geom_list = []
    # 拾取被切割平面上的线段，同一个theta
    for i in range(1, index_t):
        geom_list.append(s_cross_section_partition.Line(point1=points[0, i], point2=points[index_r, i]))

    # Partition
    # p_faces = p.faces.getByBoundingBox(0, 0, z_list[-1], PEN, PEN, PEN)
    # p.PartitionFaceBySketch(sketchUpEdge=d[y_axis.id], faces=p_faces, sketch=s_cross_section_partition)

    # 建立平面，通过三个点：同一个theta的两个点和z方向上偏移1.0的点，保证平面法向量朝外，用该平面切割p.cells
    t_planes = []
    for j in range(1, index_t):
        t_planes.append(p.DatumPlaneByThreePoints(point1=(points[0, j, 0], points[0, j, 1], 0.0), point2=(points[-1, j, 0], points[-1, j, 1], 0.0), point3=(points[0, j, 0], points[0, j, 1], 1.0)))
    for t_plane in t_planes:
        p.PartitionCellByDatumPlane(datumPlane=d[t_plane.id], cells=p.cells)

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

    # 星槽切割
    s_slot, p1p, p2p = create_sketch_slot(model, 'SKETCH-FRONT-SLOT', x0, deep, a, b, angle_demolding_1, n, r_cut, burn_offset)

    p1p = cut_slot(p, d, x0, deep, a, b, angle_demolding_1, n, burn_offset, PEN, xy_plane, y_axis)

    # 切割头部燃道
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, flipExtrudeDirection=ON)
    p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, angle=90.0, flipRevolveDirection=OFF)

    # SKETCH-BURN-X0
    s_burn_x0 = create_sketch_burn_x0(model, 'SKETCH-BURN-X0', x0, PEN, burn_offset)
    # x0方向燃面退移
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=ON)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=OFF)

    for i in range(1, len(z_list) - 1):
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z[i].id], cells=p.cells)

    # 建立INSULATION集合
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-GRAIN', ['SET-CELL-GRAIN'])
    if cells:
        p.Set(cells=cells, name='SET-CELL-INSULATION')

    # 建立GLUE集合
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-INSULATION', ['SET-CELL-GRAIN', 'SET-CELL-INSULATION'])
    if cells:
        p.Set(cells=cells, name='SET-CELL-GLUE-A')

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

    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    # 拾取内部切割后的轮廓曲线
    p_edges = []
    for z_center in z_centers:
        edge = p.edges.findAt((p1p[0], p1p[1], z_center))
        if edge is not None:
            p_edges.append(edge)
        p.DatumPointByCoordinate(coords=(p1p[0], p1p[1], z_center))

    point1 = (x0 + deep - r_cut, 0.0)
    point2 = (x0 + deep - r_cut, 1.0)
    point3 = rotate_point_around_origin_2d(point1, beta / 2.0)
    point4 = rotate_point_around_origin_2d(point2, beta / 2.0)
    point5 = rotate_point_around_axis((p1p[0], p1p[1], 0.0), (point3[0], point3[1], 0.0), (point4[0], point4[1], 0.0), TOL)
    p.DatumPointByCoordinate(coords=point5)

    edge = p.edges.findAt(point5)
    if edge is not None:
        p_edges.append(edge)

    if p_edges:
        p.PartitionCellByExtrudeEdge(line=d[y_axis.id], cells=p.cells, edges=p_edges, sense=REVERSE)

    create_block_surface_common(p, points, dimension)

    p1 = [x0 + deep + b, 0.0]
    x1 = p1[0] * np.cos(degrees_to_radians(180.0 / n))
    y1 = p1[0] * np.sin(degrees_to_radians(180.0 / n))
    p_faces = p.faces.getByBoundingBox(0, TOL, -r_cut - b, x1 * 1.1, y1, length / 2.0)
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-SLOT')

    # xz_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=180.0 / n / 2.0)
    # p.PartitionCellByDatumPlane(datumPlane=d[xz_plane_rot.id], cells=p.cells)

    if size == '1':
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
        # xz_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=-180.0 / n / 2.0)
        # p.PartitionCellByDatumPlane(datumPlane=d[xz_plane_rot.id], cells=p.cells)

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    given_surface_names.remove('SURFACE-OUTER')
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT'], 'SURFACE-INNER')

    create_face_set_from_surface(p)

    create_block_sets_same_volume(p)

    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')

    generate_part_mesh(p, element_size=element_size)

    if insert_czm:
        insert_COH3D8_at_face_set(p, 'SET-FACES-GRAIN-INSULATION', 'COHESIVE-ELEMENTS-GRAIN-INSULATION')

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
    burn_offset = dimension['burn_offset']
    r_cut = dimension['r_cut']
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
    PEN = 1e4
    TOL = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-GAP-Z
    s_gap_z = create_sketch_gap_z_front_behind(model, 'SKETCH-GAP-Z-FRONT-BEHIND', points)

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
    s_front_outer, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_front_outer(model, 'SKETCH-FRONT-OUTER', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list, PEN)
    # 旋转切割头部外轮廓
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_front_outer, angle=360.0, flipRevolveDirection=ON)

    # 草图切割环向面
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_front_outer_offset = create_sketch_front_outer_offset(model, 'SKETCH-FRONT-OUTER-OFFSET', t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3)

    # SKETCH-GAP-T
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, length / 2.0))
    s_gap_t = create_sketch_gap_t_front_behind(model, 'SKETCH-GAP-T-FRONT-BEHIND', t, points)

    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_t, depth=(z_list[-1] - z_list[-2]), flipExtrudeDirection=OFF)

    # 旋转切割头部外轮廓
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_front_outer, angle=360.0, flipRevolveDirection=ON)

    # Partition
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z1.id], cells=p.cells)

    point1 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], length / 2.0))
    point2 = p.DatumPointByCoordinate(coords=(lines['02-12'][2][0], lines['02-12'][2][1], length / 2.0))
    point3 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], 0.0))
    partition_plane = p.DatumPlaneByThreePoints(point1=d[point1.id], point2=d[point2.id], point3=d[point3.id])
    p.PartitionCellByDatumPlane(datumPlane=d[partition_plane.id], cells=p.cells)

    # SKETCH-FRONT-CUT
    s_slot, p1p, p2p = create_sketch_slot(model, 'SKETCH-FRONT-SLOT', x0, deep, a, b, angle_demolding_1, n, r_cut, burn_offset)

    # 切割头部燃道
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, flipExtrudeDirection=ON)
    p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, angle=90.0, flipRevolveDirection=OFF)

    # SKETCH-BURN-X0
    s_burn_x0 = create_sketch_burn_x0(model, 'SKETCH-BURN-X0', x0, PEN, burn_offset)
    # x0方向燃面退移
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=ON)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=OFF)

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
    p_faces = p.faces.getByBoundingBox(0, TOL, -r_cut - b, x1 * 1.1, y1, z_list[-1])
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-SLOT')

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT'], 'SURFACE-INNER')

    create_face_set_from_surface(p)

    # Partition
    p1 = [x0 + deep, -a]
    offset = p1[0] * np.cos(degrees_to_radians(180.0 / n)) - p1[1] * np.sin(degrees_to_radians(180.0 / n))
    yz_plane_2 = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=offset)
    p.PartitionCellByDatumPlane(datumPlane=d[yz_plane_2.id], cells=p.cells.getByBoundingBox(0, -PEN, 0, PEN, PEN, PEN))
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    # 拓扑层面忽略外表面的公共边
    p_faces = p.surfaces['SURFACE-OUTER'].faces.getByBoundingBox(0, -PEN, -PEN, PEN, PEN, 0)
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
    insert_czm = dimension['insert_czm']
    burn_offset = dimension['burn_offset']
    origin = (0.0, 0.0, 0.0)
    length = z_list[-1] * 2.0
    PEN = 1e4
    TOL = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-CROSS-SECTION
    s_cross_section = create_sketch_cross_section(model, 'SKETCH-CROSS-SECTION', points, index_r, index_t)

    # Extrude
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    d = p.datums

    p.BaseSolidExtrude(sketch=s_cross_section, depth=length / 2.0)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)

    # SKETCH-CROSS-SECTION-PARTITION
    s_cross_section_partition = model.ConstrainedSketch(name='SKETCH-CROSS-SECTION-PARTITION', sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    # 拾取被切割平面上的线段，同一个theta
    for i in range(1, index_t):
        geom_list.append(s_cross_section_partition.Line(point1=points[0, i], point2=points[index_r, i]))
    # 拾取被切割平面上的线段，同一个r
    for i in range(1, index_r):
        geom_list.append(s_cross_section_partition.ArcByCenterEnds(center=center, point1=points[i, 0], point2=points[i, index_t], direction=COUNTERCLOCKWISE))

    # Partition
    p_faces = p.faces.getByBoundingBox(0, 0, 0, PEN, PEN, TOL)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketchOrientation=BOTTOM, sketch=s_cross_section_partition)

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

    set_names = create_block_sets_common(p, faces, dimension)

    p1p = cut_slot(p, d, x0, deep, a, b, angle_demolding_1, n, burn_offset, PEN, xy_plane, y_axis)

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

    create_block_sets_same_volume(p)

    create_block_surface_common(p, points, dimension)

    p1 = [x0 + deep + b, 0.0]
    x1 = p1[0] * np.cos(degrees_to_radians(180.0 / n))
    y1 = p1[0] * np.sin(degrees_to_radians(180.0 / n))
    p_faces = p.faces.getByBoundingBox(0, TOL, 0, x1 * 1.1, y1, length / 2.0)
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-SLOT')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')

    part_partition_p1p(p, d, p1p)

    # 旋转切割内燃道
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_penult_inner = create_sketch_penult_inner(model, 'SKETCH-PENULT-INNER', t, x0, deep, block_length, z_list, block_insulation_thickness_z, a, b, PEN)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_penult_inner, angle=360.0, flipRevolveDirection=ON)

    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-SLOT-2')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT', 'SURFACE-SLOT-2'], 'SURFACE-INNER')

    create_face_set_from_surface(p)

    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')

    generate_part_mesh(p, element_size=element_size)

    if insert_czm:
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
    burn_offset = dimension['burn_offset']
    origin = (0.0, 0.0, 0.0)
    length = z_list[-2] * 2.0
    PEN = 1e4
    TOL = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-GAP
    s_gap_z = create_sketch_gap_z(model, 'SKETCH-GAP-Z', points)

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
    s_gap_t = create_sketch_gap_t(model, 'SKETCH-GAP-T', t, points)

    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_t, depth=(z_list[-1] - z_list[-2]), flipExtrudeDirection=OFF)

    # Partition
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z1.id], cells=p.cells)
    cut_edges = (
        p.edges.findAt((lines['02-12'][3][0], lines['02-12'][3][1], length / 2.0)),
    )
    p.PartitionCellByExtrudeEdge(line=d[z_axis.id], cells=p.cells, edges=cut_edges, sense=FORWARD)

    p1p = cut_slot(p, d, x0, deep, a, b, angle_demolding_1, n, burn_offset, PEN, xy_plane, y_axis)

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
    p_faces = p.faces.getByBoundingBox(0, TOL, 0, x1 * 1.1, y1, z_list[-1])
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-SLOT')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')

    set_name = 'SET-CELL-GLUE-A'
    p.Set(cells=p.cells, name=set_name)

    part_partition_p1p(p, d, p1p)

    # 旋转切割内燃道
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_penult_inner = create_sketch_penult_inner(model, 'SKETCH-PENULT-INNER', t, x0, deep, block_length, z_list, block_insulation_thickness_z, a, b, PEN)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_penult_inner, angle=360.0, flipRevolveDirection=ON)

    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-SLOT-2')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT', 'SURFACE-SLOT-2'], 'SURFACE-INNER')

    create_face_set_from_surface(p)

    generate_part_mesh(p, element_size=element_size)

    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_behind(model, part_name, points, lines, faces, dimension):
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
    insert_czm = dimension['insert_czm']
    burn_offset = dimension['burn_offset']
    r_cut = dimension['r_cut']
    length_behind = dimension['length_behind']
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
    PEN = 1e4
    TOL = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-CROSS-SECTION
    s_cross_section = create_sketch_cross_section(model, 'SKETCH-CROSS-SECTION', points, index_r, index_t)

    # Extrude
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cross_section, depth=length / 2.0, flipExtrudeDirection=ON)

    # 头部药块额外拉伸
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cross_section, depth=length_behind, flipExtrudeDirection=OFF)

    # 旋转切割头部外轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_outer, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_behind_outer(model, 'SKETCH-BEHIND-OUTER', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list, PEN)

    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_outer, angle=360.0, flipRevolveDirection=ON)

    # 草图切割环向面
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_outer_offset = create_sketch_behind_outer_offset(model, 'SKETCH-BEHIND-OUTER-OFFSET', t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3)

    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for g in s_behind_outer_offset.geometry.values()[:6]:
        z, x = g.pointOn
        point = (x, 0.0, z)
        angle = degrees_to_radians(180.0 / n / 2.0)
        point_rot = rotate_point_around_vector(point, [0, 0, 1], angle)
        p_faces += p.faces.findAt((point_rot,))
        # p.DatumPointByCoordinate(coords=point_rot)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    g = s_behind_outer_offset.geometry
    faces_xz_plane = {}
    for i in range(1, index_r):
        faces_xz_plane[i] = []
        for j in [2, 3, 4, 5, 6, 7]:
            pa = (np.array(g[j + 6 * (i - 1)].pointOn) + np.array(g[j + 6 * i].pointOn)) / 2.0
            faces_xz_plane[i].append(pa)
            s_behind_outer_offset.Spot(point=pa)

    for i in range(1, index_r):
        for j in [3, 4, 5, 6, 7]:
            pa = g[6 * (i - 1) + j].getVertices()[0].coords
            pb = g[6 * i + j].getVertices()[0].coords
            s_behind_outer_offset.Line(point1=pa, point2=pb)

    p_faces = p.faces.getByBoundingBox(0, 0, -PEN, PEN, TOL, PEN)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketch=s_behind_outer_offset)

    # 基于p4点所在的半径拾取sweep_edge
    x, y = polar_to_cartesian(p4[1], TOL)
    # x = min(x, points[index_r, 0][0])
    sweep_edge = p.edges.findAt((x, y, -z_list[-1]))

    # 拾取主体弧线
    partition_edges = []
    for g in s_behind_outer_offset.geometry.values()[2:index_r * 6]:
        z, x = g.pointOn
        # p.DatumPointByCoordinate(coords=(x, 0.0, z))
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # 基于p4点所在的半径拾取sweep_edge
    x, y = polar_to_cartesian(p4[1], TOL)
    x = min(x, points[index_r, 0][0])
    sweep_edge = p.edges.findAt((x, y, -z_list[-1]))

    # 拾取分段连线
    partition_edges = []
    for g in s_behind_outer_offset.geometry.values()[index_r * 6:]:
        z, x = g.pointOn
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # 建立不同z的xy_plane
    xy_plane_z = {}
    for i in range(1, len(z_list)):
        xy_plane_z[i] = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=-z_list[i])

    # SKETCH-CROSS-SECTION-PARTITION
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z[len(z_list) - 1].id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, -z_list[-1]))
    s_cross_section_partition = model.ConstrainedSketch(name='SKETCH-CROSS-SECTION-PARTITION', sheetSize=200.0, transform=t)
    geom_list = []
    # 拾取被切割平面上的线段，同一个theta
    for i in range(1, index_t):
        geom_list.append(s_cross_section_partition.Line(point1=points[0, i], point2=points[index_r, i]))

    # Partition
    # p_faces = p.faces.getByBoundingBox(0, 0, z_list[-1], PEN, PEN, PEN)
    # p.PartitionFaceBySketch(sketchUpEdge=d[y_axis.id], faces=p_faces, sketch=s_cross_section_partition)

    # 建立平面，通过三个点：同一个theta的两个点和z方向上偏移1.0的点，保证平面法向量朝外，用该平面切割p.cells
    t_planes = []
    for j in range(1, index_t):
        t_planes.append(p.DatumPlaneByThreePoints(point1=(points[0, j, 0], points[0, j, 1], 0.0), point2=(points[-1, j, 0], points[-1, j, 1], 0.0), point3=(points[0, j, 0], points[0, j, 1], 1.0)))
    for t_plane in t_planes:
        p.PartitionCellByDatumPlane(datumPlane=d[t_plane.id], cells=p.cells)

    for i in range(1, len(z_list) - 1):
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z[i].id], cells=p.cells)

    # 建立GRAIN集合
    cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for rtz in [
        [0, 0, 0]
    ]:
        cells += p.cells.findAt(((faces[rtz[0], rtz[1]][0], faces[rtz[0], rtz[1]][1], z_centers[rtz[2]]),))
    cells = get_same_volume_cells(p, cells)
    for pa in faces_xz_plane[index_r - 1]:
        cells += p.cells.findAt(((pa[1], 0.0, pa[0]),))
    if cells:
        p.Set(cells=cells, name='SET-CELL-GRAIN')

    # 建立INSULATION集合
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-GRAIN', ['SET-CELL-GRAIN'])
    if cells:
        p.Set(cells=cells, name='SET-CELL-INSULATION')

    # 建立GLUE集合
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-INSULATION', ['SET-CELL-GRAIN', 'SET-CELL-INSULATION'])
    if cells:
        p.Set(cells=cells, name='SET-CELL-GLUE-A')

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

    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    create_block_surface_common(p, points, dimension)

    xz_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=180.0 / n / 2.0)
    p.PartitionCellByDatumPlane(datumPlane=d[xz_plane_rot.id], cells=p.cells)

    if size == '1':
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
        xz_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=-180.0 / n / 2.0)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane_rot.id], cells=p.cells)

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    given_surface_names.remove('SURFACE-OUTER')
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')

    # 旋转切割头部外轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_inner = create_sketch_behind_inner(model, 'SKETCH-BEHIND-INNER', t, x0, deep, a, b, PEN, burn_offset)

    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_inner, angle=360.0, flipRevolveDirection=ON)

    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

    create_face_set_from_surface(p)

    create_block_sets_same_volume(p)

    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')

    generate_part_mesh(p, element_size=element_size)

    if insert_czm:
        insert_COH3D8_at_face_set(p, 'SET-FACES-GRAIN-INSULATION', 'COHESIVE-ELEMENTS-GRAIN-INSULATION')

    set_section_common(p)
    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_gap_behind(model, part_name, points, lines, faces, dimension):
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
    burn_offset = dimension['burn_offset']
    r_cut = dimension['r_cut']
    length_behind = dimension['length_behind']
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
    PEN = 1e4
    TOL = 1e-6
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-GAP-Z
    s_gap_z = create_sketch_gap_z_front_behind(model, 'SKETCH-GAP-Z-FRONT-BEHIND', points)

    # Extrude
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    xy_plane_z1 = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=-length / 2.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_z, depth=length / 2.0, flipExtrudeDirection=ON)

    # 头部药块额外拉伸
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_z, depth=length_behind, flipExtrudeDirection=OFF)

    # 旋转切割头部外轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_outer, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_behind_outer(model, 'SKETCH-BEHIND-OUTER', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list, PEN)

    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_outer, angle=360.0, flipRevolveDirection=ON)

    # 草图切割环向面
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_outer_offset = create_sketch_behind_outer_offset(model, 'SKETCH-BEHIND-OUTER-OFFSET', t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3)

    # SKETCH-GAP-T
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, length / 2.0))
    s_gap_t = create_sketch_gap_t_front_behind(model, 'SKETCH-GAP-T-FRONT-BEHIND', t, points)

    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_t, depth=(z_list[-1] - z_list[-2]), flipExtrudeDirection=ON)

    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_outer, angle=360.0, flipRevolveDirection=ON)

    # Partition
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z1.id], cells=p.cells)

    point1 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], length / 2.0))
    point2 = p.DatumPointByCoordinate(coords=(lines['02-12'][2][0], lines['02-12'][2][1], length / 2.0))
    point3 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], 0.0))
    partition_plane = p.DatumPlaneByThreePoints(point1=d[point1.id], point2=d[point2.id], point3=d[point3.id])
    p.PartitionCellByDatumPlane(datumPlane=d[partition_plane.id], cells=p.cells)

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

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')

    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_inner = create_sketch_behind_inner(model, 'SKETCH-BEHIND-INNER', t, x0, deep, a, b, PEN, burn_offset)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_inner, angle=360.0, flipRevolveDirection=ON)

    # 通过排除法确定内表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

    for name in p.surfaces.keys():
        p.Set(faces=p.surfaces[name].faces, name='SET-' + name)

    create_face_set_from_surface(p)

    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    set_name = 'SET-CELL-GLUE-A'
    p.Set(cells=p.cells, name=set_name)

    generate_part_mesh(p, element_size=element_size)

    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def part_partition_p1p(p, d, p1p):
    # Partition
    # p1 = [x0 + deep, -a]
    # offset = p1[0] * np.cos(degrees_to_radians(180.0 / n)) - p1[1] * np.sin(degrees_to_radians(180.0 / n))
    offset = p1p[0]
    if offset >= p.cells.getBoundingBox()['low'][0]:
        yz_plane_2 = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=offset)
        p.PartitionCellByDatumPlane(datumPlane=d[yz_plane_2.id], cells=p.cells)


def cut_slot(p, d, x0, deep, a, b, angle_demolding_1, n, burn_offset, PEN, xy_plane, y_axis):
    r_cut = x0 + deep
    s_slot, p1p, p2p = create_sketch_slot(model, 'SKETCH-SLOT', x0, deep, a, b, angle_demolding_1, n, r_cut, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, flipExtrudeDirection=ON)

    # SKETCH-BURN-X0
    s_burn_x0 = create_sketch_burn_x0(model, 'SKETCH-BURN-X0', x0, PEN, burn_offset)
    # CutExtrude
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=ON)
    # p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=OFF)

    return p1p


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
        if cells is not None:
            set_name = 'SET-CELL-GLUE-B'
            p.Set(cells=cells, name=set_name)
            set_names.append(set_name)

    return set_names


def create_block_sets_same_volume(p):
    for set_name in ['SET-CELL-GRAIN', 'SET-CELL-INSULATION', 'SET-CELL-GLUE-A', 'SET-CELL-GLUE-B']:
        if set_name in p.sets.keys():
            p_cells = p.sets[set_name].cells
            p_cells = get_same_volume_cells(p, p_cells)
            p.Set(cells=p_cells, name=set_name)


def create_block_surface_common(p, points, dimension):
    z_list = dimension['z_list']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    deep = dimension['deep']
    burn_offset = dimension['burn_offset']
    length = z_list[-1] * 2.0

    p1 = (points[0, 0][0] + burn_offset, points[0, 0][1], 0.0)
    p2 = (points[0, 1][0] + burn_offset, points[0, 1][1], 0.0)
    p3 = (points[0, 0][0] + burn_offset, points[0, 0][1], 1.0)
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

    p1 = [x0 + deep + b + burn_offset, 0.0]
    x1 = p1[0] * np.cos(degrees_to_radians(180.0 / n))
    y1 = p1[0] * np.sin(degrees_to_radians(180.0 / n))
    p_faces = p.faces.getByBoundingBox(0, 0, 0, x1 * 1.1, y1, length / 2.0)
    p_faces = get_same_area_faces(p, p_faces)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-SLOT')


def create_gap_surface_common(p, points, dimension):
    z_list = dimension['z_list']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    burn_offset = dimension['burn_offset']
    length = z_list[-1] * 2.0

    p1 = (points[0, 0][0] + burn_offset, points[0, 0][1], 0.0)
    p2 = (points[0, 1][0] + burn_offset, points[0, 1][1], 0.0)
    p3 = (points[0, 0][0] + burn_offset, points[0, 0][1], 1.0)
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


def draw_map(block):
    """
    根据布尔矩阵 block 绘制 blocks 地图。
    参数:
        block: np.ndarray, 布尔矩阵，True 表示该位置有块
    """

    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    nl, nt = block.shape

    # 数值矩阵用于颜色
    data = np.zeros_like(block, dtype=int)
    data[0, block[0, :]] = 1
    data[-2, block[-2, :]] = 2
    data[-1, block[-1, :]] = 3
    for i in range(1, nl - 2):
        data[i, block[i, :]] = 4

    # 绘图
    fig, ax = plt.subplots(figsize=(8, 8))

    # 颜色映射
    cmap = plt.cm.colors.ListedColormap(['white', '#FF6B6B', '#98FB98', '#4ECDC4', '#FFE66D'])
    bounds = [0, 1, 2, 3, 4, 5]
    norm = plt.cm.colors.BoundaryNorm(bounds, cmap.N)

    im = ax.imshow(data, cmap=cmap, norm=norm, aspect='equal')

    # 坐标轴：行列号
    ax.set_xticks(range(nt))
    ax.set_yticks(range(nl))
    ax.set_xticklabels(range(1, nt + 1))
    ax.set_yticklabels(range(1, nl + 1))

    # 格子边框（黑色网格线）
    ax.set_xticks(np.arange(-0.5, nt, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, nl, 1), minor=True)
    ax.grid(which='minor', color='black', linewidth=0.5, linestyle='-')

    # 在每个 True 格子中心加坐标标签（使用 .format 代替 f-string）
    for i in range(nl):
        for j in range(nt):
            if data[i, j] != 0:
                ax.text(j, i, '({}-{})'.format(i, j), ha='center', va='center', color='black', fontsize=8)

    # 高亮相邻 True 格子之间的共享边
    highlight_color = 'red'
    linewidth = 2.5

    # 向右检查（垂直边）
    for i in range(nl):
        for j in range(nt - 1):
            if block[i, j] and block[i, j + 1]:
                ax.plot([j + 0.5, j + 0.5], [i - 0.5, i + 0.5], color=highlight_color, linewidth=linewidth)

    # 向下检查（水平边）
    for i in range(nl - 1):
        for j in range(nt):
            if block[i, j] and block[i + 1, j]:
                ax.plot([j - 0.5, j + 0.5], [i + 0.5, i + 0.5], color=highlight_color, linewidth=linewidth)

    # 行方向环状接触：检查每行的第一个和最后一个格子
    for i in range(nl):
        if block[i, 0] and block[i, -1]:
            ax.plot([-0.5, -0.5], [i - 0.5, i + 0.5], color=highlight_color, linewidth=linewidth)  # 左边界
            ax.plot([nt - 0.5, nt - 0.5], [i - 0.5, i + 0.5], color=highlight_color, linewidth=linewidth)  # 右边界

    # 图例
    legend_patches = [
        mpatches.Patch(color='#FF6B6B', label='FRONT'),
        mpatches.Patch(color='#98FB98', label='PENULT'),
        mpatches.Patch(color='#4ECDC4', label='BEHIND'),
        mpatches.Patch(color='#FFE66D', label='MIDDLE'),
        mpatches.Patch(color=highlight_color, label='TIE'),
    ]
    ax.legend(handles=legend_patches, loc='upper left', bbox_to_anchor=(1.05, 1))

    ax.set_title('BLOCKS MAP')
    plt.tight_layout()
    plt.show()


def get_tie_types(block):
    """
    根据 block 矩阵计算相邻（包括环形相邻）的格子对，并输出字典。
    参数:
        block: np.ndarray, 布尔矩阵，True 表示有块
    """
    nl, nt = block.shape
    edges_list = []

    # 右邻
    for i in range(nl):
        for j in range(nt - 1):
            if block[i, j] and block[i, j + 1]:
                edges_list.append(((i, j), (i, j + 1), 'right'))

    # 下邻
    for i in range(nl - 1):
        for j in range(nt):
            if block[i, j] and block[i + 1, j]:
                edges_list.append(((i, j), (i + 1, j), 'down'))

    # 环形连接（行方向首尾）
    for i in range(nl):
        if block[i, 0] and block[i, -1]:
            edges_list.append(((i, 0), (i, nt - 1), 'circular'))

    # 规范化并存入字典
    edges_dict = {}
    for (c1, c2, d) in edges_list:
        if d == 'circular':
            key = (c1[0], c1[1], c2[0], c2[1])
        else:
            # 普通邻边，确保顺序统一（按行优先，同行则按列序）
            if c1[0] < c2[0] or (c1[0] == c2[0] and c1[1] < c2[1]):
                key = (c1[0], c1[1], c2[0], c2[1])
            else:
                key = (c2[0], c2[1], c1[0], c1[1])
        edges_dict[key] = d

    # 打印输出
    # for key, d in edges_dict.items():
    #     r1, c1, r2, c2 = key
    #     print("({},{}) -> ({},{})  [{}]".format(r1 + 1, c1 + 1, r2 + 1, c2 + 1, d))

    return edges_dict


def get_block_types(block):
    """
    返回每个有块位置的标签。
    参数:
        block: np.ndarray, 布尔矩阵，True 表示有块
    返回:
        dict: 键为 (行,列) 坐标，值为标签字符串 ('FRONT','PENULT','BEHIND','MIDDLE')
    """
    nl, nt = block.shape
    labels = {}

    # 第一行
    for j in np.where(block[0, :])[0]:
        labels[(0, int(j))] = 'FRONT'

    # 倒数第二行
    if nl >= 2:
        for j in np.where(block[-2, :])[0]:
            labels[(nl - 2, int(j))] = 'PENULT'

    # 最后一行
    for j in np.where(block[-1, :])[0]:
        labels[(nl - 1, int(j))] = 'BEHIND'

    # 中间行（索引 1 到 nl-3）
    for i in range(1, nl - 2):
        for j in np.where(block[i, :])[0]:
            labels[(i, int(j))] = 'MIDDLE'

    return labels


def create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2):
    region1 = a.instances[instance_name_1].surfaces[surface_name_1]
    region2 = a.instances[instance_name_2].surfaces[surface_name_2]
    constrain_name = 'TIE-%s-%s' % (instance_name_1, instance_name_2)
    if major_version >= 2022:
        model.Tie(name=constrain_name, main=region1, secondary=region2, positionToleranceMethod=COMPUTED, adjust=OFF, tieRotations=OFF, thickness=ON)
    else:
        model.Tie(name=constrain_name, master=region1, slave=region2, positionToleranceMethod=COMPUTED, adjust=OFF, tieRotations=OFF, thickness=ON)


def print_sketch(session, model, viewport, sketch_name):
    s = model.ConstrainedSketch(name='__edit__', objectToCopy=mdb.models['Model-1'].sketches[sketch_name])
    s.setPrimaryObject(option=STANDALONE)
    s.Spot(point=(0, 0))
    s.sketchOptions.setValues(grid=OFF)
    if 'REVOLVE' in sketch_name:
        viewport.view.rotate(xAngle=90, yAngle=90, zAngle=0, mode=MODEL)
    viewport.view.fitView()
    session.printToFile(fileName=sketch_name + '.png', format=PNG, canvasObjects=(viewport,))
    s.unsetPrimaryObject()
    del model.sketches['__edit__']


def print_part(session, model, viewport, part_name):
    p = model.parts[part_name]
    viewport.setValues(displayedObject=p)
    viewport.view.setValues(session.views['Iso'])
    cmap = viewport.colorMappings['Material']
    viewport.setColor(colorMapping=cmap)
    session.printToFile(fileName=part_name + '_iso.png', format=PNG, canvasObjects=(viewport,))


def print_assembly(session, model, viewport):
    viewport.setValues(displayedObject=a)
    cmap = viewport.colorMappings['Material']
    viewport.setColor(colorMapping=cmap)

    datum_list = []
    for instance_name in model.rootAssembly.allInstances.keys():
        for datum_id in model.rootAssembly.allInstances[instance_name].datums.keys():
            datum_list.append(model.rootAssembly.allInstances[instance_name].datums[datum_id])
    leaf = dgm.LeafFromDatums(datum_list)
    viewport.assemblyDisplay.displayGroup.remove(leaf=leaf)

    session.printOptions.setValues(reduceColors=False)
    viewport.view.setValues(session.views['Iso'])
    viewport.view.rotate(xAngle=0, yAngle=0, zAngle=-90, mode=MODEL)
    session.printToFile(fileName='assembly_iso.png', format=PNG, canvasObjects=(viewport,))


if __name__ == "__main__":
    n = 9

    d = 3529.0
    x0 = 500.0

    block_length = 1229.0
    block_insulation_thickness_z = 3.0
    block_insulation_thickness_t = 3.0
    block_insulation_thickness_r = 3.0
    block_gap_z = 18.0
    block_gap_t = 18.0

    a = 50.0
    b = 25.0
    fillet_radius = 50.0
    angle_demolding_1 = 1.5

    burn_offset = 0.0

    element_size = 40
    insert_czm = False

    size = '1'

    front_ref_length = 509.0
    behind_ref_length = 500.0

    r_cut_front = 460.0
    length_front = 1500.0
    p0_front = (-1207.5, 794)
    theta0_deg_front = 90.0
    p3_front = (-350, 1762.5)
    theta3_deg_front = 0.0
    r1_front = 929.4
    r2_front = 1524.0
    r3_front = 655.2
    theta_in_deg_front = 1.6

    r_cut_behind = 460.0
    length_behind = 1500.0
    p0_behind = (1207.5, 794)
    theta0_deg_behind = -90.0
    p3_behind = (350, 1762.5)
    theta3_deg_behind = 0.0
    r1_behind = 929.4
    r2_behind = 1524.0
    r3_behind = 655.2
    theta_in_deg_behind = 0.16

    if p3_front[1] > d / 2.0:
        raise RuntimeError('The y-coordinate of p3_front exceeds d/2, which will cause geometric construction to fail. Please check the parameter settings!')

    if p3_behind[1] > d / 2.0:
        raise RuntimeError('The y-coordinate of p3_behind exceeds d/2, which will cause geometric construction to fail. Please check the parameter settings!')

    nl, nt = 6, n
    block = np.zeros((nl, nt), dtype=bool)
    block[:, 0] = True
    # block[:, 1] = True
    # block[:, 8] = True

    # setting_file = 'setting.json'
    # message = load_json(setting_file)
    #
    # n = message['n']
    # d = message['d']
    # x0 = message['x0']
    # block_length = message['block_length']
    # block_insulation_thickness_z = message['block_insulation_thickness_z']
    # block_insulation_thickness_t = message['block_insulation_thickness_t']
    # block_insulation_thickness_r = message['block_insulation_thickness_r']
    # block_gap_z = message['block_gap_z']
    # block_gap_t = message['block_gap_t']
    # a = message['a']
    # b = message['b']
    # fillet_radius = message['fillet_radius']
    # angle_demolding_1 = message['angle_demolding_1']
    # element_size = message['element_size']
    # insert_czm = message['insert_czm']
    # size = message['size']
    # front_ref_length = message['front_ref_length']
    # behind_ref_length = message['behind_ref_length']
    # r_cut_front = message['r_cut_front']
    # length_front = message['length_front']
    # p0_front = message['p0_front']
    # theta0_deg_front = message['theta0_deg_front']
    # p3_front = message['p3_front']
    # theta3_deg_front = message['theta3_deg_front']
    # r1_front = message['r1_front']
    # r2_front = message['r2_front']
    # r3_front = message['r3_front']
    # theta_in_deg_front = message['theta_in_deg_front']
    # r_cut_behind = message['r_cut_behind']
    # length_behind = message['length_behind']
    # p0_behind = message['p0_behind']
    # theta0_deg_behind = message['theta0_deg_behind']
    # p3_behind = message['p3_behind']
    # theta3_deg_behind = message['theta3_deg_behind']
    # r1_behind = message['r1_behind']
    # r2_behind = message['r2_behind']
    # r3_behind = message['r3_behind']
    # theta_in_deg_behind = message['theta_in_deg_behind']

    beta = math.pi / n

    if not ABAQUS_ENV:
        points, lines, faces = geometries(d, x0, beta, [0, 100, 100, 100], [0, 50, 50])
        # plot_geometries(points, lines, faces)

        points, lines, faces = geometries(d, x0, beta, [0, block_insulation_thickness_r], [0, block_gap_z / 2.0, block_insulation_thickness_t])
        print(points)

    if ABAQUS_ENV:
        Mdb()
        model = mdb.models['Model-1']
        model.setValues(absoluteZero=-273.15)

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
            'z_list': [0, block_length / 2 - block_insulation_thickness_z, block_length / 2],
            'deep': 380.0,
            'x0': x0,
            'length_up': 1039.2,
            'width': 100.0,
            'angle_demolding_1': angle_demolding_1,
            'angle_demolding_2': 10.0,
            'fillet_radius': fillet_radius,
            'a': a,
            'b': b,
            'size': size,
            'index_r': 2,
            'index_t': 2,
            'element_size': element_size,
            'insert_czm': insert_czm,
            'beta': beta,
            'burn_offset': burn_offset
        }

        points, lines, faces = geometries(d, x0, beta, [0, block_insulation_thickness_r], [0, block_gap_z / 2.0, block_insulation_thickness_t])
        p_block = create_part_block(model, 'PART-BLOCK', points, lines, faces, block_dimension)

        gap_dimension = deepcopy(block_dimension)
        gap_dimension['z_list'] = [0, block_length / 2 - block_insulation_thickness_z, block_length / 2, block_length / 2 + block_gap_z / 2]
        gap_dimension['index_r'] = 2
        gap_dimension['index_t'] = 3
        p_gap = create_part_gap(model, 'PART-GAP', points, lines, faces, gap_dimension)

        penult_block_dimension = deepcopy(block_dimension)
        p_block_penult = create_part_block_penult(model, 'PART-BLOCK-PENULT', points, lines, faces, penult_block_dimension)

        penult_gap_dimension = deepcopy(gap_dimension)
        p_gap_penult = create_part_gap_penult(model, 'PART-GAP-PENULT', points, lines, faces, penult_gap_dimension)

        points, lines, faces = geometries(d, x0, beta, [0, block_insulation_thickness_r, 300], [0, block_gap_z / 2.0, block_insulation_thickness_t])

        first_block_dimension = deepcopy(block_dimension)
        first_block_dimension['z_list'] = [0, front_ref_length, front_ref_length + block_insulation_thickness_z]
        first_block_dimension['index_r'] = 3
        first_block_dimension['index_t'] = 2

        first_block_dimension['r_cut'] = r_cut_front
        first_block_dimension['length_front'] = length_front
        first_block_dimension['p0'] = p0_front
        first_block_dimension['theta0_deg'] = theta0_deg_front
        first_block_dimension['p3'] = p3_front
        first_block_dimension['theta3_deg'] = theta3_deg_front
        first_block_dimension['r1'] = r1_front
        first_block_dimension['r2'] = r2_front
        first_block_dimension['r3'] = r3_front
        first_block_dimension['theta_in_deg'] = theta_in_deg_front

        p_block_front = create_part_block_front(model, 'PART-BLOCK-FRONT', points, lines, faces, first_block_dimension)

        first_gap_dimension = deepcopy(first_block_dimension)
        first_gap_dimension['z_list'] = [0, front_ref_length, front_ref_length + block_insulation_thickness_z, front_ref_length + block_insulation_thickness_z + block_gap_z / 2]
        p_gap_front = create_part_gap_front(model, 'PART-GAP-FRONT', points, lines, faces, first_gap_dimension)

        behind_block_dimension = deepcopy(first_block_dimension)
        behind_block_dimension['z_list'] = [0, behind_ref_length, behind_ref_length + block_insulation_thickness_z]
        behind_block_dimension['r_cut'] = r_cut_behind
        behind_block_dimension['length_behind'] = length_behind
        behind_block_dimension['p0'] = p0_behind
        behind_block_dimension['theta0_deg'] = theta0_deg_behind
        behind_block_dimension['p3'] = p3_behind
        behind_block_dimension['theta3_deg'] = theta3_deg_behind
        behind_block_dimension['r1'] = r1_behind
        behind_block_dimension['r2'] = r2_behind
        behind_block_dimension['r3'] = r3_behind
        behind_block_dimension['theta_in_deg'] = theta_in_deg_behind
        p_block_behind = create_part_block_behind(model, 'PART-BLOCK-BEHIND', points, lines, faces, behind_block_dimension)

        behind_gap_dimension = deepcopy(behind_block_dimension)
        behind_gap_dimension['z_list'] = [0, behind_ref_length, behind_ref_length + block_insulation_thickness_z, behind_ref_length + block_insulation_thickness_z + block_gap_z / 2]
        p_gap_behind = create_part_gap_behind(model, 'PART-GAP-BEHIND', points, lines, faces, behind_gap_dimension)

        block_types = get_block_types(block)
        ties_types = get_tie_types(block)

        block_dict = {
            'FRONT': p_block_front,
            'PENULT': p_block_penult,
            'BEHIND': p_block_behind,
            'MIDDLE': p_block
        }

        gap_dict = {
            'FRONT': p_gap_front,
            'PENULT': p_gap_penult,
            'BEHIND': p_gap_behind,
            'MIDDLE': p_gap
        }

        a = model.rootAssembly
        a.DatumCsysByDefault(CARTESIAN)
        cylindrical_datum = a.DatumCsysByThreePoints(name='Datum csys-2', coordSysType=CYLINDRICAL, origin=(0.0, 0.0, 0.0), point1=(1.0, 0.0, 0.0), point2=(0.0, 1.0, 0.0))

        for block_loc, block_type in block_types.items():
            l, i = block_loc

            z_shift = 0.0

            if block_type == 'FRONT':
                z_shift = 0.0
            elif block_type == 'MIDDLE':
                z_shift = front_ref_length + block_insulation_thickness_z + block_gap_z / 2 + (l - 1 + 0.5) * (block_gap_z + block_length)
            elif block_type == 'PENULT':
                z_shift = front_ref_length + block_insulation_thickness_z + block_gap_z / 2 + (l - 1 + 0.5) * (block_gap_z + block_length)
            elif block_type == 'BEHIND':
                z_shift = front_ref_length + block_insulation_thickness_z + block_gap_z / 2 + (l - 1) * (block_gap_z + block_length) + block_gap_z / 2 + block_insulation_thickness_z + behind_ref_length

            instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
            a.Instance(name=instance_name, part=block_dict[block_type], dependent=ON)
            a.translate(instanceList=(instance_name,), vector=(0.0, 0.0, z_shift))
            a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)

            instance_name = 'GAP-%s-%s' % (l + 1, i + 1)
            a.Instance(name=instance_name, part=gap_dict[block_type], dependent=ON)
            a.translate(instanceList=(instance_name,), vector=(0.0, 0.0, z_shift))
            a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)

        model.StaticStep(name='Step-1', previous='Initial', nlgeom=OFF, timePeriod=1.0, maxNumInc=10000, initialInc=1.0, minInc=1e-06, maxInc=1.0)
        # model.FrequencyStep(name='Step-1', previous='Initial', numEigen=10)

        for block_loc, block_type in block_types.items():
            l, i = block_loc
            instance_name_1 = 'BLOCK-%s-%s' % (l + 1, i + 1)
            surface_name_1 = 'SURFACE-TIE'
            instance_name_2 = 'GAP-%s-%s' % (l + 1, i + 1)
            surface_name_2 = 'SURFACE-TIE'
            create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

        for tie_loc, tie_type in ties_types.items():
            l1, i1, l2, i2 = tie_loc
            if tie_type == 'down':
                instance_name_1 = 'GAP-%s-%s' % (l1 + 1, i1 + 1)
                surface_name_1 = 'SURFACE-Z2'
                instance_name_2 = 'GAP-%s-%s' % (l2 + 1, i2 + 1)
                surface_name_2 = 'SURFACE-Z-2'
                create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

            elif tie_type == 'right':
                instance_name_1 = 'GAP-%s-%s' % (l1 + 1, i1 + 1)
                surface_name_1 = 'SURFACE-T2'
                instance_name_2 = 'GAP-%s-%s' % (l2 + 1, i2 + 1)
                surface_name_2 = 'SURFACE-T-2'
                create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

            elif tie_type == 'circular':
                instance_name_1 = 'GAP-%s-%s' % (l1 + 1, i1 + 1)
                surface_name_1 = 'SURFACE-T-2'
                instance_name_2 = 'GAP-%s-%s' % (l2 + 1, i2 + 1)
                surface_name_2 = 'SURFACE-T2'
                create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

        for block_loc, block_type in block_types.items():
            l, i = block_loc
            instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
            surface_name = 'SURFACE-INNER'
            load_name = 'LOAD-' + instance_name + '-' + surface_name
            model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=UNIFORM, field='', magnitude=1.0, amplitude=UNSET)

            set_name = 'SET-SURFACE-OUTER'
            bc_name = 'BC-' + instance_name + '-' + set_name
            model.DisplacementBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name],
                                 u1=0.0, u2=0.0, u3=0.0, ur1=UNSET, ur2=UNSET, ur3=UNSET, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', localCsys=a.datums[cylindrical_datum.id])

            instance_name = 'GAP-%s-%s' % (l + 1, i + 1)
            surface_name = 'SURFACE-INNER'
            load_name = 'LOAD-' + instance_name + '-' + surface_name
            model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=UNIFORM, field='', magnitude=1.0, amplitude=UNSET)

            set_name = 'SET-SURFACE-OUTER'
            bc_name = 'BC-' + instance_name + '-' + set_name
            model.DisplacementBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name],
                                 u1=0.0, u2=0.0, u3=0.0, ur1=UNSET, ur2=UNSET, ur3=UNSET, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', localCsys=a.datums[cylindrical_datum.id])

        for block_loc, block_type in block_types.items():
            l, i = block_loc

            if i == 0:
                instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
                set_name = 'SET-SURFACE-T1'
                bc_name = 'BC-' + instance_name + '-' + set_name
                model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

                instance_name = 'GAP-%s-%s' % (l + 1, i + 1)
                set_name = 'SET-SURFACE-T2'
                bc_name = 'BC-' + instance_name + '-' + set_name
                model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

            # if i == 8:
            #     instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
            #     set_name = 'SET-SURFACE-T-1'
            #     bc_name = 'BC-' + instance_name + '-' + set_name
            #     model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])
            #
            #     instance_name = 'GAP-%s-%s' % (l + 1, i + 1)
            #     set_name = 'SET-SURFACE-T-2'
            #     bc_name = 'BC-' + instance_name + '-' + set_name
            #     model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

        if major_version >= 2022:
            mdb.Job(name='Job-1', model='Model-1', description='', type=ANALYSIS,
                    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
                    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
                    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
                    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
                    scratch='', resultsFormat=ODB, numThreadsPerMpiProcess=1,
                    multiprocessingMode=DEFAULT, numCpus=8, numDomains=8, numGPUs=0)
        else:
            mdb.Job(name='Job-1', model='Model-1', description='', type=ANALYSIS,
                    atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
                    memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
                    explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
                    modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
                    scratch='', resultsFormat=ODB, multiprocessingMode=DEFAULT, numCpus=8,
                    numDomains=8, numGPUs=0)

        viewport = session.viewports['Viewport: 1']
        viewport.makeCurrent()
        viewport.setValues(width=200)
        viewport.setValues(height=200)
        # session.pngOptions.setValues(imageSize=(1600, 1600))
        session.printOptions.setValues(vpDecorations=OFF)

        print_assembly(session, model, viewport)

        for sketch_name in model.sketches.keys():
            print_sketch(session, model, viewport, sketch_name)

        for part_name in model.parts.keys():
            print_part(session, model, viewport, part_name)

        mdb.jobs['Job-1'].writeInput(consistencyChecking=OFF)
