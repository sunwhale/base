# -*- coding: utf-8 -*-
"""

"""
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
    radians_to_degrees, rotate_point_around_axis, rotate_point_around_origin_2d, rotate_point_around_vector, set_material, set_obj, solve_three_arcs, string_types, text_type, vertices_in_cells, get_mirror_faces, get_cells_from_faces, get_edges_from_faces

PEN = 1e4
TOL = 1e-6
PENULT_CORRECTION = 1.0


# s.setPrimaryObject(option=STANDALONE)
# p.DatumPointByCoordinate(coords=(0, 0, 0))
# execfile('F:/GitHub/base/base/utils/flow/f2.py', __main__.__dict__)


def create_sketch_cross_section(model, sketch_name, points, index_r, index_t):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 0], point2=points[index_r, 0]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[index_r, 0], point2=points[index_r, index_t], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[index_r, index_t], point2=points[0, index_t]))
    geom_list.append(s.Line(point1=points[0, index_t], point2=points[0, 0]))
    return s


def create_sketch_cross_section_behind(model, sketch_name, points, index_r, index_t):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 0], point2=points[index_r, 0]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[index_r, 0], point2=points[index_r, index_t], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[index_r, index_t], point2=points[0, index_t]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[0, index_t], point2=points[0, 0], direction=CLOCKWISE))
    return s


def create_sketch_burn_x0(model, sketch_name, x0, burn_offset=0.0):
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


def create_sketch_slot(model, sketch_name, x0, slot_deep, slot_ellipse_a, slot_ellipse_b, angle_demolding_1, n, r_cut, burn_offset=0.0):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = [x0 + slot_deep, 0.0]
    p1 = [x0 + slot_deep, -slot_ellipse_a]
    p2 = [x0 + slot_deep + slot_ellipse_b, 0.0]
    e1 = s.EllipseByCenterPerimeter(center=center, axisPoint1=p1, axisPoint2=p2)
    l1 = Line2D(p1, np.tan(degrees_to_radians(angle_demolding_1)))
    l2 = Line2D([x0 + slot_deep - r_cut, 0.0], [x0 + slot_deep - r_cut, 1.0])
    p3 = l1.get_intersection(l2)
    p4 = [p3[0], 0.0]

    s.Line(point1=p1, point2=p3)
    s.Line(point1=p3, point2=p4)
    s.Line(point1=center, point2=p2)
    s.autoTrimCurve(curve1=e1, point1=[x0 + slot_deep, slot_ellipse_a])
    s.Line(point1=p4, point2=center)

    if burn_offset > 0:
        s.offset(distance=burn_offset, objectList=(s.geometry[4], s.geometry[7]), side=RIGHT)
        s.Line(point1=s.vertices[3].coords, point2=s.vertices[7].coords)
        s.Line(point1=s.vertices[5].coords, point2=s.vertices[8].coords)
        s.delete(objectList=(s.geometry[4], s.geometry[7]))

    center_line = s.ConstructionLine(point1=(x0 + slot_deep - r_cut, -1e4), point2=(x0 + slot_deep - r_cut, 1e4))
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


def create_sketch_front_outer(model, sketch_name, t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)

    result = solve_three_arcs(p0, theta0_deg, p3, theta3_deg, r1, r2, r3)
    l1 = Line2D(p3, np.tan(degrees_to_radians(theta_in_deg)))
    l2 = Line2D([0.0, points[index_r, 0, 0]], [1.0, points[index_r, 0, 0]])
    l3 = Line2D((z_list[-1], 0.0), (z_list[-1], 1.0))

    if l1.get_intersection(l2) is None:
        # 处理theta_in_deg为0度，l1和l2平行的情况
        p4 = l1.get_intersection(l3)
        p5 = (PEN, p4[1])
    else:
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


def create_sketch_behind_outer(model, sketch_name, t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)

    result = solve_three_arcs(p0, theta0_deg, p3, theta3_deg, r1, r2, r3)
    l1 = Line2D(p3, np.tan(degrees_to_radians(-theta_in_deg)))
    l2 = Line2D([0.0, points[index_r, 0, 0]], [1.0, points[index_r, 0, 0]])
    l3 = Line2D((-z_list[-1], 0.0), (-z_list[-1], 1.0))
    if l1.get_intersection(l2) is None:
        # 处理theta_in_deg为0度，l1和l2平行的情况
        p4 = l1.get_intersection(l3)
        p5 = (-PEN, p4[1])
    else:

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
    geom_list.append(s.Line(point1=(p0[0], points[0, 0, 0]), point2=p0))
    geom_list.append(s.ArcByCenterEnds(center=c1, point1=p0, point2=p1, direction=get_direction(delta1)))
    geom_list.append(s.ArcByCenterEnds(center=c2, point1=p1, point2=p2, direction=get_direction(delta2)))
    geom_list.append(s.ArcByCenterEnds(center=c3, point1=p2, point2=p3, direction=get_direction(delta3)))
    if np.linalg.norm(p3 - p4) > 1e-10:
        # 处理p3和p4重合的情况
        geom_list.append(s.Line(point1=p3, point2=p4))
    geom_list.append(s.Line(point1=p4, point2=p5))
    # 逆序循环，保证轮廓线从外到内的顺序排列
    for i in range(index_r - 1, 0, -1):
        s.offset(distance=float(points[index_r, 0][0] - points[i, 0][0]), objectList=geom_list, side=LEFT)
    return s, len(geom_list)


def create_sketch_front_outer_offset(model, sketch_name, t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)
    geom_list = []
    geom_list.append(s.Line(point1=(p0[0], x0), point2=p0))
    geom_list.append(s.ArcByCenterEnds(center=c1, point1=p0, point2=p1, direction=get_direction(delta1)))
    geom_list.append(s.ArcByCenterEnds(center=c2, point1=p1, point2=p2, direction=get_direction(delta2)))
    geom_list.append(s.ArcByCenterEnds(center=c3, point1=p2, point2=p3, direction=get_direction(delta3)))
    if np.linalg.norm(p3 - p4) > 1e-10:
        # 处理p3和p4重合的情况
        geom_list.append(s.Line(point1=p3, point2=p4))
    geom_list.append(s.Line(point1=p4, point2=p5))
    # 逆序循环，保证轮廓线从外到内的顺序排列
    for i in range(index_r - 1, 0, -1):
        s.offset(distance=float(points[index_r, 0][0] - points[i, 0][0]), objectList=geom_list, side=RIGHT)
    return s, len(geom_list)


def create_sketch_penult_inner(model, sketch_name, t, x0, slot_deep, block_length, z_list, block_insulation_thickness_z, slot_ellipse_a, slot_ellipse_b, burn_offset=0.0):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)

    r = x0 + slot_deep + slot_ellipse_b + burn_offset + PENULT_CORRECTION

    p0 = [block_length / 2.0 + z_list[-1] - z_list[-2], r]
    p1 = [block_length / 2.0, r]
    p2 = [block_length / 2.0 - block_insulation_thickness_z, r]
    l1 = Line2D(p2, np.tan(degrees_to_radians(22.5)))
    l2 = Line2D([p2[0] - 2.0 * slot_ellipse_b, 0.0], [p2[0] - 2.0 * slot_ellipse_b, 1.0])
    p3 = l1.get_intersection(l2)

    l3 = Line2D(p3, np.tan(degrees_to_radians(45.0)))
    l4 = Line2D([0.0, 0.0], [1.0, 0.0])
    p4 = l3.get_intersection(l4)
    p5 = [block_length / 2.0 + z_list[-1] - z_list[-2], 0.0]

    s.Line(point1=p0, point2=p1)
    s.Line(point1=p1, point2=p2)
    s.Line(point1=p2, point2=p3)
    s.Line(point1=p3, point2=p4)
    s.Line(point1=p4, point2=p5)
    s.Line(point1=p5, point2=p0)

    s.Spot(point=p3)

    center_line = s.ConstructionLine(point1=(0.0, 0.0), point2=(PEN, 0.0))
    s.assignCenterline(line=center_line)

    return s, p3


def create_sketch_behind_inner(model, sketch_name, t, x0, slot_deep, slot_ellipse_a, slot_ellipse_b, burn_offset=0.0):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=4000.0, transform=t)

    r = x0 + slot_deep + slot_ellipse_b + burn_offset + PENULT_CORRECTION

    p1 = [-PEN, r]
    p2 = [PEN, r]
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
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=2000.0, gridSpacing=100.0, transform=t)

    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 0], point2=points[3, 0]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[3, 0], point2=points[3, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[3, 3], point2=points[0, 3]))
    geom_list.append(s.Line(point1=points[0, 3], point2=points[0, 0]))

    return s


def create_sketch_gap_t(model, sketch_name, t, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=2000.0, gridSpacing=100.0, transform=t)

    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 0], point2=points[2, 0]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[2, 0], point2=points[2, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[2, 3], point2=points[0, 3]))
    geom_list.append(s.Line(point1=points[0, 3], point2=points[0, 0]))

    return s


def create_sketch_polygon(model, sketch_name, t, x0, n):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=2000.0, gridSpacing=100.0, transform=t)

    angel = 360.0 / n / 2.0

    l1 = Line2D((0.0, 0.0), math.tan(degrees_to_radians(angel)))
    l2 = Line2D((0.0, 0.0), -math.tan(degrees_to_radians(angel)))
    l3 = Line2D((x0, 0.0), math.tan(degrees_to_radians(90)))

    point1 = l1.get_intersection(l3)
    point2 = l2.get_intersection(l3)

    line = s.Line(point1=point1, point2=point2)

    s.rotate(centerPoint=(0.0, 0.0), angle=90.0 + angel, objectList=(s.geometry[line.id],))
    s.radialPattern(geomList=(s.geometry[line.id],), vertexList=(), number=n, totalAngle=360.0, centerPoint=(0.0, 0.0))
    return s


def create_sketch_gap_front(model, sketch_name, p0_front, theta0_deg_front, p3_front, theta3_deg_front, r1_front, r2_front, r3_front, shell_l_c1_out, gap_front_r, gap_front_l1, gap_front_l2):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=2000.0, gridSpacing=100.0)

    arcs_front = solve_three_arcs(p0_front, theta0_deg_front, p3_front, theta3_deg_front, r1_front, r2_front, r3_front)
    s.ArcByCenterEnds(center=arcs_front['c1'], point1=p0_front, point2=arcs_front['p1'], direction=get_direction(arcs_front['delta1']))
    s.ArcByCenterEnds(center=arcs_front['c2'], point1=arcs_front['p1'], point2=arcs_front['p2'], direction=get_direction(arcs_front['delta2']))
    s.ArcByCenterEnds(center=arcs_front['c3'], point1=arcs_front['p2'], point2=p3_front, direction=get_direction(arcs_front['delta3']))
    s.Line(point1=p0_front, point2=(p0_front[0], 0.0))

    geom_list = []
    for g in s.geometry.values():
        geom_list.append(g)

    s.offset(distance=gap_front_l1, objectList=geom_list, side=LEFT)
    s.offset(distance=gap_front_l1 + gap_front_l2, objectList=geom_list, side=LEFT)
    s.delete(objectList=geom_list)

    # 水平线
    s.Line(point1=(-shell_l_c1_out, gap_front_r), point2=(0.0, gap_front_r))

    curve = s.geometry.findAt((-shell_l_c1_out, gap_front_r))
    s.autoTrimCurve(curve1=curve, point1=(shell_l_c1_out, gap_front_r))

    curve = s.geometry.findAt((0.0, gap_front_r))
    s.autoTrimCurve(curve1=curve, point1=(0.0, gap_front_r))

    # 区间分类
    r1 = s.geometry[8].getVertices()[1].coords[1]
    r2 = s.geometry[8].getVertices()[0].coords[1]
    r3 = s.geometry[11].getVertices()[0].coords[1]
    # 水平线打断交点
    point1 = s.geometry[16].getVertices()[0].coords
    point2 = s.geometry[16].getVertices()[1].coords

    if gap_front_r > r1:
        s.breakCurve(curve1=s.geometry[9], point1=point1, curve2=s.geometry[16], point2=point2)
        s.breakCurve(curve1=s.geometry[13], point1=point1, curve2=s.geometry[16], point2=point2)

    elif r1 > gap_front_r > r2:
        s.breakCurve(curve1=s.geometry[8], point1=point1, curve2=s.geometry[16], point2=point2)
        s.breakCurve(curve1=s.geometry[12], point1=point1, curve2=s.geometry[16], point2=point2)

    elif r2 > gap_front_r > r3:
        s.breakCurve(curve1=s.geometry[7], point1=point1, curve2=s.geometry[16], point2=point2)
        s.breakCurve(curve1=s.geometry[11], point1=point1, curve2=s.geometry[16], point2=point2)

    elif gap_front_r < r3:
        s.breakCurve(curve1=s.geometry[6], point1=point1, curve2=s.geometry[16], point2=point2)
        s.breakCurve(curve1=s.geometry[10], point1=point1, curve2=s.geometry[16], point2=point2)

    geom_list = []
    for geo_item in s.geometry.values():
        if geo_item.pointOn[1] > gap_front_r + TOL:
            geom_list.append(s.geometry[geo_item.id])

    s.delete(objectList=geom_list)

    point1 = [p0_front[0] - gap_front_l1 - gap_front_l2, 0.0]
    point2 = [p0_front[0] - gap_front_l1, 0.0]
    s.Line(point1=point1, point2=point2)

    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    return s


def get_local_variables_common(dimension):
    n = dimension['n']
    z_list = dimension['z_list']
    slot_deep = dimension['slot_deep']
    x0 = dimension['x0']
    angle_demolding_1 = dimension['angle_demolding_1']
    slot_ellipse_a = dimension['slot_ellipse_a']
    slot_ellipse_b = dimension['slot_ellipse_b']
    size = dimension['size']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    element_size = dimension['element_size']
    insert_czm = dimension['insert_czm']
    burn_offset = dimension['burn_offset']

    return (n,
            z_list,
            slot_deep,
            x0,
            angle_demolding_1,
            slot_ellipse_a,
            slot_ellipse_b,
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


def get_local_variables_behind(dimension):
    r_cut = dimension['r_cut']
    length_behind = dimension['length_behind']
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
            length_behind,
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


def create_part_block(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    n, z_list, slot_deep, x0, angle_demolding_1, slot_ellipse_a, slot_ellipse_b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables_common(dimension)

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
    set_names = create_sets_block_common(p, faces, dimension)

    # 星槽切割
    r_cut = x0 + slot_deep
    s_slot, p1p, p2p = create_sketch_slot(model, 'SKETCH-SLOT', x0, slot_deep, slot_ellipse_a, slot_ellipse_b, angle_demolding_1, n, r_cut, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, flipExtrudeDirection=ON)

    # 燃面退移x0
    s_burn_x0 = create_sketch_burn_x0(model, 'SKETCH-BURN-X0', x0, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=ON)

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
    create_surface_block_common(p, points, dimension)
    create_surface_slot(p, p1p, p2p, 0.0, z_list[-1], size)
    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT'], 'SURFACE-INNER')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 更新集合（体），处理镜像
    create_sets_block_same_volume(p)

    # 创建集合（面），粘接界面
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-INSULATION'], p.sets['SET-CELL-GLUE-A']), name='SET-FACES-INSULATION-GLUE-A')
    create_sets_z_t_face(p, points, dimension, 1, 1, 'SET-FACES-INSULATION-GLUE-A')

    # 星槽剖分
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
    n, z_list, slot_deep, x0, angle_demolding_1, slot_ellipse_a, slot_ellipse_b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables_common(dimension)

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
    r_cut = x0 + slot_deep
    s_slot, p1p, p2p = create_sketch_slot(model, 'SKETCH-SLOT', x0, slot_deep, slot_ellipse_a, slot_ellipse_b, angle_demolding_1, n, r_cut, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, flipExtrudeDirection=ON)

    # 燃面退移x0
    s_burn_x0 = create_sketch_burn_x0(model, 'SKETCH-BURN-X0', x0, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=ON)

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
    create_surface_gap_common(p, points, dimension)
    create_surface_slot(p, p1p, p2p, 0.0, z_list[-1], size)
    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT'], 'SURFACE-INNER')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体）
    set_name = 'SET-CELL-GLUE-A'
    p.Set(cells=p.cells, name=set_name)

    # 星槽剖分
    part_partition_p1p(p, d, p1p)

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_front(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    n, z_list, slot_deep, x0, angle_demolding_1, slot_ellipse_a, slot_ellipse_b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables_common(dimension)
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

    # 生成额外基础体，z方向长度length_front
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cross_section, depth=length_front, flipExtrudeDirection=ON)

    # 旋转切割头部外轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_front_outer, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_front_outer(model, 'SKETCH-FRONT-OUTER', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_front_outer, angle=360.0, flipRevolveDirection=ON)

    # SKETCH-FRONT-OUTER-OFFSET
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_front_outer_offset, num_geometry = create_sketch_front_outer_offset(model, 'SKETCH-FRONT-OUTER-OFFSET', t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3)

    # 创建面SURFACE-OUTER
    # p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    # for g in s_front_outer_offset.geometry.values()[:6]:
    #     z, x = g.pointOn
    #     point = (x, 0.0, z)
    #     angle = beta / 2.0
    #     point_rot = rotate_point_around_vector(point, [0, 0, 1], angle)
    #     p_faces += p.faces.findAt((point_rot,))
    # if p_faces:
    #     p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    # 面剖分OUTER-OFFSET
    g = s_front_outer_offset.geometry
    faces_xz_plane = {}
    for i in range(1, index_r):
        faces_xz_plane[i] = []
        for j in range(2, num_geometry + 1):
            pa = (np.array(g[j + num_geometry * (i - 1)].pointOn) + np.array(g[j + num_geometry * i].pointOn)) / 2.0
            faces_xz_plane[i].append(pa)
            s_front_outer_offset.Spot(point=pa)
    for i in range(1, index_r):
        for j in range(3, num_geometry + 1):
            pa = g[num_geometry * (i - 1) + j].getVertices()[0].coords
            pb = g[num_geometry * i + j].getVertices()[0].coords
            s_front_outer_offset.Line(point1=pa, point2=pb)
    p_faces = p.faces.getByBoundingBox(0, 0, -PEN, PEN, TOL, PEN)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketch=s_front_outer_offset)

    # 弧线轮廓剖分
    x, y = polar_to_cartesian(p4[1], TOL)
    # x = min(x, points[index_r, 0][0])
    sweep_edge = p.edges.findAt((x, y, z_list[-1]))  # 基于p4点所在的半径拾取sweep_edge
    # 拾取主体弧线
    partition_edges = []
    for g in s_front_outer_offset.geometry.values()[2:index_r * num_geometry]:
        z, x = g.pointOn
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # 连接线段剖分
    x, y = polar_to_cartesian(p4[1], TOL)
    # x = min(x, points[index_r, 0][0])
    sweep_edge = p.edges.findAt((x, y, z_list[-1]))  # 基于p4点所在的半径拾取sweep_edge
    # 拾取分段连线
    partition_edges = []
    for g in s_front_outer_offset.geometry.values()[index_r * num_geometry:]:
        z, x = g.pointOn
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # z剖分
    part_partition_z(p, d, z_list)

    # theta剖分
    t_planes = []
    for j in range(1, index_t):
        # 建立平面，通过三个点：同一个theta的两个点和z方向上偏移1.0的点，保证平面法向量朝外，用该平面切割p.cells
        t_planes.append(p.DatumPlaneByThreePoints(point1=(points[0, j, 0], points[0, j, 1], 0.0), point2=(points[-1, j, 0], points[-1, j, 1], 0.0), point3=(points[0, j, 0], points[0, j, 1], 1.0)))
    for t_plane in t_planes:
        p.PartitionCellByDatumPlane(datumPlane=d[t_plane.id], cells=p.cells)

    # 创建集合（体），SET-CELL-GRAIN
    cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for rtz in [
        [0, 0, 0]
    ]:
        cells += p.cells.findAt(((faces[rtz[0], rtz[1]][0], faces[rtz[0], rtz[1]][1], z_centers[rtz[2]]),))
    for pa in faces_xz_plane[index_r - 1]:
        if pa[0] < z_list[1]:
            cells += p.cells.findAt(((pa[1], 0.0, pa[0]),))
        else:
            # 处理切割面距离中心界面距离非常近的情况
            cells += p.cells.findAt(((pa[1], 0.0, z_list[1] - TOL * 10),))
    if cells:
        p.Set(cells=cells, name='SET-CELL-GRAIN')

    # 星槽切割
    s_slot, p1p, p2p = create_sketch_slot(model, 'SKETCH-FRONT-SLOT', x0, slot_deep, slot_ellipse_a, slot_ellipse_b, angle_demolding_1, n, r_cut, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, flipExtrudeDirection=ON)
    p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, angle=90.0, flipRevolveDirection=OFF)

    # 燃面退移x0
    s_burn_x0 = create_sketch_burn_x0(model, 'SKETCH-BURN-X0', x0, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=ON)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=OFF)

    # 镜像
    if size == '1':
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
    elif size == '1/2':
        pass
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    # 创建集合（体），SET-CELL-INSULATION
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-GRAIN', ['SET-CELL-GRAIN'])
    if cells:
        p.Set(cells=cells, name='SET-CELL-INSULATION')

    # 创建集合（体），SET-CELL-GLUE-A
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-INSULATION', ['SET-CELL-GRAIN', 'SET-CELL-INSULATION'])
    if cells:
        p.Set(cells=cells, name='SET-CELL-GLUE-A')

    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    # 星槽剖分
    # 拾取星槽切割后的轮廓曲线
    p_edges = []
    for z_center in z_centers:
        edge = p.edges.findAt((p1p[0], p1p[1], z_center))
        if edge is not None:
            p_edges.append(edge)
        # p.DatumPointByCoordinate(coords=(p1p[0], p1p[1], z_center))
    point1 = (x0 + slot_deep - r_cut, 0.0)
    point2 = (x0 + slot_deep - r_cut, 1.0)
    point3 = rotate_point_around_origin_2d(point1, beta / 2.0)
    point4 = rotate_point_around_origin_2d(point2, beta / 2.0)
    point5 = rotate_point_around_axis((p1p[0], p1p[1], 0.0), (point3[0], point3[1], 0.0), (point4[0], point4[1], 0.0), TOL * 10.0)
    # p.DatumPointByCoordinate(coords=point5)
    edge = p.edges.findAt(point5)
    if edge is not None:
        p_edges.append(edge)
    if p_edges:
        p.PartitionCellByExtrudeEdge(line=d[y_axis.id], cells=p.cells, edges=p_edges, sense=REVERSE)

    # 创建面
    create_surface_block_common(p, points, dimension)
    create_surface_slot(p, p1p, p2p, -r_cut - slot_ellipse_b - burn_offset, z_list[-1], size, is_middle=False)

    if size == '1':
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
        # xz_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=-180.0 / n / 2.0)
        # p.PartitionCellByDatumPlane(datumPlane=d[xz_plane_rot.id], cells=p.cells)

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    if 'SURFACE-OUTER' in given_surface_names:
        given_surface_names.remove('SURFACE-OUTER')
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT'], 'SURFACE-INNER')

    if faces.shape[0] >= 3 and faces.shape[1] >= 3:
        # 创建集合（体），SET-CELL-GLUE-B
        p_cells = get_cells_from_faces(p, p.surfaces['SURFACE-OUTER'].faces)
        if p_cells:
            p.Set(cells=p_cells, name='SET-CELL-GLUE-B')

        # 更新集合（体），SET-CELL-GLUE-A
        p_cells = get_cells_by_remove(p, p.sets['SET-CELL-GLUE-A'].cells, p.sets['SET-CELL-GLUE-B'].cells)
        if p_cells:
            p.Set(cells=p_cells, name='SET-CELL-GLUE-A')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 更新集合（体），处理镜像
    # create_sets_block_same_volume(p)

    # 创建集合（面），粘接界面
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-INSULATION'], p.sets['SET-CELL-GLUE-A']), name='SET-FACES-INSULATION-GLUE-A')
    create_sets_z_t_face(p, points, dimension, 1, 1, 'SET-FACES-INSULATION-GLUE-A')

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    # 插入内聚力单元
    if insert_czm:
        insert_COH3D8_at_face_set(p, 'SET-FACES-GRAIN-INSULATION', 'COHESIVE-ELEMENTS-GRAIN-INSULATION')

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_gap_front(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    n, z_list, slot_deep, x0, angle_demolding_1, slot_ellipse_a, slot_ellipse_b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables_common(dimension)
    r_cut, length_front, p0, theta0_deg, p3, theta3_deg, theta_in_deg, beta, r1, r2, r3 = get_local_variables_front(dimension)

    # 基本参数
    origin = (0.0, 0.0, 0.0)
    length = z_list[-2] * 2.0
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-GAP-Z
    s_gap_z = create_sketch_gap_z_front_behind(model, 'SKETCH-GAP-Z-FRONT-BEHIND', points)

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis, xy_plane_z1 = create_part_base(model, part_name, s_gap_z, length)

    # 生成额外基础体，z方向长度length_front
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_z, depth=length_front, flipExtrudeDirection=ON)

    # SKETCH-GAP-T
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, length / 2.0))
    s_gap_t = create_sketch_gap_t_front_behind(model, 'SKETCH-GAP-T-FRONT-BEHIND', t, points)

    # 生成额外基础体，z方向长度（z_list[-1] - z_list[-2]）
    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_t, depth=(z_list[-1] - z_list[-2]), flipExtrudeDirection=OFF)

    # 旋转切割头部外轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_front_outer, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_front_outer(model, 'SKETCH-FRONT-OUTER', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_front_outer, angle=360.0, flipRevolveDirection=ON)

    # z剖分
    part_partition_z(p, d, z_list)

    # theta剖分
    point1 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], length / 2.0))
    point2 = p.DatumPointByCoordinate(coords=(lines['02-12'][2][0], lines['02-12'][2][1], length / 2.0))
    point3 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], 0.0))
    partition_plane = p.DatumPlaneByThreePoints(point1=d[point1.id], point2=d[point2.id], point3=d[point3.id])
    p.PartitionCellByDatumPlane(datumPlane=d[partition_plane.id], cells=p.cells)

    # 星槽切割
    s_slot, p1p, p2p = create_sketch_slot(model, 'SKETCH-FRONT-SLOT', x0, slot_deep, slot_ellipse_a, slot_ellipse_b, angle_demolding_1, n, r_cut, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, flipExtrudeDirection=ON)
    p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, angle=90.0, flipRevolveDirection=OFF)

    # 燃面退移x0
    s_burn_x0 = create_sketch_burn_x0(model, 'SKETCH-BURN-X0', x0, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=ON)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=OFF)

    # 镜像
    if size == '1':
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    elif size == '1/2':
        pass
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    # 创建面
    create_surface_gap_common(p, points, dimension)
    create_surface_slot(p, p1p, p2p, -r_cut - slot_ellipse_b - burn_offset, z_list[-1], size, is_middle=False)

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT'], 'SURFACE-INNER')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 星槽剖分
    offset = p1p[0]
    if offset >= p.cells.getBoundingBox()['low'][0]:
        yz_plane_slot = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=offset)
        try:
            p.PartitionCellByDatumPlane(datumPlane=d[yz_plane_slot.id], cells=p.cells.getByBoundingBox(0, -PEN, 0, PEN, PEN, PEN))
        except:
            pass
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    # 创建集合（体），SET-CELL-GLUE-A
    set_name = 'SET-CELL-GLUE-A'
    p.Set(cells=p.cells, name=set_name)

    # 拓扑层面忽略外表面的公共边
    p_faces = p.surfaces['SURFACE-OUTER'].faces.getByBoundingBox(0, -PEN, -PEN, PEN, PEN, 0)
    ignore_common_edges_of_faces(p, p_faces)

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_penult(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    n, z_list, slot_deep, x0, angle_demolding_1, slot_ellipse_a, slot_ellipse_b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables_common(dimension)

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
    set_names = create_sets_block_common(p, faces, dimension)

    # 星槽切割
    r_cut = x0 + slot_deep
    s_slot, p1p, p2p = create_sketch_slot(model, 'SKETCH-SLOT', x0, slot_deep, slot_ellipse_a, slot_ellipse_b, angle_demolding_1, n, r_cut, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, flipExtrudeDirection=ON)

    # 燃面退移x0
    s_burn_x0 = create_sketch_burn_x0(model, 'SKETCH-BURN-X0', x0, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=ON)

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

    # 更新集合（体），处理镜像
    create_sets_block_same_volume(p)

    # 创建面
    create_surface_block_common(p, points, dimension)
    create_surface_slot(p, p1p, p2p, 0.0, z_list[-1], size)
    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')

    # 旋转切割内燃道
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_penult_inner, ref_point = create_sketch_penult_inner(model, 'SKETCH-PENULT-INNER', t, x0, slot_deep, block_length, z_list, block_insulation_thickness_z, slot_ellipse_a, slot_ellipse_b, burn_offset)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_penult_inner, angle=360.0, flipRevolveDirection=ON)

    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-REVOLVE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT', 'SURFACE-REVOLVE'], 'SURFACE-INNER')

    # 倒角剖分
    xy_plane_inner = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=ref_point[0])
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_inner.id], cells=p.cells)

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（面），粘接界面
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-INSULATION'], p.sets['SET-CELL-GLUE-A']), name='SET-FACES-INSULATION-GLUE-A')
    create_sets_z_t_face(p, points, dimension, 1, 1, 'SET-FACES-INSULATION-GLUE-A')

    # 星槽剖分
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


def create_part_gap_penult(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    n, z_list, slot_deep, x0, angle_demolding_1, slot_ellipse_a, slot_ellipse_b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables_common(dimension)

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
    part_partition_z(p, d, z_list)
    # del p.features['Partition cell-1']

    # theta剖分
    point1 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], length / 2.0))
    point2 = p.DatumPointByCoordinate(coords=(lines['02-12'][2][0], lines['02-12'][2][1], length / 2.0))
    point3 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], 0.0))
    partition_plane = p.DatumPlaneByThreePoints(point1=d[point1.id], point2=d[point2.id], point3=d[point3.id])
    p.PartitionCellByDatumPlane(datumPlane=d[partition_plane.id], cells=p.cells)

    # 星槽切割
    r_cut = x0 + slot_deep
    s_slot, p1p, p2p = create_sketch_slot(model, 'SKETCH-SLOT', x0, slot_deep, slot_ellipse_a, slot_ellipse_b, angle_demolding_1, n, r_cut, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_slot, flipExtrudeDirection=ON)

    # 燃面退移x0
    s_burn_x0 = create_sketch_burn_x0(model, 'SKETCH-BURN-X0', x0, burn_offset)
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_burn_x0, flipExtrudeDirection=ON)

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
    create_surface_gap_common(p, points, dimension)
    create_surface_slot(p, p1p, p2p, 0.0, z_list[-1], size)
    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')

    # 捕捉倒角参考点
    p.DatumPointByCoordinate(coords=(p2p[0], p2p[1], 0))
    p_edge = p.edges.getByBoundingSphere((p2p[0], p2p[1], 0), 10.0)
    p_edge.getBoundingBox()

    # 旋转切割内燃道
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_penult_inner, ref_point = create_sketch_penult_inner(model, 'SKETCH-PENULT-INNER', t, x0, slot_deep, block_length, z_list, block_insulation_thickness_z, slot_ellipse_a, slot_ellipse_b, burn_offset)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_penult_inner, angle=360.0, flipRevolveDirection=ON)

    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-REVOLVE')
    combine_surfaces(p, ['SURFACE-X0', 'SURFACE-SLOT', 'SURFACE-REVOLVE'], 'SURFACE-INNER')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体）
    set_name = 'SET-CELL-GLUE-A'
    p.Set(cells=p.cells, name=set_name)

    # 星槽剖分
    part_partition_p1p(p, d, p1p)

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_behind(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    n, z_list, slot_deep, x0, angle_demolding_1, slot_ellipse_a, slot_ellipse_b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables_common(dimension)
    r_cut, length_behind, p0, theta0_deg, p3, theta3_deg, theta_in_deg, beta, r1, r2, r3 = get_local_variables_behind(dimension)

    # 基本参数
    origin = (0.0, 0.0, 0.0)
    length = z_list[-1] * 2.0
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-CROSS-SECTION
    s_cross_section = create_sketch_cross_section(model, 'SKETCH-CROSS-SECTION', points, index_r, index_t)

    # 生成基础体
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cross_section, depth=length / 2.0, flipExtrudeDirection=ON)

    # 生成额外基础体，z方向长度length_behind
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cross_section, depth=length_behind, flipExtrudeDirection=OFF)

    # 旋转切割头部外轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_outer, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_behind_outer(model, 'SKETCH-BEHIND-OUTER', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_outer, angle=360.0, flipRevolveDirection=ON)

    # SKETCH-BEHIND-OUTER-OFFSET
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_outer_offset, num_geometry = create_sketch_behind_outer_offset(model, 'SKETCH-BEHIND-OUTER-OFFSET', t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3)

    # 创建面SURFACE-OUTER
    # p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    # for g in s_front_outer_offset.geometry.values()[:6]:
    #     z, x = g.pointOn
    #     point = (x, 0.0, z)
    #     angle = beta / 2.0
    #     point_rot = rotate_point_around_vector(point, [0, 0, 1], angle)
    #     p_faces += p.faces.findAt((point_rot,))
    # if p_faces:
    #     p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    # 面剖分OUTER-OFFSET
    g = s_behind_outer_offset.geometry
    faces_xz_plane = {}
    for i in range(1, index_r):
        faces_xz_plane[i] = []
        for j in range(2, num_geometry + 1):
            pa = (np.array(g[j + num_geometry * (i - 1)].pointOn) + np.array(g[j + num_geometry * i].pointOn)) / 2.0
            faces_xz_plane[i].append(pa)
            s_behind_outer_offset.Spot(point=pa)
    for i in range(1, index_r):
        for j in range(3, num_geometry + 1):
            pa = g[num_geometry * (i - 1) + j].getVertices()[0].coords
            pb = g[num_geometry * i + j].getVertices()[0].coords
            s_behind_outer_offset.Line(point1=pa, point2=pb)
    p_faces = p.faces.getByBoundingBox(0, 0, -PEN, PEN, TOL, PEN)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketch=s_behind_outer_offset)

    # 弧线轮廓剖分
    x, y = polar_to_cartesian(p4[1], TOL)
    # x = min(x, points[index_r, 0][0])
    sweep_edge = p.edges.findAt((x, y, -z_list[-1]))
    # 拾取主体弧线
    partition_edges = []
    for g in s_behind_outer_offset.geometry.values()[2:index_r * num_geometry]:
        z, x = g.pointOn
        # p.DatumPointByCoordinate(coords=(x, 0.0, z))
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # 连接线段剖分
    x, y = polar_to_cartesian(p4[1], TOL)
    # x = min(x, points[index_r, 0][0])
    sweep_edge = p.edges.findAt((x, y, -z_list[-1]))
    # 拾取分段连线
    partition_edges = []
    for g in s_behind_outer_offset.geometry.values()[index_r * num_geometry:]:
        z, x = g.pointOn
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # z剖分
    part_partition_z(p, d, z_list, is_minus=True)

    # theta剖分
    t_planes = []
    for j in range(1, index_t):
        # 建立平面，通过三个点：同一个theta的两个点和z方向上偏移1.0的点，保证平面法向量朝外，用该平面切割p.cells
        t_planes.append(p.DatumPlaneByThreePoints(point1=(points[0, j, 0], points[0, j, 1], 0.0), point2=(points[-1, j, 0], points[-1, j, 1], 0.0), point3=(points[0, j, 0], points[0, j, 1], 1.0)))
    for t_plane in t_planes:
        p.PartitionCellByDatumPlane(datumPlane=d[t_plane.id], cells=p.cells)

    # 创建集合（体），SET-CELL-GRAIN
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

    # 镜像
    if size == '1':
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
        # p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    elif size == '1/2':
        pass
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    # 创建集合（体），SET-CELL-INSULATION
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-GRAIN', ['SET-CELL-GRAIN'])
    if cells:
        p.Set(cells=cells, name='SET-CELL-INSULATION')

    # 创建集合（体），SET-CELL-GLUE-A
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-INSULATION', ['SET-CELL-GRAIN', 'SET-CELL-INSULATION'])
    if cells:
        p.Set(cells=cells, name='SET-CELL-GLUE-A')

    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    # 创建面
    create_surface_block_common(p, points, dimension)

    if size == '1':
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
        # xz_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=-180.0 / n / 2.0)
        # p.PartitionCellByDatumPlane(datumPlane=d[xz_plane_rot.id], cells=p.cells)

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    if 'SURFACE-OUTER' in given_surface_names:
        given_surface_names.remove('SURFACE-OUTER')
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')

    # 旋转切割尾部内轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_inner = create_sketch_behind_inner(model, 'SKETCH-BEHIND-INNER', t, x0, slot_deep, slot_ellipse_a, slot_ellipse_b, burn_offset)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_inner, angle=360.0, flipRevolveDirection=ON)

    # 通过排除法确定内表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

    if faces.shape[0] >= 3 and faces.shape[1] >= 3:
        # 创建集合（体），SET-CELL-GLUE-B
        p_cells = get_cells_from_faces(p, p.surfaces['SURFACE-OUTER'].faces)
        if p_cells:
            p.Set(cells=p_cells, name='SET-CELL-GLUE-B')

        # 更新集合（体），SET-CELL-GLUE-A
        p_cells = get_cells_by_remove(p, p.sets['SET-CELL-GLUE-A'].cells, p.sets['SET-CELL-GLUE-B'].cells)
        if p_cells:
            p.Set(cells=p_cells, name='SET-CELL-GLUE-A')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 更新集合（体），处理镜像
    # create_sets_block_same_volume(p)

    # 创建集合（面），粘接界面
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-INSULATION'], p.sets['SET-CELL-GLUE-A']), name='SET-FACES-INSULATION-GLUE-A')
    create_sets_z_t_face(p, points, dimension, 1, 1, 'SET-FACES-INSULATION-GLUE-A')

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    # 插入内聚力单元
    if insert_czm:
        insert_COH3D8_at_face_set(p, 'SET-FACES-GRAIN-INSULATION', 'COHESIVE-ELEMENTS-GRAIN-INSULATION')

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_behind_1(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    n, z_list, slot_deep, x0, angle_demolding_1, slot_ellipse_a, slot_ellipse_b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables_common(dimension)
    r_cut, length_behind, p0, theta0_deg, p3, theta3_deg, theta_in_deg, beta, r1, r2, r3 = get_local_variables_behind(dimension)
    central_angle = dimension['central_angle']

    # 基本参数
    origin = (0.0, 0.0, 0.0)
    length = z_list[-1] * 2.0
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-CROSS-SECTION
    s_cross_section = create_sketch_cross_section_behind(model, 'SKETCH-CROSS-SECTION-BEHIND', points, index_r, index_t)

    # 生成基础体
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cross_section, depth=length / 2.0, flipExtrudeDirection=ON)

    # 生成额外基础体，z方向长度length_behind
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cross_section, depth=length_behind, flipExtrudeDirection=OFF)

    # 旋转切割头部外轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_outer, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_behind_outer(model, 'SKETCH-BEHIND-OUTER', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_outer, angle=360.0, flipRevolveDirection=ON)

    # SKETCH-BEHIND-OUTER-OFFSET
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_outer_offset, num_geometry = create_sketch_behind_outer_offset(model, 'SKETCH-BEHIND-OUTER-OFFSET', t, points, x0, index_r, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3)

    # 创建面SURFACE-OUTER
    # p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    # for g in s_front_outer_offset.geometry.values()[:6]:
    #     z, x = g.pointOn
    #     point = (x, 0.0, z)
    #     angle = beta / 2.0
    #     point_rot = rotate_point_around_vector(point, [0, 0, 1], angle)
    #     p_faces += p.faces.findAt((point_rot,))
    # if p_faces:
    #     p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    # 面剖分OUTER-OFFSET
    g = s_behind_outer_offset.geometry
    faces_xz_plane = {}
    for i in range(1, index_r):
        faces_xz_plane[i] = []
        for j in range(2, num_geometry + 1):
            pa = (np.array(g[j + num_geometry * (i - 1)].pointOn) + np.array(g[j + num_geometry * i].pointOn)) / 2.0
            faces_xz_plane[i].append(pa)
            s_behind_outer_offset.Spot(point=pa)
    for i in range(1, index_r):
        for j in range(3, num_geometry + 1):
            pa = g[num_geometry * (i - 1) + j].getVertices()[0].coords
            pb = g[num_geometry * i + j].getVertices()[0].coords
            s_behind_outer_offset.Line(point1=pa, point2=pb)
    p_faces = p.faces.getByBoundingBox(0, 0, -PEN, PEN, TOL, PEN)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketch=s_behind_outer_offset)

    # 弧线轮廓剖分
    if central_angle < math.pi / n:
        x, y = polar_to_cartesian(points[0, 0, 0], TOL)
    else:
        x, y = polar_to_cartesian(p4[1], TOL)
    sweep_edge = p.edges.findAt((x, y, -z_list[-1]))

    # 拾取主体弧线
    partition_edges = []
    for g in s_behind_outer_offset.geometry.values()[2:index_r * num_geometry]:
        z, x = g.pointOn
        # p.DatumPointByCoordinate(coords=(x, 0.0, z))
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # 连接线段剖分
    if central_angle < math.pi / n:
        x, y = polar_to_cartesian(points[0, 0, 0], TOL)
    else:
        x, y = polar_to_cartesian(p4[1], TOL)
    sweep_edge = p.edges.findAt((x, y, -z_list[-1]))
    # 拾取分段连线
    partition_edges = []
    for g in s_behind_outer_offset.geometry.values()[index_r * num_geometry:]:
        z, x = g.pointOn
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # z剖分
    part_partition_z(p, d, z_list, is_minus=True)

    # theta剖分
    t_planes = []
    for j in range(1, index_t):
        # 建立平面，通过三个点：同一个theta的两个点和z方向上偏移1.0的点，保证平面法向量朝外，用该平面切割p.cells
        t_planes.append(p.DatumPlaneByThreePoints(point1=(points[0, j, 0], points[0, j, 1], 0.0), point2=(points[-1, j, 0], points[-1, j, 1], 0.0), point3=(points[0, j, 0], points[0, j, 1], 1.0)))
    for t_plane in t_planes:
        p.PartitionCellByDatumPlane(datumPlane=d[t_plane.id], cells=p.cells)

    # 创建集合（体），SET-CELL-GRAIN
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

    # 镜像
    if size == '1':
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
        # p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    elif size == '1/2':
        pass
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    # 创建集合（体），SET-CELL-INSULATION
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-GRAIN', ['SET-CELL-GRAIN'])
    if cells:
        p.Set(cells=cells, name='SET-CELL-INSULATION')

    # 创建集合（体），SET-CELL-GLUE-A
    cells = get_cells_adjacent_to_set_and_remove_set_names(p, 'SET-CELL-INSULATION', ['SET-CELL-GRAIN', 'SET-CELL-INSULATION'])
    if cells:
        p.Set(cells=cells, name='SET-CELL-GLUE-A')

    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    # 创建面
    create_surface_block_common(p, points, dimension)

    if size == '1':
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
        # xz_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=-180.0 / n / 2.0)
        # p.PartitionCellByDatumPlane(datumPlane=d[xz_plane_rot.id], cells=p.cells)

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    if 'SURFACE-OUTER' in given_surface_names:
        given_surface_names.remove('SURFACE-OUTER')
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')

    # 旋转切割尾部内轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_inner = create_sketch_behind_inner(model, 'SKETCH-BEHIND-INNER', t, x0, slot_deep, slot_ellipse_a, slot_ellipse_b, burn_offset)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_inner, angle=360.0, flipRevolveDirection=ON)

    # 通过排除法确定内表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

    if faces.shape[0] >= 3 and faces.shape[1] >= 3:
        # 创建集合（体），SET-CELL-GLUE-B
        p_cells = get_cells_from_faces(p, p.surfaces['SURFACE-OUTER'].faces)
        if p_cells:
            p.Set(cells=p_cells, name='SET-CELL-GLUE-B')

        # 更新集合（体），SET-CELL-GLUE-A
        p_cells = get_cells_by_remove(p, p.sets['SET-CELL-GLUE-A'].cells, p.sets['SET-CELL-GLUE-B'].cells)
        if p_cells:
            p.Set(cells=p_cells, name='SET-CELL-GLUE-A')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 更新集合（体），处理镜像
    # create_sets_block_same_volume(p)

    # 创建集合（面），粘接界面
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    # 插入内聚力单元
    if insert_czm:
        insert_COH3D8_at_face_set(p, 'SET-FACES-GRAIN-INSULATION', 'COHESIVE-ELEMENTS-GRAIN-INSULATION')

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_behind_2(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    n, z_list, slot_deep, x0, angle_demolding_1, slot_ellipse_a, slot_ellipse_b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables_common(dimension)

    # 基本参数
    origin = (0.0, 0.0, 0.0)
    length = z_list[-1] * 2.0
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-CROSS-SECTION
    s_cross_section = create_sketch_cross_section_behind(model, 'SKETCH-CROSS-SECTION-BEHIND', points, index_r, index_t)

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis, xy_plane_z1 = create_part_base(model, part_name, s_cross_section, length)

    # 截面剖分
    part_partition_cross_section(model, p, d, x_axis, z_axis, index_t, index_r)

    # z剖分
    part_partition_z(p, d, z_list)

    # 创建集合（体）
    set_names = create_sets_block_common(p, faces, dimension)

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

    # 旋转切割尾部内轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_inner = create_sketch_behind_inner(model, 'SKETCH-BEHIND-INNER', t, x0, slot_deep, slot_ellipse_a, slot_ellipse_b, burn_offset)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_inner, angle=360.0, flipRevolveDirection=ON)

    # 创建面
    create_surface_block_common(p, points, dimension)
    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 更新集合（体），处理镜像
    create_sets_block_same_volume(p)

    # 创建集合（面），粘接界面
    p.Set(faces=get_common_faces_between_sets(p, p.sets['SET-CELL-GRAIN'], p.sets['SET-CELL-INSULATION']), name='SET-FACES-GRAIN-INSULATION')

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    # 插入内聚力单元
    if insert_czm:
        insert_COH3D8_at_face_set(p, 'SET-FACES-GRAIN-INSULATION', 'COHESIVE-ELEMENTS-GRAIN-INSULATION')

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_gap_behind(model, part_name, points, lines, faces, dimension):
    # 变量赋值
    n, z_list, slot_deep, x0, angle_demolding_1, slot_ellipse_a, slot_ellipse_b, size, index_r, index_t, element_size, insert_czm, burn_offset = get_local_variables_common(dimension)
    r_cut, length_behind, p0, theta0_deg, p3, theta3_deg, theta_in_deg, beta, r1, r2, r3 = get_local_variables_behind(dimension)

    # 基本参数
    origin = (0.0, 0.0, 0.0)
    length = z_list[-2] * 2.0
    z = np.array(z_list)
    z_centers = (z[:-1] + z[1:]) / 2.0

    # SKETCH-GAP-Z
    s_gap_z = create_sketch_gap_z_front_behind(model, 'SKETCH-GAP-Z-FRONT-BEHIND', points)

    # 生成基础体
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

    # 生成额外基础体，z方向长度length_behind
    p.SolidExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_z, depth=length_behind, flipExtrudeDirection=OFF)

    # SKETCH-GAP-T
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, length / 2.0))
    s_gap_t = create_sketch_gap_t_front_behind(model, 'SKETCH-GAP-T-FRONT-BEHIND', t, points)

    # 生成额外基础体，z方向长度（z_list[-1] - z_list[-2]）
    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_gap_t, depth=(z_list[-1] - z_list[-2]), flipExtrudeDirection=ON)

    # 旋转切割头部外轮廓
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_outer, p0, p1, p2, p3, p4, p5, c1, c2, c3, delta1, delta2, delta3 = create_sketch_behind_outer(model, 'SKETCH-BEHIND-OUTER', t, points, index_r, index_t, p0, theta0_deg, p3, theta3_deg, theta_in_deg, r1, r2, r3, z_list)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_outer, angle=360.0, flipRevolveDirection=ON)

    # z剖分
    part_partition_z(p, d, z_list, is_minus=True)

    # theta剖分
    point1 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], length / 2.0))
    point2 = p.DatumPointByCoordinate(coords=(lines['02-12'][2][0], lines['02-12'][2][1], length / 2.0))
    point3 = p.DatumPointByCoordinate(coords=(lines['02-12'][1][0], lines['02-12'][1][1], 0.0))
    partition_plane = p.DatumPlaneByThreePoints(point1=d[point1.id], point2=d[point2.id], point3=d[point3.id])
    p.PartitionCellByDatumPlane(datumPlane=d[partition_plane.id], cells=p.cells)

    # 镜像
    if size == '1':
        p.Mirror(mirrorPlane=d[xz_plane.id], keepOriginal=ON)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)
    elif size == '1/2':
        pass
    elif size == '1/4':
        pass
    else:
        raise NotImplementedError('Unsupported size {}'.format(size))

    # XY面剖分
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    # 创建面
    create_surface_gap_common(p, points, dimension)

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')

    combine_surfaces(p, ['SURFACE-T1', 'SURFACE-T-1', 'SURFACE-Z1', 'SURFACE-Z-1'], 'SURFACE-TIE')

    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_behind_inner = create_sketch_behind_inner(model, 'SKETCH-BEHIND-INNER', t, x0, slot_deep, slot_ellipse_a, slot_ellipse_b, burn_offset)
    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_behind_inner, angle=360.0, flipRevolveDirection=ON)

    # 通过排除法确定内表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体），SET-CELL-GLUE-A
    set_name = 'SET-CELL-GLUE-A'
    p.Set(cells=p.cells, name=set_name)

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_shell(model, part_name, dimension):
    # 变量赋值
    l_c1_c2 = dimension['l_c1_c2']
    ellipse_ratio = dimension['ellipse_ratio']
    shell_r_in = dimension['shell_r_in']
    shell_r_out = dimension['shell_r_out']
    a_front = dimension['a_front']
    a_behind = dimension['a_behind']
    shell_theta_in_deg_front = dimension['shell_theta_in_deg_front']
    shell_theta_in_deg_behind = dimension['shell_theta_in_deg_behind']
    shell_theta_out_deg_front = dimension['shell_theta_out_deg_front']
    shell_theta_out_deg_behind = dimension['shell_theta_out_deg_behind']
    shell_r_out_at_a_front = dimension['shell_r_out_at_a_front']
    shell_r_out_at_a_behind = dimension['shell_r_out_at_a_behind']
    shell_r_in_front = dimension['shell_r_in_front']
    shell_r_in_behind = dimension['shell_r_in_behind']
    shell_l_c1_out = dimension['shell_l_c1_out']
    shell_l_c2_out = dimension['shell_l_c2_out']
    shell_points_front = dimension['shell_points_front']
    shell_points_behind = dimension['shell_points_behind']
    rotate_angle_deg = dimension['rotate_angle_deg']

    # 基本参数
    c1 = [0.0, 0.0]
    c2 = [l_c1_c2, 0.0]
    element_size = 60.0

    # 前后椭圆对象
    b_front = a_front / ellipse_ratio
    b_behind = a_behind / ellipse_ratio
    ellipse_front = Ellipse(c1[0], c1[1], a_front, b_front, long_axis='y')
    ellipse_behind = Ellipse(c2[0], c2[1], a_behind, b_behind, long_axis='y')

    # 前封头外轮廓
    line1 = Line2D((0, shell_r_out_at_a_front), math.tan(degrees_to_radians(shell_theta_out_deg_front)))
    line2 = Line2D((0, shell_r_out), (1, shell_r_out))
    p_front_out_1 = line1.get_intersection(line2)
    p_front_out_2 = [c1[0], shell_r_out_at_a_front]

    # 后封头外轮廓
    line1 = Line2D((c2[0], shell_r_out_at_a_behind), -math.tan(degrees_to_radians(shell_theta_out_deg_behind)))
    line2 = Line2D((0, shell_r_out), (1, shell_r_out))
    p_behind_out_1 = line1.get_intersection(line2)
    p_behind_out_2 = [c2[0], shell_r_out_at_a_behind]

    # 前封头内轮廓
    line1 = Line2D((0, a_front), math.tan(degrees_to_radians(shell_theta_in_deg_front)))
    line2 = Line2D((0, shell_r_in), (1, shell_r_in))
    p_front_in_1 = line1.get_intersection(line2)
    p_front_in_2 = [c1[0], a_front]
    p_front_in_3 = [ellipse_front.x_from_y(shell_r_in_front)[1], shell_r_in_front]
    p_front_in_4 = [c1[0] - shell_l_c1_out, shell_r_in_front]

    # 后封头内轮廓
    line1 = Line2D((c2[0], a_behind), -math.tan(degrees_to_radians(shell_theta_in_deg_behind)))
    line2 = Line2D((0, shell_r_in), (1, shell_r_in))
    p_behind_in_1 = line1.get_intersection(line2)
    p_behind_in_2 = [c2[0], a_behind]
    p_behind_in_3 = [ellipse_behind.x_from_y(shell_r_in_behind)[0], shell_r_in_behind]
    p_behind_in_4 = [c2[0] + shell_l_c2_out, shell_r_in_behind]

    # SKETCH-SHELL
    s = model.ConstrainedSketch(name='SKETCH-SHELL', sheetSize=2000.0)

    # 中段
    s.Line(point1=p_front_in_1, point2=p_behind_in_1)
    s.Line(point1=p_front_in_1, point2=p_front_in_2)
    s.Line(point1=p_behind_in_1, point2=p_behind_in_2)
    s.Line(point1=p_front_out_1, point2=p_behind_out_1)
    s.Line(point1=p_front_out_1, point2=p_front_out_2)
    s.Line(point1=p_behind_out_1, point2=p_behind_out_2)

    # 前封头
    l_trim_front = s.Line(point1=p_front_in_3, point2=p_front_in_4)
    ellipse_front = s.EllipseByCenterPerimeter(center=c1, axisPoint1=p_front_in_2, axisPoint2=[c1[0] + b_front, 0.0])
    s.autoTrimCurve(curve1=ellipse_front, point1=(c1[0] + b_front, 0.0))
    add_spline(s, shell_points_front)

    # 后封头
    l_trim_behind = s.Line(point1=p_behind_in_3, point2=p_behind_in_4)
    ellipse_behind = s.EllipseByCenterPerimeter(center=c2, axisPoint1=p_behind_in_2, axisPoint2=[c2[0] + b_behind, 0.0])
    s.autoTrimCurve(curve1=ellipse_behind, point1=(c2[0] + b_behind, 0.0))
    add_spline(s, shell_points_behind)

    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis = create_part_base_rotation(model, part_name, s, rotate_angle_deg)

    # 创建面
    create_surface_rotation_part_common(p, rotate_angle_deg)

    cylinder = Cylinder((0, 0, 0), (1, 0, 0), shell_r_in_front)
    create_surface_on_cylinder(p, cylinder, 'SURFACE-RIN-FRONT')
    cylinder = Cylinder((0, 0, 0), (1, 0, 0), shell_r_in_behind)
    create_surface_on_cylinder(p, cylinder, 'SURFACE-RIN-BEHIND')

    create_surface_rotation_part_common(p, rotate_angle_deg)
    point_middle_in = ((p_front_in_1[0] + p_behind_in_1[0]) / 2.0, (p_front_in_1[1] + p_behind_in_1[1]) / 2.0, 0)
    point_middle_in_rot = rotate_point_around_axis(point_middle_in, (0, 0, 0), (1, 0, 0), rotate_angle_deg / 2.0)
    p_face_middle = p.faces.findAt((point_middle_in_rot,))[0]
    p.Surface(side1Faces=p_face_middle.getFacesByFaceAngle(20), name='SURFACE-INNER')

    combine_surfaces(p, ['SURFACE-RIN-FRONT', 'SURFACE-RIN-BEHIND', 'SURFACE-INNER'], 'SURFACE-INNER')

    point_middle_out = ((p_front_out_1[0] + p_behind_out_1[0]) / 2.0, (p_front_out_1[1] + p_behind_out_1[1]) / 2.0, 0)
    point_middle_out_rot = rotate_point_around_axis(point_middle_out, (0, 0, 0), (1, 0, 0), rotate_angle_deg / 2.0)
    p_face_middle = p.faces.findAt((point_middle_out_rot,))[0]
    p.Surface(side1Faces=p_face_middle.getFacesByFaceAngle(20), name='SURFACE-OUTER')

    if 'SURFACE-R0' in p.surfaces.keys():
        del p.surfaces['SURFACE-R0']
    if 'SURFACE-R1' in p.surfaces.keys():
        del p.surfaces['SURFACE-R1']

    # 截面剖分
    cut_planes = [
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p_front_out_1[0]),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p_front_in_1[0]),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=c2[0]),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p_behind_out_1[0]),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p_behind_in_1[0]),
    ]
    for plane in cut_planes:
        try:
            p.PartitionCellByDatumPlane(datumPlane=d[plane.id], cells=p.cells)
        except:
            pass

    part_partition_rotation(p, d, n, xy_plane, x_axis)

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体）
    set_name = 'SET-CELL-SHELL'
    p.Set(cells=p.cells, name=set_name)

    # 创建集合（边）
    p_edges = get_edges_from_faces(p, p.surfaces['SURFACE-OUTER'].faces)
    p_edges_x0 = p.edges.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for edge in p_edges:
        edge_id = edge.index
        if edge.pointOn[0][0] == 0.0:
            p_edges_x0 += p.edges[edge_id:edge_id + 1]
    p.Set(edges=p_edges_x0, name='SET-EDGE-X0')

    # 赋予SECTION属性
    # set_section_common(p)
    normalAxisRegion = p.surfaces['SURFACE-OUTER']
    primaryAxisRegion = p.sets['SET-EDGE-X0']
    compositeLayup = p.CompositeLayup(name='COMPOSITELAYUP-1', description='', elementType=SOLID, symmetric=False, thicknessAssignment=FROM_SECTION)

    material_name = 'MATERIAL-SHELL-COMPOSITE'
    num_int_points = 3
    region = p.sets['SET-CELL-SHELL']
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

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_skirt_front(model, part_name, dimension):
    # 变量赋值
    skirt_r_out_front = dimension['skirt_r_out_front']
    skirt_r_in_1_front = dimension['skirt_r_in_1_front']
    skirt_r_in_2_front = dimension['skirt_r_in_2_front']
    skirt_l_1_front = dimension['skirt_l_1_front']
    skirt_l_2_front = dimension['skirt_l_2_front']
    skirt_offset_front = dimension['skirt_offset_front']
    rotate_angle_deg = dimension['rotate_angle_deg']

    # 基本参数
    c1 = [0.0, 0.0]
    element_size = 50.0

    point_1 = [c1[0] + skirt_offset_front, skirt_r_in_1_front]
    point_2 = [c1[0] + skirt_offset_front, skirt_r_out_front]
    point_3 = [c1[0] + skirt_offset_front + skirt_l_2_front, skirt_r_out_front]
    point_4 = [c1[0] + skirt_offset_front + skirt_l_2_front, skirt_r_in_2_front]
    point_5 = [c1[0] + skirt_offset_front + skirt_l_1_front, skirt_r_in_2_front]
    point_6 = [c1[0] + skirt_offset_front + skirt_l_1_front, skirt_r_in_1_front]

    # SKETCH-SKIRT-FRONT
    s = model.ConstrainedSketch(name='SKETCH-SKIRT-FRONT', sheetSize=2000.0)

    s.Line(point1=point_1, point2=point_2)
    s.Line(point1=point_2, point2=point_3)
    s.Line(point1=point_3, point2=point_4)
    s.Line(point1=point_4, point2=point_5)
    s.Line(point1=point_5, point2=point_6)
    s.Line(point1=point_6, point2=point_1)

    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis = create_part_base_rotation(model, part_name, s, rotate_angle_deg)

    # 切割壳体
    p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=model.sketches['SKETCH-SHELL'], angle=360.0, flipRevolveDirection=OFF)

    # 截面剖分
    cut_planes = [
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=point_5[0]),
    ]
    for plane in cut_planes:
        p.PartitionCellByDatumPlane(datumPlane=d[plane.id], cells=p.cells)

    part_partition_rotation(p, d, n, xy_plane, x_axis)

    # 创建面
    create_surface_rotation_part_common(p, rotate_angle_deg)
    # 通过排除法确定内表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体）
    set_name = 'SET-CELL-SKIRT'
    p.Set(cells=p.cells, name=set_name)

    # 创建集合（边）
    p_edges = get_edges_from_faces(p, p.surfaces['SURFACE-R1'].faces)
    p_edges_x0 = p.edges.getByBoundingBox(0, 0, 0, 0, 0, 0)
    x_low = p.cells.getBoundingBox()['low'][0]
    for edge in p_edges:
        edge_id = edge.index
        if abs(edge.pointOn[0][0] - x_low) < TOL:
            p_edges_x0 += p.edges[edge_id:edge_id + 1]
    p.Set(edges=p_edges_x0, name='SET-EDGE-X0')

    # 赋予SECTION属性
    # set_section_common(p)
    normalAxisRegion = p.surfaces['SURFACE-R1']
    primaryAxisRegion = p.sets['SET-EDGE-X0']
    compositeLayup = p.CompositeLayup(name='COMPOSITELAYUP-1', description='', elementType=SOLID, symmetric=False, thicknessAssignment=FROM_SECTION)

    material_name = 'MATERIAL-SKIRT-COMPOSITE'
    num_int_points = 3
    region = p.sets['SET-CELL-SKIRT']
    shell_composite_layup = np.genfromtxt('skirt_composite_layup.csv', delimiter=',')
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

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_skirt_behind(model, part_name, dimension):
    # 变量赋值
    l_c1_c2 = dimension['l_c1_c2']
    skirt_r_out_behind = dimension['skirt_r_out_behind']
    skirt_r_in_1_behind = dimension['skirt_r_in_1_behind']
    skirt_r_in_2_behind = dimension['skirt_r_in_2_behind']
    skirt_l_1_behind = dimension['skirt_l_1_behind']
    skirt_l_2_behind = dimension['skirt_l_2_behind']
    skirt_offset_behind = dimension['skirt_offset_behind']
    rotate_angle_deg = dimension['rotate_angle_deg']

    # 基本参数
    c2 = [l_c1_c2, 0.0]
    element_size = 50.0

    point_1 = [c2[0] + skirt_offset_behind, skirt_r_in_1_behind]
    point_2 = [c2[0] + skirt_offset_behind, skirt_r_out_behind]
    point_3 = [c2[0] + skirt_offset_behind - skirt_l_2_behind, skirt_r_out_behind]
    point_4 = [c2[0] + skirt_offset_behind - skirt_l_2_behind, skirt_r_in_2_behind]
    point_5 = [c2[0] + skirt_offset_behind - skirt_l_1_behind, skirt_r_in_2_behind]
    point_6 = [c2[0] + skirt_offset_behind - skirt_l_1_behind, skirt_r_in_1_behind]

    # SKETCH-SKIRT-BEHIND
    s = model.ConstrainedSketch(name='SKETCH-SKIRT-BEHIND', sheetSize=2000.0)

    s.Line(point1=point_1, point2=point_2)
    s.Line(point1=point_2, point2=point_3)
    s.Line(point1=point_3, point2=point_4)
    s.Line(point1=point_4, point2=point_5)
    s.Line(point1=point_5, point2=point_6)
    s.Line(point1=point_6, point2=point_1)

    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis = create_part_base_rotation(model, part_name, s, rotate_angle_deg)

    # 切割壳体
    p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=model.sketches['SKETCH-SHELL'], angle=360.0, flipRevolveDirection=OFF)

    # 截面剖分
    cut_planes = [
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=point_5[0]),
    ]
    for plane in cut_planes:
        p.PartitionCellByDatumPlane(datumPlane=d[plane.id], cells=p.cells)

    part_partition_rotation(p, d, n, xy_plane, x_axis)

    # 创建面
    create_surface_rotation_part_common(p, rotate_angle_deg)

    # 创建集合（面）
    create_face_set_from_surface(p)
    # 通过排除法确定内表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

    # 创建集合（体）
    set_name = 'SET-CELL-SKIRT'
    p.Set(cells=p.cells, name=set_name)

    # 创建集合（边）
    p_edges = get_edges_from_faces(p, p.surfaces['SURFACE-R1'].faces)
    p_edges_x0 = p.edges.getByBoundingBox(0, 0, 0, 0, 0, 0)
    x_low = p.cells.getBoundingBox()['low'][0]
    for edge in p_edges:
        edge_id = edge.index
        if abs(edge.pointOn[0][0] - x_low) < TOL:
            p_edges_x0 += p.edges[edge_id:edge_id + 1]
    p.Set(edges=p_edges_x0, name='SET-EDGE-X0')

    # 赋予SECTION属性
    # set_section_common(p)
    normalAxisRegion = p.surfaces['SURFACE-R1']
    primaryAxisRegion = p.sets['SET-EDGE-X0']
    compositeLayup = p.CompositeLayup(name='COMPOSITELAYUP-1', description='', elementType=SOLID, symmetric=False, thicknessAssignment=FROM_SECTION)

    material_name = 'MATERIAL-SKIRT-COMPOSITE'
    num_int_points = 3
    region = p.sets['SET-CELL-SKIRT']
    shell_composite_layup = np.genfromtxt('skirt_composite_layup.csv', delimiter=',')
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

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_flange_front(model, part_name, dimension):
    # 变量赋值
    ellipse_ratio = dimension['ellipse_ratio']
    a_front = dimension['a_front']
    flange_thickness_offset_front = dimension['flange_thickness_offset_front']
    flange_r_in_front = dimension['flange_r_in_front']
    flange_r_out_front = dimension['flange_r_out_front']
    cover_r_out_front = dimension['cover_r_out_front']
    flange_thickness_front = dimension['flange_thickness_front']
    flange_offset_front = dimension['flange_offset_front']
    flange_fillet_radius_front = dimension['flange_fillet_radius_front']
    flange_slope_deg_front = dimension['flange_slope_deg_front']
    rotate_angle_deg = dimension['rotate_angle_deg']

    # 基本参数
    c1 = [0.0, 0.0]
    element_size = 40.0
    b_front = a_front / ellipse_ratio
    ellipse = Ellipse(c1[0], c1[1], a_front, b_front, long_axis='y')
    ellipse_top_point = [c1[0], a_front]
    ellipse_right_point = [c1[0] + b_front, 0.0]
    r_mid = cover_r_out_front + flange_thickness_offset_front
    point_fillet = [ellipse.x_from_y(r_mid)[1], r_mid]
    point_left_conner = [flange_offset_front, r_mid]
    point_temp_0 = [c1[0], flange_r_out_front]
    point_temp_1 = [ellipse.x_from_y(flange_r_out_front)[1], flange_r_out_front]

    # SKETCH-FLANGE-FRONT
    s = model.ConstrainedSketch(name='SKETCH-FLANGE-FRONT', sheetSize=2000.0)

    e = s.EllipseByCenterPerimeter(center=c1, axisPoint1=ellipse_top_point, axisPoint2=ellipse_right_point)
    s.Line(point1=point_fillet, point2=point_left_conner)
    s.autoTrimCurve(curve1=e, point1=ellipse_right_point)

    # s.FilletByRadius(radius=flange_fillet_radius_front,
    #                  curve1=s.geometry.findAt(ellipse_top_point), nearPoint1=(ellipse.x_from_y(r_mid + 1.0)[1], r_mid + 1.0),
    #                  curve2=s.geometry.findAt(point_left_conner), nearPoint2=((point_fillet[0] + point_left_conner[0]) / 2, point_fillet[1]))

    geom_list = []
    for g in s.geometry.values():
        geom_list.append(g)
    s.offset(distance=flange_thickness_offset_front, objectList=geom_list, side=RIGHT)
    s.delete(objectList=geom_list)

    s.Line(point1=point_temp_0, point2=point_temp_1)

    ellipse_top_point_offset = [ellipse_top_point[0], ellipse_top_point[1] - flange_thickness_offset_front]
    curve = s.geometry.findAt((ellipse_top_point_offset))
    s.autoTrimCurve(curve1=curve, point1=ellipse_top_point_offset)

    curve = s.geometry.findAt((point_temp_1))
    s.autoTrimCurve(curve1=curve, point1=point_temp_1)

    point_left_conner_offset = [point_left_conner[0], cover_r_out_front]

    point_1 = [point_left_conner_offset[0], flange_r_in_front]
    point_2 = [point_left_conner_offset[0] + flange_thickness_front, flange_r_in_front]
    point_3 = [point_left_conner_offset[0] + flange_thickness_front, cover_r_out_front]

    s.Line(point1=point_left_conner_offset, point2=point_1)
    s.Line(point1=point_1, point2=point_2)
    s.Line(point1=point_2, point2=point_3)

    l1 = Line2D(point_3, np.tan(np.radians(flange_slope_deg_front)))
    l2 = Line2D(point_temp_0, point_temp_1)
    s.Line(point1=l1.get_intersection(l2), point2=point_3)
    curve = s.geometry.findAt((point_temp_0))
    s.autoTrimCurve(curve1=curve, point1=point_temp_0)

    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis = create_part_base_rotation(model, part_name, s, rotate_angle_deg)

    # 剖分
    cylinder = Cylinder((0, 0, 0), (1, 0, 0), cover_r_out_front)
    part_partition_by_cylinder(p, cylinder, p.cells)

    # 截面剖分
    part_partition_rotation(p, d, n, xy_plane, x_axis)

    # 创建面
    create_surface_rotation_part_common(p, rotate_angle_deg)
    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')
    combine_surfaces(p, ['SURFACE-R1', 'SURFACE-OUTER'], 'SURFACE-OUTER')
    combine_surfaces(p, ['SURFACE-R0', 'SURFACE-X1', 'SURFACE-OUTER'], 'SURFACE-TIE')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体）
    set_name = 'SET-CELL-FLANGE'
    p.Set(cells=p.cells, name=set_name)

    # 赋予SECTION属性
    set_section_common(p)

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_flange_behind(model, part_name, dimension):
    # 变量赋值
    l_c1_c2 = dimension['l_c1_c2']
    ellipse_ratio = dimension['ellipse_ratio']
    a_behind = dimension['a_behind']
    flange_thickness_offset_behind = dimension['flange_thickness_offset_behind']
    flange_r_in_behind = dimension['flange_r_in_behind']
    flange_r_out_behind = dimension['flange_r_out_behind']
    cover_r_out_behind = dimension['cover_r_out_behind']
    flange_thickness_behind = dimension['flange_thickness_behind']
    flange_offset_behind = dimension['flange_offset_behind']
    flange_fillet_radius_behind = dimension['flange_fillet_radius_behind']
    flange_slope_deg_behind = dimension['flange_slope_deg_behind']
    rotate_angle_deg = dimension['rotate_angle_deg']

    # 基本参数
    c2 = [l_c1_c2, 0.0]
    element_size = 40.0
    b_behind = a_behind / ellipse_ratio
    ellipse = Ellipse(c2[0], c2[1], a_behind, b_behind, long_axis='y')
    ellipse_top_point = [c2[0], a_behind]
    ellipse_left_point = [c2[0] - b_behind, 0.0]
    r_mid = cover_r_out_behind + flange_thickness_offset_behind
    point_fillet = [ellipse.x_from_y(r_mid)[0], r_mid]
    point_left_conner = [flange_offset_behind - flange_thickness_offset_behind, r_mid]
    point_right_conner = [flange_offset_behind, r_mid]
    point_temp_0 = [c2[0], flange_r_out_behind]
    point_temp_1 = [ellipse.x_from_y(flange_r_out_behind)[0], flange_r_out_behind]

    # SKETCH-FLANGE-BEHIND
    s = model.ConstrainedSketch(name='SKETCH-FLANGE-BEHIND', sheetSize=2000.0)

    e = s.EllipseByCenterPerimeter(center=c2, axisPoint1=ellipse_top_point, axisPoint2=ellipse_left_point)
    s.Line(point1=point_fillet, point2=point_right_conner)
    s.autoTrimCurve(curve1=e, point1=ellipse_left_point)

    # s.FilletByRadius(radius=flange_fillet_radius_behind,
    #                  curve1=s.geometry.findAt(ellipse_top_point), nearPoint1=(ellipse.x_from_y(r_mid + 1.0)[1], r_mid + 1.0),
    #                  curve2=s.geometry.findAt(point_left_conner), nearPoint2=((point_fillet[0] + point_left_conner[0]) / 2, point_fillet[1]))

    geom_list = []
    for g in s.geometry.values():
        geom_list.append(g)
    s.offset(distance=flange_thickness_offset_behind, objectList=geom_list, side=LEFT)
    s.delete(objectList=geom_list)

    s.Line(point1=point_temp_0, point2=point_temp_1)

    ellipse_top_point_offset = [ellipse_top_point[0], ellipse_top_point[1] - flange_thickness_offset_behind]
    curve = s.geometry.findAt((ellipse_top_point_offset))
    s.autoTrimCurve(curve1=curve, point1=ellipse_top_point_offset)

    curve = s.geometry.findAt((point_temp_1))
    s.autoTrimCurve(curve1=curve, point1=point_temp_1)

    point_right_conner_offset = [point_right_conner[0], cover_r_out_behind]

    point_1 = [point_right_conner_offset[0], flange_r_in_behind]
    point_2 = [point_right_conner_offset[0] - flange_thickness_behind, flange_r_in_behind]
    point_3 = [point_right_conner_offset[0] - flange_thickness_behind, cover_r_out_behind]

    s.Line(point1=point_right_conner_offset, point2=point_1)
    s.Line(point1=point_1, point2=point_2)
    s.Line(point1=point_2, point2=point_3)

    l1 = Line2D(point_3, np.tan(np.radians(flange_slope_deg_behind)))
    l2 = Line2D(point_temp_0, point_temp_1)
    s.Line(point1=l1.get_intersection(l2), point2=point_3)
    curve = s.geometry.findAt((point_temp_0))
    s.autoTrimCurve(curve1=curve, point1=point_temp_0)

    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis = create_part_base_rotation(model, part_name, s, rotate_angle_deg)

    # 剖分
    cylinder = Cylinder((0, 0, 0), (1, 0, 0), cover_r_out_behind)
    part_partition_by_cylinder(p, cylinder, p.cells)

    part_partition_rotation(p, d, n, xy_plane, x_axis)

    # 创建面
    create_surface_rotation_part_common(p, rotate_angle_deg)
    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-OUTER')
    combine_surfaces(p, ['SURFACE-R1', 'SURFACE-OUTER'], 'SURFACE-OUTER')
    combine_surfaces(p, ['SURFACE-R0', 'SURFACE-X0', 'SURFACE-OUTER'], 'SURFACE-TIE')

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体）
    set_name = 'SET-CELL-FLANGE'
    p.Set(cells=p.cells, name=set_name)

    # 赋予SECTION属性
    set_section_common(p)

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_insulation(model, part_name, dimension):
    # 变量赋值
    l_c1_c2 = dimension['l_c1_c2']
    ellipse_ratio = dimension['ellipse_ratio']

    shell_insulation_r_in = dimension['shell_insulation_r_in']
    shell_insulation_r_out = dimension['shell_insulation_r_out']

    shell_insulation_theta_in_deg_front = dimension['shell_insulation_theta_in_deg_front']
    shell_insulation_theta_in_deg_behind = dimension['shell_insulation_theta_in_deg_behind']

    shell_theta_in_deg_front = dimension['shell_theta_in_deg_front']
    shell_theta_in_deg_behind = dimension['shell_theta_in_deg_behind']

    a_front = dimension['a_front']
    a_behind = dimension['a_behind']
    shell_insulation_r_in_at_a_front = dimension['shell_insulation_r_in_at_a_front']
    shell_insulation_r_in_at_a_behind = dimension['shell_insulation_r_in_at_a_behind']

    shell_insulation_r_out_front = dimension['shell_insulation_r_out_front']
    shell_insulation_r_out_behind = dimension['shell_insulation_r_out_behind']

    shell_insulation_r_in_front = dimension['shell_insulation_r_in_front']
    shell_insulation_r_in_behind = dimension['shell_insulation_r_in_behind']

    shell_insulation_thickness_at_flange_front = dimension['shell_insulation_thickness_at_flange_front']
    shell_insulation_thickness_at_flange_behind = dimension['shell_insulation_thickness_at_flange_behind']

    shell_l_c1_out = dimension['shell_l_c1_out']
    shell_l_c2_out = dimension['shell_l_c2_out']
    flange_r_out_front = dimension['flange_r_out_front']
    flange_r_out_behind = dimension['flange_r_out_behind']
    flange_r_in_front = dimension['flange_r_in_front']
    flange_r_in_behind = dimension['flange_r_in_behind']
    shell_r_in_front = dimension['shell_r_in_front']
    shell_r_in_behind = dimension['shell_r_in_behind']

    rotate_angle_deg = dimension['rotate_angle_deg']

    p0_front = dimension['p0_front']
    theta0_deg_front = dimension['theta0_deg_front']
    p3_front = dimension['p3_front']
    theta3_deg_front = dimension['theta3_deg_front']
    r1_front = dimension['r1_front']
    r2_front = dimension['r2_front']
    r3_front = dimension['r3_front']

    p0_behind = dimension['p0_behind']
    theta0_deg_behind = dimension['theta0_deg_behind']
    p3_behind = dimension['p3_behind']
    theta3_deg_behind = dimension['theta3_deg_behind']
    r1_behind = dimension['r1_behind']
    r2_behind = dimension['r2_behind']
    r3_behind = dimension['r3_behind']

    shell_insulation_gap_front_r = dimension['shell_insulation_gap_front_r']
    shell_insulation_gap_front_l1 = dimension['shell_insulation_gap_front_l1']
    shell_insulation_gap_front_l2 = dimension['shell_insulation_gap_front_l2']

    front_points = [[-shell_l_c1_out, shell_insulation_r_out_front],
                    [-shell_l_c1_out, shell_insulation_r_out_front - shell_insulation_thickness_at_flange_front],
                    [-shell_l_c1_out + cover_thickness_front, shell_insulation_r_out_front - shell_insulation_thickness_at_flange_front],
                    [-shell_l_c1_out + cover_thickness_front, flange_r_in_front],
                    [-shell_l_c1_out + cover_thickness_front, shell_insulation_r_in_front]]
    behind_points = [[l_c1_c2 + shell_l_c2_out, shell_insulation_r_out_behind],
                     [l_c1_c2 + shell_l_c2_out, shell_insulation_r_out_behind - shell_insulation_thickness_at_flange_behind],
                     [l_c1_c2 + shell_l_c2_out - cover_thickness_behind, shell_insulation_r_out_behind - shell_insulation_thickness_at_flange_behind],
                     [l_c1_c2 + shell_l_c2_out - cover_thickness_behind, flange_r_in_behind],
                     [l_c1_c2 + shell_l_c2_out - cover_thickness_behind, shell_insulation_r_in_behind]]

    # 基本参数
    c1 = [0.0, 0.0]
    c2 = [l_c1_c2, 0.0]
    element_size = 60.0

    # 前后椭圆对象
    b_front = a_front / ellipse_ratio
    b_behind = a_behind / ellipse_ratio
    ellipse_front = Ellipse(c1[0], c1[1], a_front, b_front, long_axis='y')
    ellipse_behind = Ellipse(c2[0], c2[1], a_behind, b_behind, long_axis='y')

    # 前封头外轮廓
    line1 = Line2D((0, a_front), math.tan(degrees_to_radians(shell_theta_in_deg_front)))
    line2 = Line2D((0, shell_insulation_r_out), (1, shell_insulation_r_out))
    p_front_out_1 = line1.get_intersection(line2)
    p_front_out_2 = [c1[0], a_front]
    p_front_out_3 = [ellipse_front.x_from_y(shell_insulation_r_out_front)[1], shell_insulation_r_out_front]

    # 后封头外轮廓
    line1 = Line2D((c2[0], a_behind), -math.tan(degrees_to_radians(shell_theta_in_deg_behind)))
    line2 = Line2D((0, shell_insulation_r_out), (1, shell_insulation_r_out))
    p_behind_out_1 = line1.get_intersection(line2)
    p_behind_out_2 = [c2[0], a_behind]
    p_behind_out_3 = [ellipse_behind.x_from_y(shell_insulation_r_out_behind)[0], shell_insulation_r_out_behind]

    # 前封头内轮廓
    line1 = Line2D((0, shell_insulation_r_in_at_a_front), math.tan(degrees_to_radians(shell_insulation_theta_in_deg_front)))
    line2 = Line2D((0, shell_insulation_r_in), (1, shell_insulation_r_in))
    p_front_in_1 = line1.get_intersection(line2)
    p_front_in_2 = [c1[0], shell_insulation_r_in_at_a_front]

    # 后封头内轮廓
    line1 = Line2D((c2[0], shell_insulation_r_in_at_a_behind), -math.tan(degrees_to_radians(shell_insulation_theta_in_deg_behind)))
    line2 = Line2D((0, shell_insulation_r_in), (1, shell_insulation_r_in))
    p_behind_in_1 = line1.get_intersection(line2)
    p_behind_in_2 = [c2[0], shell_insulation_r_in_at_a_behind]

    s = model.ConstrainedSketch(name='SKETCH-INSULATION', sheetSize=2000.0)

    # 前封头
    l_trim_front = s.Line(point1=p_front_out_3, point2=(p_front_out_3[0] + 1.0, p_front_out_3[1]))
    ellipse_front = s.EllipseByCenterPerimeter(center=c1, axisPoint1=p_front_out_2, axisPoint2=[c1[0] + b_front, 0.0])
    s.autoTrimCurve(curve1=ellipse_front, point1=(c1[0] - b_front, 0.0))
    s.delete(objectList=(s.geometry[l_trim_front.id],))

    arcs_front = solve_three_arcs(p0_front, theta0_deg_front, p3_front, theta3_deg_front, r1_front, r2_front, r3_front)
    s.ArcByCenterEnds(center=arcs_front['c1'], point1=p0_front, point2=arcs_front['p1'], direction=get_direction(arcs_front['delta1']))
    s.ArcByCenterEnds(center=arcs_front['c2'], point1=arcs_front['p1'], point2=arcs_front['p2'], direction=get_direction(arcs_front['delta2']))
    s.ArcByCenterEnds(center=arcs_front['c3'], point1=arcs_front['p2'], point2=p3_front, direction=get_direction(arcs_front['delta3']))

    point_list_front = [p_front_out_3] + front_points + [[p0_front[0], shell_insulation_r_in_front], p0_front]
    for i in range(len(point_list_front) - 1):
        s.Line(point1=point_list_front[i], point2=point_list_front[i + 1])

    # 后封头
    l_trim_behind = s.Line(point1=p_behind_out_3, point2=(p_behind_out_3[0] + 1.0, p_behind_out_3[1]))
    ellipse_behind = s.EllipseByCenterPerimeter(center=c2, axisPoint1=p_behind_out_2, axisPoint2=[c2[0] + b_behind, 0.0])
    s.autoTrimCurve(curve1=ellipse_behind, point1=(c2[0] + b_behind, 0.0))
    s.delete(objectList=(s.geometry[l_trim_behind.id],))

    arcs_behind = solve_three_arcs(p0_behind, theta0_deg_behind, p3_behind, theta3_deg_behind, r1_behind, r2_behind, r3_behind)
    s.ArcByCenterEnds(center=arcs_behind['c1'], point1=p0_behind, point2=arcs_behind['p1'], direction=get_direction(arcs_behind['delta1']))
    s.ArcByCenterEnds(center=arcs_behind['c2'], point1=arcs_behind['p1'], point2=arcs_behind['p2'], direction=get_direction(arcs_behind['delta2']))
    s.ArcByCenterEnds(center=arcs_behind['c3'], point1=arcs_behind['p2'], point2=p3_behind, direction=get_direction(arcs_behind['delta3']))

    point_list_behind = [p_behind_out_3] + behind_points + [[p0_behind[0], shell_insulation_r_in_behind], p0_behind]
    for i in range(len(point_list_behind) - 1):
        s.Line(point1=point_list_behind[i], point2=point_list_behind[i + 1])

    # 中段外侧
    s.Line(point1=p_front_out_1, point2=p_behind_out_1)
    s.Line(point1=p_front_out_1, point2=p_front_out_2)
    s.Line(point1=p_behind_out_1, point2=p_behind_out_2)

    # 中段内侧
    s.Line(point1=p_front_in_1, point2=p_behind_in_1)
    s.Line(point1=p_front_in_1, point2=p_front_in_2)
    s.Line(point1=p_behind_in_1, point2=p_behind_in_2)

    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis = create_part_base_rotation(model, part_name, s, rotate_angle_deg)

    # 切割前接头
    p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=model.sketches['SKETCH-FLANGE-FRONT'], angle=360.0, flipRevolveDirection=OFF)

    if shell_insulation_gap_front_r > shell_insulation_r_in_front:
        s_insulation_gap_front = create_sketch_gap_front(model, 'SKETCH-INSULATION-GAP-FRONT', p0_front, theta0_deg_front, p3_front, theta3_deg_front, r1_front, r2_front, r3_front, shell_l_c1_out,
                                                         shell_insulation_gap_front_r, shell_insulation_gap_front_l1, shell_insulation_gap_front_l2)
        p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=model.sketches['SKETCH-INSULATION-GAP-FRONT'], angle=360.0, flipRevolveDirection=OFF)

    # 切割后接头
    p.CutRevolve(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=model.sketches['SKETCH-FLANGE-BEHIND'], angle=360.0, flipRevolveDirection=OFF)

    # 创建面
    create_surface_rotation_part_common(p, rotate_angle_deg)
    point_middle_in = ((p_front_in_1[0] + p_behind_in_1[0]) / 2.0, (p_front_in_1[1] + p_behind_in_1[1]) / 2.0, 0)
    point_middle_in_rot = rotate_point_around_axis(point_middle_in, (0, 0, 0), (1, 0, 0), rotate_angle_deg / 2.0)
    p_face_middle = p.faces.findAt((point_middle_in_rot,))[0]
    p.Surface(side1Faces=p_face_middle.getFacesByFaceAngle(20), name='SURFACE-INNER')

    point_middle_out = ((p_front_out_1[0] + p_behind_out_1[0]) / 2.0, (p_front_out_1[1] + p_behind_out_1[1]) / 2.0, 0)
    point_middle_out_rot = rotate_point_around_axis(point_middle_out, (0, 0, 0), (1, 0, 0), rotate_angle_deg / 2.0)
    p_face_middle = p.faces.findAt((point_middle_out_rot,))[0]
    p.Surface(side1Faces=p_face_middle.getFacesByFaceAngle(20), name='SURFACE-OUTER')

    cylinder = Cylinder((0, 0, 0), (1, 0, 0), shell_r_in_front)
    create_surface_on_cylinder(p, cylinder, 'SURFACE-ROUT-FRONT')
    cylinder = Cylinder((0, 0, 0), (1, 0, 0), shell_r_in_behind)
    create_surface_on_cylinder(p, cylinder, 'SURFACE-ROUT-BEHIND')
    combine_surfaces(p, ['SURFACE-OUTER', 'SURFACE-ROUT-FRONT', 'SURFACE-ROUT-BEHIND'], 'SURFACE-OUTER')

    cylinder = Cylinder((0, 0, 0), (1, 0, 0), shell_insulation_r_in_front)
    create_surface_on_cylinder(p, cylinder, 'SURFACE-RIN-FRONT')
    cylinder = Cylinder((0, 0, 0), (1, 0, 0), shell_insulation_r_in_behind)
    create_surface_on_cylinder(p, cylinder, 'SURFACE-RIN-BEHIND')

    # 通过排除法确定外表面
    given_surface_names = list(p.surfaces.keys())
    p_faces = get_faces_of_p_remove_given_surface_names(p, given_surface_names)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-FLANGE')

    p_faces_1 = p.faces.getByBoundingBox(-PEN, -PEN, -PEN, c1[0], PEN, PEN)
    p_faces_2 = p.surfaces['SURFACE-FLANGE'].faces
    create_surface_by_intersection(p, p_faces_1, p_faces_2, 'SURFACE-FLANGE-FRONT')

    p_faces_1 = p.faces.getByBoundingBox(c2[0], -PEN, -PEN, c2[0] + PEN, PEN, PEN)
    p_faces_2 = p.surfaces['SURFACE-FLANGE'].faces
    create_surface_by_intersection(p, p_faces_1, p_faces_2, 'SURFACE-FLANGE-BEHIND')

    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face in p.surfaces['SURFACE-INNER'].faces:
        if face.pointOn[0][0] <= 0:
            face_id = face.index
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER-FRONT')

    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face in p.surfaces['SURFACE-INNER'].faces:
        if face.pointOn[0][0] >= l_c1_c2:
            face_id = face.index
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER-BEHIND')

    p_faces_1 = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    p_faces_2 = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face in p.surfaces['SURFACE-FLANGE-FRONT'].faces:
        face_id = face.index
        if face.pointOn[0][0] >= p0_front[0] - shell_insulation_gap_front_l1 - shell_insulation_gap_front_l2:
            p_faces_1 += p.faces[face_id:face_id + 1]
        else:
            p_faces_2 += p.faces[face_id:face_id + 1]
    if p_faces_1:
        p.Surface(side1Faces=p_faces_1, name='SURFACE-GAP-FRONT')
    if p_faces_2:
        p.Surface(side1Faces=p_faces_2, name='SURFACE-FLANGE-FRONT')

    # 头部多边形切割
    # polygon_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p0_front[0])
    # t = p.MakeSketchTransform(sketchPlane=d[polygon_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, origin=(p0_front[0], 0.0, 0.0))
    # s_polygon = create_sketch_polygon(model, 'SKETCH-POLYGON', t, x0, n)
    # p_faces = p.faces.findAt((p0_front[0], p0_front[1] - TOL, 0.0,))
    # p.PartitionFaceBySketch(sketchUpEdge=d[y_axis.id], faces=p_faces, sketch=s_polygon)

    # 截面剖分
    if rotate_angle_deg == 360.0:
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    # 草图剖分
    is_sketch_partition = True
    if is_sketch_partition:
        s_insulation_partition = model.ConstrainedSketch(name='SKETCH-INSULATION-PARTITION', sheetSize=200.0)
        # s_insulation_partition.Line(point1=(c1[0], flange_r_out_front), point2=(c1[0] - b_front, flange_r_out_front))
        # s_insulation_partition.Line(point1=(c2[0], flange_r_out_behind), point2=(c2[0] + b_behind, flange_r_out_behind))
        # s_insulation_partition.Line(point1=arcs_front['c1'], point2=arcs_front['p1'])
        # s_insulation_partition.Line(point1=arcs_front['c2'], point2=arcs_front['p2'])
        # s_insulation_partition.Line(point1=arcs_behind['c1'], point2=arcs_behind['p1'])
        # s_insulation_partition.Line(point1=arcs_behind['c2'], point2=arcs_behind['p2'])
        # p0_front_offset = move_along_direction(p3_front, (p0_front[0] - arcs_front['c1'][0], p0_front[1] - arcs_front['c1'][1]), PEN)
        # p0_behind_offset = move_along_direction(p3_behind, (p0_behind[0] - arcs_behind['c1'][0], p0_behind[1] - arcs_behind['c1'][1]), PEN)
        # s_insulation_partition.Line(point1=p0_front, point2=p0_front_offset)
        # s_insulation_partition.Line(point1=p0_behind, point2=p0_behind_offset)

        arcs_front_p1_offset = move_along_direction(arcs_front['p1'], (arcs_front['p1'][0] - arcs_front['c1'][0], arcs_front['p1'][1] - arcs_front['c1'][1]), PEN)
        arcs_front_p2_offset = move_along_direction(arcs_front['p2'], (arcs_front['p2'][0] - arcs_front['c2'][0], arcs_front['p2'][1] - arcs_front['c2'][1]), PEN)
        arcs_behind_p1_offset = move_along_direction(arcs_behind['p1'], (arcs_behind['p1'][0] - arcs_behind['c1'][0], arcs_behind['p1'][1] - arcs_behind['c1'][1]), PEN)
        arcs_behind_p2_offset = move_along_direction(arcs_behind['p2'], (arcs_behind['p2'][0] - arcs_behind['c2'][0], arcs_behind['p2'][1] - arcs_behind['c2'][1]), PEN)
        arcs_front_p1_offset_tol = move_along_direction(arcs_front['p1'], (arcs_front['p1'][0] - arcs_front['c1'][0], arcs_front['p1'][1] - arcs_front['c1'][1]), 1.0)
        arcs_front_p2_offset_tol = move_along_direction(arcs_front['p2'], (arcs_front['p2'][0] - arcs_front['c2'][0], arcs_front['p2'][1] - arcs_front['c2'][1]), 1.0)
        arcs_behind_p1_offset_tol = move_along_direction(arcs_behind['p1'], (arcs_behind['p1'][0] - arcs_behind['c1'][0], arcs_behind['p1'][1] - arcs_behind['c1'][1]), 1.0)
        arcs_behind_p2_offset_tol = move_along_direction(arcs_behind['p2'], (arcs_behind['p2'][0] - arcs_behind['c2'][0], arcs_behind['p2'][1] - arcs_behind['c2'][1]), 1.0)
        s_insulation_partition.Line(point1=arcs_front['p1'], point2=arcs_front_p1_offset)
        s_insulation_partition.Line(point1=arcs_front['p2'], point2=arcs_front_p2_offset)
        s_insulation_partition.Line(point1=arcs_behind['p1'], point2=arcs_behind_p1_offset)
        s_insulation_partition.Line(point1=arcs_behind['p2'], point2=arcs_behind_p2_offset)
        p_faces = p.faces.getByBoundingBox(-PEN, -PEN, 0, c2[0] + PEN, PEN, TOL)
        p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketchOrientation=BOTTOM, sketch=s_insulation_partition)
        sweep_edge_point = rotate_point_around_axis((0.0, a_front, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), TOL)
        p.DatumPointByCoordinate(coords=sweep_edge_point)
        sweep_edge = p.edges.findAt(sweep_edge_point)
        partition_edges = []
        for partition_edge_point in [arcs_front_p1_offset_tol, arcs_front_p2_offset_tol, arcs_behind_p1_offset_tol, arcs_behind_p2_offset_tol]:
            x, y = partition_edge_point
            edge_sequence = p.edges.findAt((x, y, 0.0))
            if edge_sequence is not None:
                partition_edges.append(edge_sequence)
        p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

        if rotate_angle_deg == 360.0:
            sweep_edge_point = rotate_point_around_axis((0.0, a_front, 0.0), (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), -TOL)
            p.DatumPointByCoordinate(coords=sweep_edge_point)
            sweep_edge = p.edges.findAt(sweep_edge_point)
            partition_edges = []
            for partition_edge_point in [arcs_front_p1_offset_tol, arcs_front_p2_offset_tol, arcs_behind_p1_offset_tol, arcs_behind_p2_offset_tol]:
                x, y = partition_edge_point
                edge_sequence = p.edges.findAt((x, y, 0.0))
                if edge_sequence is not None:
                    partition_edges.append(edge_sequence)
            p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    part_partition_rotation(p, d, n, xy_plane, x_axis)

    cylinder = Cylinder((0, 0, 0), (1, 0, 0), shell_insulation_gap_front_r)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if cylinder.is_point_on_cylinder(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-GAP-FRONT-R')
        p.PartitionCellByExtendFace(extendFace=p_faces[0], cells=p.cells.getByBoundingBox(-PEN, -PEN, -PEN, 0.0, PEN, PEN))

    # 截面剖分
    cut_planes = [
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=c2[0]),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p_front_out_1[0]),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p_behind_out_1[0]),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p_front_in_1[0]),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p_behind_in_1[0]),
    ]
    for plane in cut_planes:
        p.PartitionCellByDatumPlane(datumPlane=d[plane.id], cells=p.cells)

    # 面扩展剖分
    for radius in [flange_r_out_front, shell_r_in_front - shell_insulation_thickness_at_flange_front, shell_r_in_front, flange_r_in_front]:
        cylinder = Cylinder((0, 0, 0), (1, 0, 0), radius)
        p_cells_front = p.cells.getByBoundingBox(-PEN, -PEN, -PEN, c1[0], PEN, PEN)
        part_partition_by_cylinder(p, cylinder, p_cells_front)

    for radius in [flange_r_out_behind, shell_r_in_behind - shell_insulation_thickness_at_flange_behind, shell_r_in_behind, flange_r_in_behind]:
        cylinder = Cylinder((0, 0, 0), (1, 0, 0), radius)
        p_cells_behind = p.cells.getByBoundingBox(c1[0], -PEN, -PEN, c2[0] + PEN, PEN, PEN)
        part_partition_by_cylinder(p, cylinder, p_cells_behind)

    # 截面剖分
    cut_planes = [
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p_front_out_3[0]),
        p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=p_behind_out_3[0]),
        # p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=(p_front_out_3[0] - shell_l_c1_out) / 2.0),
        # p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=(p_behind_out_3[0] + l_c1_c2 + shell_l_c2_out) / 2.0),
    ]
    for plane in cut_planes:
        p.PartitionCellByDatumPlane(datumPlane=d[plane.id], cells=p.cells)

    # 生成网格
    # 切割后的体在前后法兰切处存在一些边被打断，导致网格划分失败，因此先进行虚拟拓扑合并处理
    # p.createVirtualTopology(mergeShortEdges=True, shortEdgeThreshold=1000.0,
    #                         mergeSmallFaces=False, mergeSliverFaces=False, mergeSmallAngleFaces=False,
    #                         mergeThinStairFaces=False, ignoreRedundantEntities=False,
    #                         cornerAngleTolerance=30.0, applyBlendControls=False)
    generate_part_mesh(p, element_size=element_size)

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 创建集合（体）
    set_name = 'SET-CELL-INSULATION'
    p.Set(cells=p.cells, name=set_name)

    # 赋予SECTION属性
    set_section_common(p)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_cover_front(model, part_name, dimension):
    # 变量赋值
    cover_r_out_front = dimension['cover_r_out_front']
    cover_thickness_front = dimension['cover_thickness_front']
    cover_offset_front = dimension['cover_offset_front']
    rotate_angle_deg = dimension['rotate_angle_deg']

    # 基本参数
    element_size = 25.0
    point_1 = [cover_offset_front, 0.0]
    point_2 = [cover_offset_front + cover_thickness_front, 0.0]
    point_3 = [cover_offset_front + cover_thickness_front, cover_r_out_front]
    point_4 = [cover_offset_front, cover_r_out_front]

    # SKETCH-COVER-FRONT
    s = model.ConstrainedSketch(name='SKETCH-COVER-FRONT', sheetSize=2000.0)
    s.Line(point1=point_1, point2=point_2)
    s.Line(point1=point_2, point2=point_3)
    s.Line(point1=point_3, point2=point_4)
    s.Line(point1=point_1, point2=point_4)
    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis = create_part_base_rotation(model, part_name, s, rotate_angle_deg)

    # 创建面
    create_surface_rotation_part_common(p, rotate_angle_deg)

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 截面剖分
    if rotate_angle_deg == 360.0:
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)

    # 创建集合（体）
    set_name = 'SET-CELL-COVER'
    p.Set(cells=p.cells, name=set_name)

    # 赋予SECTION属性
    set_section_common(p)

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_cover_behind(model, part_name, dimension):
    # 变量赋值
    cover_r_out_behind = dimension['cover_r_out_behind']
    cover_thickness_behind = dimension['cover_thickness_behind']
    cover_offset_behind = dimension['cover_offset_behind']
    rotate_angle_deg = dimension['rotate_angle_deg']

    # 基本参数
    element_size = 25.0
    point_1 = [cover_offset_behind, 0.0]
    point_2 = [cover_offset_behind + cover_thickness_behind, 0.0]
    point_3 = [cover_offset_behind + cover_thickness_behind, cover_r_out_behind]
    point_4 = [cover_offset_behind, cover_r_out_behind]

    # SKETCH-COVER-BEHIND
    s = model.ConstrainedSketch(name='SKETCH-COVER-BEHIND', sheetSize=2000.0)
    s.Line(point1=point_1, point2=point_2)
    s.Line(point1=point_2, point2=point_3)
    s.Line(point1=point_3, point2=point_4)
    s.Line(point1=point_1, point2=point_4)
    s.ConstructionLine(point1=(0.0, 0.0), point2=(1.0, 0.0))

    # 生成基础体
    p, d, xy_plane, yz_plane, xz_plane, x_axis, y_axis, z_axis = create_part_base_rotation(model, part_name, s, rotate_angle_deg)

    # 创建面
    create_surface_rotation_part_common(p, rotate_angle_deg)

    # 创建集合（面）
    create_face_set_from_surface(p)

    # 截面剖分
    if rotate_angle_deg == 360.0:
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
        p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)

    # 创建集合（体）
    set_name = 'SET-CELL-COVER'
    p.Set(cells=p.cells, name=set_name)

    # 赋予SECTION属性
    set_section_common(p)

    # 生成网格
    generate_part_mesh(p, element_size=element_size)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


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


def part_partition_z(p, d, z_list, is_minus=False):
    xy_plane_z = {}
    for i in range(1, len(z_list) - 1):
        if is_minus:
            xy_plane_z[i] = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=-z_list[i])
        else:
            xy_plane_z[i] = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=z_list[i])
        p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z[i].id], cells=p.cells)
    return xy_plane_z


def part_partition_p1p(p, d, p1p):
    # p1 = [x0 + slot_deep, -slot_ellipse_a]
    # offset = p1[0] * np.cos(degrees_to_radians(180.0 / n)) - p1[1] * np.sin(degrees_to_radians(180.0 / n))
    offset = p1p[0]
    if offset >= p.cells.getBoundingBox()['low'][0]:
        yz_plane_slot = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=offset)
        p.PartitionCellByDatumPlane(datumPlane=d[yz_plane_slot.id], cells=p.cells)


def part_partition_rotation(p, d, n, xy_plane, x_axis):
    # if rotate_angle_deg == 360.0:
    #     p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)
    #     p.PartitionCellByDatumPlane(datumPlane=d[xz_plane.id], cells=p.cells)

    for i in range(0, n):
        angle = i * 360.0 / n
        cut_plane = p.DatumPlaneByRotation(plane=d[xy_plane.id], axis=d[x_axis.id], angle=angle)
        try:
            p.PartitionCellByDatumPlane(datumPlane=d[cut_plane.id], cells=p.cells)
        except:
            pass


def create_sets_block_common(p, faces, dimension):
    z_list = dimension['z_list']
    index_t = dimension['index_t']
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

    if index_t >= 3 and faces.shape[1] >= 3:
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


def create_sets_block_same_volume(p):
    for set_name in ['SET-CELL-GRAIN', 'SET-CELL-INSULATION', 'SET-CELL-GLUE-A', 'SET-CELL-GLUE-B']:
        if set_name in p.sets.keys():
            p_cells = p.sets[set_name].cells
            p_cells = get_same_volume_cells(p, p_cells)
            p.Set(cells=p_cells, name=set_name)


def create_sets_z_t_face(p, points, dimension, nz, nt, set_name):
    z_list = dimension['z_list']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    slot_deep = dimension['slot_deep']
    burn_offset = dimension['burn_offset']
    length = z_list[-1 - nz] * 2.0

    p1 = (points[0, 0][0], points[0, 0][1], length / 2.0)
    p2 = (points[0, 1][0], points[0, 1][1], length / 2.0)
    p3 = (points[1, 0][0], points[1, 0][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and is_face_in_set(p.faces[face_id], p.sets[set_name]):
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Set(faces=p_faces, name=set_name + '-Z1')

    p1 = (points[0, 0][0], points[0, 0][1], -length / 2.0)
    p2 = (points[0, 1][0], points[0, 1][1], -length / 2.0)
    p3 = (points[1, 0][0], points[1, 0][1], -length / 2.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and is_face_in_set(p.faces[face_id], p.sets[set_name]):
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Set(faces=p_faces, name=set_name + '-Z-1')

    p1 = (points[0, index_t - nt][0], points[0, index_t - nt][1], 0.0)
    p2 = (points[index_r, index_t - nt][0], points[index_r, index_t - nt][1], 0.0)
    p3 = (points[0, index_t - nt][0], points[0, index_t - nt][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and is_face_in_set(p.faces[face_id], p.sets[set_name]):
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Set(faces=p_faces, name=set_name + '-T1')

    p1 = (points[0, index_t - nt][0], -points[0, index_t - nt][1], 0.0)
    p2 = (points[index_r, index_t - nt][0], -points[index_r, index_t - nt][1], 0.0)
    p3 = (points[0, index_t - nt][0], -points[0, index_t - nt][1], length / 2.0)
    plane = Plane(p1, p2, p3)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and is_face_in_set(p.faces[face_id], p.sets[set_name]):
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Set(faces=p_faces, name=set_name + '-T-1')


def create_surface_slot(p, ref_point_1, ref_point_2, z_begin, z_end, size, is_middle=True):
    x1 = ref_point_2[0]
    y1 = ref_point_2[1]
    if ref_point_1[1] > 0.0:
        p_faces = p.faces.getByBoundingBox(0, TOL, z_begin, x1 * 1.05, y1 * (1.0 + TOL), z_end)
    else:
        p_faces = p.faces.getByBoundingBox(0, 0, z_begin, x1 * 1.05, y1 * (1.0 + TOL), z_end)
    p_faces = get_mirror_faces(p, p_faces, size, is_middle)
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-SLOT')


def create_surface_block_common(p, points, dimension):
    z_list = dimension['z_list']
    index_r = dimension['index_r']
    index_t = dimension['index_t']
    slot_deep = dimension['slot_deep']
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


def create_surface_gap_common(p, points, dimension):
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


def set_section_common(p):
    set_name = 'SET-CELL-GRAIN'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-GRAIN', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'SET-CELL-INSULATION'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-INSULATION', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'SET-CELL-SHELL'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-SHELL', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'SET-CELL-SKIRT'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-SHELL', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'SET-CELL-FLANGE'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-STEEL', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'SET-CELL-COVER'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-STEEL', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'SET-CELL-GLUE-A'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-GLUE', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'SET-CELL-GLUE-B'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-GLUE-WALL', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)

    set_name = 'COHESIVE-ELEMENTS-GRAIN-INSULATION'
    if set_name in p.sets.keys():
        p.SectionAssignment(region=p.sets[set_name], sectionName='SECTION-CZM', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='', thicknessAssignment=FROM_SECTION)


def plot_blocks_map(block, figsize=(8, 8), is_show=True, is_save=True, save_path='blocks.png'):
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
    fig, ax = plt.subplots(figsize=figsize)

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
    if is_save:
        plt.savefig(save_path, dpi=300)

    if is_show:
        plt.show()


def print_sketch(session, model, viewport, sketch_name):
    s = model.ConstrainedSketch(name='__edit__', objectToCopy=mdb.models['Model-1'].sketches[sketch_name])
    s.setPrimaryObject(option=STANDALONE)
    s.Spot(point=(0, 0))
    s.sketchOptions.setValues(grid=OFF)
    if 'OUTER' in sketch_name or 'INNER' in sketch_name:
        viewport.view.rotate(xAngle=90, yAngle=90, zAngle=0, mode=MODEL)
    viewport.view.fitView()
    session.printToFile(fileName=sketch_name + '.png', format=PNG, canvasObjects=(viewport,))
    s.unsetPrimaryObject()
    del model.sketches['__edit__']


def print_part(session, model, viewport, part_name):
    p = model.parts[part_name]
    viewport.setValues(displayedObject=p)
    viewport.view.setValues(session.views['Iso'])
    viewport.view.rotate(xAngle=0, yAngle=0, zAngle=-90, mode=MODEL)
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


def find_geos_relative_to_x(geo_list, x_val, mode='intersect'):
    """
    查找 geo_list 中与垂直线 x = x_val 有特定位置关系的几何对象。

    参数:
        geo_list: 几何对象列表
        x_val:    给定的 x 坐标
        mode:     判定模式
                  - 'strict'   : 严格两侧（左< x <右），端点恰好在线上不算。
                  - 'intersect': 相交或接触（默认）。包含端点在线上且另一侧有点的情况，
                                 适用于 breakCurve 分割，不包含完全与线重叠的退化情况。
                  - 'touch'    : 专门筛选出有顶点恰好在 x_val 上的几何。
    """
    result = []
    tol = 1e-10  # 浮点数容差

    for geo in geo_list:
        vertices = geo.getVertices()
        x_coords = [v.coords[0] for v in vertices]

        # 判断三个状态
        has_left = any(x < x_val - tol for x in x_coords)
        has_right = any(x > x_val + tol for x in x_coords)
        has_on = any(abs(x - x_val) <= tol for x in x_coords)

        if mode == 'strict':
            # 必须严格一左一右，忽略端点恰好在上的情况
            if has_left and has_right:
                result.append(geo)

        elif mode == 'touch':
            # 只要某个端点刚好在这条线上（常用于寻找切点或交点）
            if has_on:
                result.append(geo)

        else:  # mode == 'intersect'
            # 条件：1. 左右各有点；2. 或者端点在上，且另外还有点在左边或右边
            # 这样既包含跨越，也包含从一侧接触上来的情况。
            # 特别注意：排除所有顶点都在线上（即完全重叠）的退化几何。
            if (has_left and has_right) or (has_on and (has_left or has_right)):
                result.append(geo)

    return result


def find_geos_in_xy_interval(geo_list, x_min=None, x_max=None, y_min=None, y_max=None, include_min_x=True, include_max_x=True, include_min_y=True, include_max_y=True, use_tol=True):
    """
    查找 geo_list 中，其 x 坐标范围与指定 x 区间有交集，且 y 坐标范围与指定 y 区间有交集的几何对象。
    区间可为开或闭，端点可为正负无穷（None 表示无限制）。

    参数:
        geo_list: 几何对象列表，每个对象需实现 getVertices() 方法，
                  顶点需有 coords[0] 作为 x 坐标，coords[1] 作为 y 坐标（二维或三维点）。
        x_min:         x 区间左端点，None 表示负无穷。
        x_max:         x 区间右端点，None 表示正无穷。
        y_min:         y 区间左端点，None 表示负无穷。
        y_max:         y 区间右端点，None 表示正无穷。
        include_min_x: bool，x 区间是否包含左端点（True 为闭，False 为开）。
        include_max_x: bool，x 区间是否包含右端点（True 为闭，False 为开）。
        include_min_y: bool，y 区间是否包含左端点（True 为闭，False 为开）。
        include_max_y: bool，y 区间是否包含右端点（True 为闭，False 为开）。
        use_tol:       bool，是否使用容差（1e-10）进行比较，False 则为严格数学比较。

    返回:
        同时满足 x、y 区间交集条件的几何对象列表。
    """
    result = []
    tol = 1e-10 if use_tol else 0.0

    # 无效区间检查（仅当 x_min 和 x_max 均非 None 时）
    if x_min is not None and x_max is not None and x_min > x_max:
        return result
    if y_min is not None and y_max is not None and y_min > y_max:
        return result

    for geo in geo_list:
        vertices = geo.getVertices()
        if not vertices:
            continue

        # 提取 x 和 y 坐标
        try:
            x_coords = [v.coords[0] for v in vertices]
            y_coords = [v.coords[1] for v in vertices]
        except (IndexError, AttributeError):
            # 若顶点缺少坐标或无法索引，跳过该几何
            continue

        xmin, xmax = min(x_coords), max(x_coords)
        ymin, ymax = min(y_coords), max(y_coords)

        # ---- x 边界条件 ----
        left_ok_x = True
        if x_min is not None:
            if include_min_x:
                left_ok_x = xmin >= x_min - tol
            else:
                left_ok_x = xmin > x_min + tol

        right_ok_x = True
        if x_max is not None:
            if include_max_x:
                right_ok_x = xmax <= x_max + tol
            else:
                right_ok_x = xmax < x_max - tol

        # ---- y 边界条件 ----
        left_ok_y = True
        if y_min is not None:
            if include_min_y:
                left_ok_y = ymin >= y_min - tol
            else:
                left_ok_y = ymin > y_min + tol

        right_ok_y = True
        if y_max is not None:
            if include_max_y:
                right_ok_y = ymax <= y_max + tol
            else:
                right_ok_y = ymax < y_max - tol

        # 同时满足 x 和 y 条件
        if left_ok_x and right_ok_x and left_ok_y and right_ok_y:
            result.append(geo)

    return result


def compare_lists(old_list, new_list):
    """
    对比两个列表中的元素，返回减少的元素和增加的元素。
    假设列表中的元素是唯一的（如 ID）。
    """
    old_set = set(old_list)
    new_set = set(new_list)

    removed = old_set - new_set  # 旧有而新无
    added = new_set - old_set  # 新有而旧无

    return sorted(removed), sorted(added)


def find_common_vertices(geo_list, mode='all', tol=1e-6):
    """
    查找几何列表中的共同顶点。

    参数:
        geo_list: 几何对象列表（应有 getVertices() 方法）
        mode:     'all'  → 返回所有几何都共有的顶点（交集）
                  'shared' → 返回被两个及以上几何共享的顶点（及对应的几何列表）
        tol:      浮点容差，用于坐标比较

    返回:
        mode='all' : list of tuple (x, y) 共有的顶点坐标（可能为空）
        mode='shared': dict { (x,y): [geo1, geo2, ...] } 仅包含共享次数≥2的项
    """
    # 第一步：收集所有几何的顶点坐标集合（已去重）
    geo_vertex_sets = []  # 每个几何的顶点坐标集合（元组列表）
    for geo in geo_list:
        verts = geo.getVertices()
        # 将坐标转为元组，并按容差分组去重（同一几何内可能重复，但通常不会）
        coords_set = []
        for v in verts:
            # 粗略去重：如果该坐标已存在于该几何的集合中则跳过
            # 更严谨可遍历比较容差
            coord = (v.coords[0], v.coords[1])  # 假设2D
            # 检查是否已存在（容差内）
            exists = False
            for c in coords_set:
                if abs(c[0] - coord[0]) <= tol and abs(c[1] - coord[1]) <= tol:
                    exists = True
                    break
            if not exists:
                coords_set.append(coord)
        geo_vertex_sets.append(set(coords_set))  # 转为集合以便求交

    if mode == 'all':
        # 求所有集合的交集
        common = set.intersection(*geo_vertex_sets) if geo_vertex_sets else set()
        return list(common)

    elif mode == 'shared':
        # 统计每个顶点出现在哪些几何中
        vertex_geo_map = {}  # coord_tuple -> list of geo indices or geo objects
        for idx, geo in enumerate(geo_list):
            verts = geo.getVertices()
            for v in verts:
                coord = (v.coords[0], v.coords[1])
                # 使用容差查找已有的键（因为浮点数可能微小差异）
                found_key = None
                for key in vertex_geo_map.keys():
                    if abs(key[0] - coord[0]) <= tol and abs(key[1] - coord[1]) <= tol:
                        found_key = key
                        break
                if found_key is None:
                    vertex_geo_map[coord] = [geo]
                else:
                    # 避免同一个几何在该顶点重复添加（如果getVertices返回重复端点？）
                    if geo not in vertex_geo_map[found_key]:
                        vertex_geo_map[found_key].append(geo)
        # 过滤出共享次数≥2的
        shared = {k: v for k, v in vertex_geo_map.items() if len(v) >= 2}
        return shared


def sketch_break_curve(s, geo1, geo2):
    old_geo_ids = s.geometry.keys()
    s.breakCurve(curve1=geo1, point1=geo1.getVertices()[0].coords, curve2=geo2, point2=geo2.getVertices()[0].coords)
    new_geo_ids = s.geometry.keys()
    removed_geo_id, added_geo_ids = compare_lists(old_geo_ids, new_geo_ids)
    return find_common_vertices([s.geometry[index] for index in added_geo_ids], 'shared')


def create_sketch_test(model):
    # execfile('F:/GitHub/base/base/utils/flow/f2.py', __main__.__dict__)

    s = model.ConstrainedSketch(name='SKETCH-1', sheetSize=200.0)

    geo_list = []

    for i in range(10):
        geo_list.append(s.Line(point1=[i, 5], point2=[i + 1, 5]))

    geo_list.append(s.ArcByCenterEnds(center=(0, 0), point1=(0, 1), point2=(1, 0), direction=COUNTERCLOCKWISE))

    given_x = 1.5
    split_line = s.Line(point1=[given_x, 0], point2=[given_x, 10])
    crossing_geos = find_geos_relative_to_x(geo_list, given_x, mode='intersect')

    if len(crossing_geos) == 1:
        break_curve_dict = sketch_break_curve(s, crossing_geos[0], split_line)
        sketch_break_curve(s, split_line, break_curve_dict.values()[0][0])

    replace_geo_list = find_geos_in_xy_interval(s.geometry.values(), x_min=given_x, x_max=None, include_min_x=True, include_max_x=True)
    remove_geo_list = [geo for geo in s.geometry.values() if geo not in replace_geo_list]
    s.delete(objectList=remove_geo_list)

    geo_list = s.geometry.values()
    given_x = 5.0
    split_line = s.Line(point1=[given_x, 0], point2=[given_x, 10])
    crossing_geos = find_geos_relative_to_x(geo_list, given_x, mode='intersect')

    if len(crossing_geos) == 1:
        break_curve_dict = sketch_break_curve(s, crossing_geos[0], split_line)
        sketch_break_curve(s, split_line, break_curve_dict.values()[0][0])

    replace_geo_list = find_geos_in_xy_interval(s.geometry.values(), x_min=None, x_max=given_x, include_min_x=True, include_max_x=True)
    remove_geo_list = [geo for geo in s.geometry.values() if geo not in replace_geo_list]
    s.delete(objectList=remove_geo_list)

    s.setPrimaryObject(option=STANDALONE)

    return s


if __name__ == "__main__":
    is_create_p_shell = False
    is_create_p_skirt_front = False
    is_create_p_skirt_behind = False
    is_create_p_flange_front = False
    is_create_p_flange_behind = False
    is_create_p_insulation = False
    is_create_p_cover_front = False
    is_create_p_cover_behind = False
    is_create_p_block = False
    is_create_p_block_penult = False
    is_create_p_block_front = False
    is_create_p_block_behind = False
    is_create_p_block_behind_ab = False
    is_create_p_gap = False
    is_create_p_gap_penult = False
    is_create_p_gap_front = False
    is_create_p_gap_behind = False
    is_save_parts_cae = False
    is_open_parts_cae = False
    is_assemble = False

    is_create_p_shell = True
    is_create_p_skirt_front = True
    is_create_p_skirt_behind = True
    is_create_p_flange_front = True
    is_create_p_flange_behind = True
    is_create_p_insulation = True
    # is_create_p_cover_front = True
    # is_create_p_cover_behind = True
    # is_create_p_block = True
    # is_create_p_block_penult = True
    # is_create_p_block_front = True
    # is_create_p_block_behind = True
    # is_create_p_block_behind_ab = True
    # is_create_p_gap = True
    # is_create_p_gap_penult = True
    # is_create_p_gap_front = True
    # is_create_p_gap_behind = True
    # is_save_parts_cae = True
    # is_open_parts_cae = True
    # is_assemble = True

    n = 9
    d = 3529.0
    x0 = 500.0
    l_c1_c2 = 17300.0
    ellipse_ratio = 1.69
    a_front = 1772.47
    a_behind = 1772.47
    rotate_angle_deg = 40.0
    block_length = 1508.0
    block_insulation_thickness_z = 3.0
    block_insulation_thickness_t = 3.0
    block_insulation_thickness_r = 3.0
    wall_insulation_thickness = 3.0
    block_gap_z = 8.0
    block_gap_t = 8.0
    slot_deep = 380.0
    slot_ellipse_a = 50.0
    slot_ellipse_b = 25.0
    angle_demolding_1 = 1.5
    burn_offset = 0.0
    outer_partition_offset = 300.0
    element_size = 40
    insert_czm = False
    is_shared_node = True
    size = '1'

    front_offset = 350.0
    front_ref_length = 509.0
    behind_ref_length = 917.08

    r_cut_front = 460.0
    length_front = 1500.0
    p0_x_front = -857.5
    p0_y_front = 794
    theta0_deg_front = 90.0
    p3_x_front = 0.0
    p3_y_front = 1762.5
    theta3_deg_front = 0.0
    r1_front = 829.41
    r2_front = 1515.05
    r3_front = 641.21

    r_cut_behind = 460.0
    length_behind = 1500.0
    p0_x_behind = 683.73
    p0_y_behind = 1109.770
    theta0_deg_behind = -90.0
    p3_x_behind = 0.0
    p3_y_behind = 1762.5
    theta3_deg_behind = 0.0
    r1_behind = 525.61
    r2_behind = 1075.96
    r3_behind = 569.38

    shell_r_in = 1777.5
    shell_r_out = 1811.5
    shell_theta_out_deg_front = 0.49
    shell_theta_out_deg_behind = 0.49
    shell_r_out_at_a_front = 1797
    shell_r_out_at_a_behind = 1797
    shell_theta_in_deg_front = 0.24
    shell_theta_in_deg_behind = 0.24
    shell_r_in_front = 562.5
    shell_r_in_behind = 942.5
    shell_l_c1_out = 1105.75
    shell_l_c2_out = 968.46

    shell_insulation_theta_in_deg_front = 0.16
    shell_insulation_theta_in_deg_behind = 0.16
    shell_insulation_r_in = 1764.5
    shell_insulation_r_out = 1777.5
    shell_insulation_r_in_at_a_front = 1762.5
    shell_insulation_r_in_at_a_behind = 1762.5
    shell_insulation_r_in_front = 425.0
    shell_insulation_r_in_behind = 775.0
    shell_insulation_thickness_at_flange_front = 2.5
    shell_insulation_thickness_at_flange_behind = 2.5

    shell_insulation_gap_front_r = 1356.0
    shell_insulation_gap_front_l1 = 3.0
    shell_insulation_gap_front_l2 = 3.0

    cover_r_out_front = 560.0
    cover_thickness_front = 68.0

    cover_r_out_behind = 940.0
    cover_thickness_behind = 43.0

    flange_r_in_front = 460.0
    flange_r_out_front = 843.5
    flange_thickness_front = 145.0
    flange_slope_deg_front = -84.88
    flange_fillet_radius_front = 10

    flange_r_in_behind = 815.0
    flange_r_out_behind = 1258.72
    flange_thickness_behind = 179.0
    flange_slope_deg_behind = 92.78
    flange_fillet_radius_behind = 10

    skirt_r_out_front = 1835.5
    skirt_r_in_1_front = 1702.5
    skirt_r_in_2_front = 1797.585372
    skirt_l_1_front = 23.0
    skirt_l_2_front = 1650.0
    skirt_offset_front = -450.0

    skirt_r_out_behind = 1835.5
    skirt_r_in_1_behind = 1702.5
    skirt_r_in_2_behind = 1797.585372
    skirt_l_1_behind = 23.0
    skirt_l_2_behind = 1650.0
    skirt_offset_behind = 450.0

    setting_file = 'setting.json'
    # setting_file = 'setting_520.json'
    if os.path.exists(setting_file):
        message = load_json(setting_file)
        n = message['n']
        d = message['d']
        x0 = message['x0']
        l_c1_c2 = message['l_c1_c2']
        ellipse_ratio = message['ellipse_ratio']
        a_front = message['a_front']
        a_behind = message['a_behind']
        rotate_angle_deg = message['rotate_angle_deg']
        block_length = message['block_length']
        block_insulation_thickness_z = message['block_insulation_thickness_z']
        block_insulation_thickness_t = message['block_insulation_thickness_t']
        block_insulation_thickness_r = message['block_insulation_thickness_r']
        wall_insulation_thickness = message['wall_insulation_thickness']
        block_gap_z = message['block_gap_z']
        block_gap_t = message['block_gap_t']
        slot_deep = message['slot_deep']
        slot_ellipse_a = message['slot_ellipse_a']
        slot_ellipse_b = message['slot_ellipse_b']
        angle_demolding_1 = message['angle_demolding_1']
        burn_offset = message['burn_offset']
        outer_partition_offset = message['outer_partition_offset']
        element_size = message['element_size']
        insert_czm = message['insert_czm']
        is_shared_node = message['is_shared_node']
        size = message['size']
        front_offset = message['front_offset']
        front_ref_length = message['front_ref_length']
        behind_ref_length = message['behind_ref_length']
        r_cut_front = message['r_cut_front']
        length_front = message['length_front']
        p0_x_front = message['p0_x_front']
        p0_y_front = message['p0_y_front']
        theta0_deg_front = message['theta0_deg_front']
        p3_x_front = message['p3_x_front']
        p3_y_front = message['p3_y_front']
        theta3_deg_front = message['theta3_deg_front']
        r1_front = message['r1_front']
        r2_front = message['r2_front']
        r3_front = message['r3_front']
        r_cut_behind = message['r_cut_behind']
        length_behind = message['length_behind']
        p0_x_behind = message['p0_x_behind']
        p0_y_behind = message['p0_y_behind']
        theta0_deg_behind = message['theta0_deg_behind']
        p3_x_behind = message['p3_x_behind']
        p3_y_behind = message['p3_y_behind']
        theta3_deg_behind = message['theta3_deg_behind']
        r1_behind = message['r1_behind']
        r2_behind = message['r2_behind']
        r3_behind = message['r3_behind']
        shell_r_in = message['shell_r_in']
        shell_r_out = message['shell_r_out']
        shell_theta_out_deg_front = message['shell_theta_out_deg_front']
        shell_theta_out_deg_behind = message['shell_theta_out_deg_behind']
        shell_r_out_at_a_front = message['shell_r_out_at_a_front']
        shell_r_out_at_a_behind = message['shell_r_out_at_a_behind']
        shell_theta_in_deg_front = message['shell_theta_in_deg_front']
        shell_theta_in_deg_behind = message['shell_theta_in_deg_behind']
        shell_r_in_front = message['shell_r_in_front']
        shell_r_in_behind = message['shell_r_in_behind']
        shell_l_c1_out = message['shell_l_c1_out']
        shell_l_c2_out = message['shell_l_c2_out']
        shell_insulation_theta_in_deg_front = message['shell_insulation_theta_in_deg_front']
        shell_insulation_theta_in_deg_behind = message['shell_insulation_theta_in_deg_behind']
        shell_insulation_r_in = message['shell_insulation_r_in']
        shell_insulation_r_out = message['shell_insulation_r_out']
        shell_insulation_r_in_at_a_front = message['shell_insulation_r_in_at_a_front']
        shell_insulation_r_in_at_a_behind = message['shell_insulation_r_in_at_a_behind']
        shell_insulation_r_in_front = message['shell_insulation_r_in_front']
        shell_insulation_r_in_behind = message['shell_insulation_r_in_behind']
        shell_insulation_thickness_at_flange_front = message['shell_insulation_thickness_at_flange_front']
        shell_insulation_thickness_at_flange_behind = message['shell_insulation_thickness_at_flange_behind']
        cover_r_out_front = message['cover_r_out_front']
        cover_thickness_front = message['cover_thickness_front']
        cover_r_out_behind = message['cover_r_out_behind']
        cover_thickness_behind = message['cover_thickness_behind']
        flange_r_in_front = message['flange_r_in_front']
        flange_r_out_front = message['flange_r_out_front']
        flange_thickness_front = message['flange_thickness_front']
        flange_slope_deg_front = message['flange_slope_deg_front']
        flange_fillet_radius_front = message['flange_fillet_radius_front']
        flange_r_in_behind = message['flange_r_in_behind']
        flange_r_out_behind = message['flange_r_out_behind']
        flange_thickness_behind = message['flange_thickness_behind']
        flange_slope_deg_behind = message['flange_slope_deg_behind']
        flange_fillet_radius_behind = message['flange_fillet_radius_behind']
        skirt_r_out_front = message['skirt_r_out_front']
        skirt_r_in_1_front = message['skirt_r_in_1_front']
        skirt_r_in_2_front = message['skirt_r_in_2_front']
        skirt_l_1_front = message['skirt_l_1_front']
        skirt_l_2_front = message['skirt_l_2_front']
        skirt_offset_front = message['skirt_offset_front']
        skirt_r_out_behind = message['skirt_r_out_behind']
        skirt_r_in_1_behind = message['skirt_r_in_1_behind']
        skirt_r_in_2_behind = message['skirt_r_in_2_behind']
        skirt_l_1_behind = message['skirt_l_1_behind']
        skirt_l_2_behind = message['skirt_l_2_behind']
        skirt_offset_behind = message['skirt_offset_behind']
        shell_points_front = message['shell_points_front']
        shell_points_behind = message['shell_points_behind']

        # is_create_p_shell = message['is_create_p_shell']
        # is_create_p_skirt_front = message['is_create_p_skirt_front']
        # is_create_p_skirt_behind = message['is_create_p_skirt_behind']
        # is_create_p_flange_front = message['is_create_p_flange_front']
        # is_create_p_flange_behind = message['is_create_p_flange_behind']
        # is_create_p_insulation = message['is_create_p_insulation']
        # is_create_p_cover_front = message['is_create_p_cover_front']
        # is_create_p_cover_behind = message['is_create_p_cover_behind']
        # is_create_p_block = message['is_create_p_block']
        # is_create_p_block_penult = message['is_create_p_block_penult']
        # is_create_p_block_front = message['is_create_p_block_front']
        # is_create_p_block_behind = message['is_create_p_block_behind']
        # is_create_p_gap = message['is_create_p_gap']
        # is_create_p_gap_penult = message['is_create_p_gap_penult']
        # is_create_p_gap_front = message['is_create_p_gap_front']
        # is_create_p_gap_behind = message['is_create_p_gap_behind']
        # is_save_parts_cae = message['is_save_parts_cae']
        # is_open_parts_cae = message['is_open_parts_cae']
        # is_assemble = message['is_assemble']

    p0_front = (p0_x_front, p0_y_front)
    p3_front = (p3_x_front, p3_y_front)
    p0_behind = (p0_x_behind, p0_y_behind)
    p3_behind = (p3_x_behind, p3_y_behind)

    # if p3_front[1] > d / 2.0:
    #     raise RuntimeError('The y-coordinate of p3_front exceeds d/2, which will cause geometric construction to fail. Please check the parameter settings!')
    # if p3_behind[1] > d / 2.0:
    #     raise RuntimeError('The y-coordinate of p3_behind exceeds d/2, which will cause geometric construction to fail. Please check the parameter settings!')

    beta = math.pi / n
    shell_insulation_r_out_front = shell_r_in_front
    shell_insulation_r_out_behind = shell_r_in_behind
    cover_offset_front = -shell_l_c1_out
    cover_offset_behind = l_c1_c2 + shell_l_c2_out - cover_thickness_behind
    flange_offset_front = -shell_l_c1_out + cover_thickness_front
    flange_thickness_offset_front = shell_insulation_thickness_at_flange_front
    flange_offset_behind = l_c1_c2 + shell_l_c2_out - cover_thickness_behind
    flange_thickness_offset_behind = shell_insulation_thickness_at_flange_behind

    nl, nt = 12, n
    block = np.zeros((nl, nt), dtype=bool)
    block[:, 0] = True

    if not ABAQUS_ENV:
        # points, lines, faces = geometries(d, x0, beta, [0, 100, 100, 100], [0, 50, 50])
        # plot_geometries(points, lines, faces)
        # points, lines, faces = geometries(d, x0, beta, [0, block_insulation_thickness_r], [0, block_gap_z / 2.0, block_insulation_thickness_t])
        # plot_geometries(points, lines, faces)

        # r_cut_front = 460.0
        # length_front = 1500.0
        # p0_front = (-1207.5, 794)
        # theta0_deg_front = 90.0
        # p3_front = (-350, 1762.5)
        # theta3_deg_front = 0.0
        # r1_front = 929.4
        # r2_front = 1524.0
        # r3_front = 655.2
        # shell_insulation_theta_in_deg_front = 0.16

        # p0_behind = (71.54, 147.58)
        # theta0_deg_behind = -90.0
        # p3_behind = (0, 239.5)
        # theta3_deg_behind = 0.0
        # r1_behind = 60.0
        # r2_behind = 260.0
        # r3_behind = 68.0

        # for r1_behind in range(0, 100, 10):
        #     for r2_behind in range(0, 300, 10):
        #         for r3_behind in range(0, 100, 10):
        #             result = solve_three_arcs(p0_behind, theta0_deg_behind, p3_behind, theta3_deg_behind, r1_behind, r2_behind, r3_behind)
        #             if result is not None:
        #                 print(r1_behind, r2_behind, r3_behind)
        #                 plot_three_arcs(result, p0_behind, p3_behind, is_show=True, save_path='three_arcs_behind.png', objective_points=[[0.0, 237.5], [35.1081097913, 228.7594746125], [67.625019058233, 182.508006856104], [71.537317044939, 147.5867657151]])

        # result = solve_three_arcs(p0_behind, theta0_deg_behind, p3_behind, theta3_deg_behind, r1_behind, r2_behind, r3_behind)
        # plot_three_arcs(result, p0_behind, p3_behind, is_show=True, save_path='three_arcs_behind.png', objective_points=[[0.0, 237.5], [35.1081097913, 228.7594746125], [67.625019058233, 182.508006856104], [71.537317044939, 147.5867657151]])

        result = solve_three_arcs(p0_front, theta0_deg_front, p3_front, theta3_deg_front, r1_front, r2_front, r3_front)
        plot_three_arcs(result, p0_front, p3_front, is_show=False, save_path='three_arcs_front.png')

        result = solve_three_arcs(p0_behind, theta0_deg_behind, p3_behind, theta3_deg_behind, r1_behind, r2_behind, r3_behind)
        plot_three_arcs(result, p0_behind, p3_behind, is_show=False, save_path='three_arcs_behind.png')

        plot_blocks_map(block, is_show=False, save_path='blocks_map.png')
    if ABAQUS_ENV:
        # 初始化part对象
        p_insulation = None
        p_cover_front = None
        p_flange_front = None
        p_skirt_front = None
        p_cover_behind = None
        p_flange_behind = None
        p_skirt_behind = None
        p_shell = None
        p_block_front = None
        p_block_penult = None
        p_block_behind = None
        p_block = None
        p_gap_front = None
        p_gap_penult = None
        p_gap_behind = None
        p_gap = None

        Mdb()
        model = mdb.models['Model-1']
        model.setValues(absoluteZero=-273.15)
        # model.setValues(globalJob='/home/dell/www/base/files/abaqus/70/5/Job-1.odb')

        s = create_sketch_test(model)

        exit()

        set_material(model.Material(name='MATERIAL-GRAIN'), load_json('material_grain_prony.json'))
        set_material(model.Material(name='MATERIAL-INSULATION'), load_json('material_insulation.json'))
        set_material(model.Material(name='MATERIAL-GLUE'), load_json('material_glue_prony.json'))
        set_material(model.Material(name='MATERIAL-SHELL'), load_json('material_shell.json'))
        set_material(model.Material(name='MATERIAL-STEEL'), load_json('material_steel.json'))
        set_material(model.Material(name='MATERIAL-CZM'), load_json('material_czm.json'))
        set_material(model.Material(name='MATERIAL-GLUE-WALL'), load_json('material_glue_wall.json'))
        set_material(model.Material(name='MATERIAL-SHELL-COMPOSITE'), load_json('material_shell_composite.json'))
        set_material(model.Material(name='MATERIAL-SKIRT-COMPOSITE'), load_json('material_skirt_composite.json'))

        model.HomogeneousSolidSection(name='SECTION-GRAIN', material='MATERIAL-GRAIN', thickness=None)
        model.HomogeneousSolidSection(name='SECTION-INSULATION', material='MATERIAL-INSULATION', thickness=None)
        model.HomogeneousSolidSection(name='SECTION-GLUE', material='MATERIAL-GLUE', thickness=None)
        model.HomogeneousSolidSection(name='SECTION-SHELL', material='MATERIAL-SHELL', thickness=None)
        model.HomogeneousSolidSection(name='SECTION-STEEL', material='MATERIAL-STEEL', thickness=None)
        model.HomogeneousSolidSection(name='SECTION-GLUE-WALL', material='MATERIAL-GLUE-WALL', thickness=None)
        model.CohesiveSection(name='SECTION-CZM', material='MATERIAL-CZM', response=TRACTION_SEPARATION, outOfPlaneThickness=None)

        model.ContactProperty('IntProp-1')
        model.interactionProperties['IntProp-1'].TangentialBehavior(formulation=FRICTIONLESS)
        model.interactionProperties['IntProp-1'].CohesiveBehavior(defaultPenalties=OFF, table=((1000000.0, 1000000.0, 1000000.0),))
        model.interactionProperties['IntProp-1'].NormalBehavior(pressureOverclosure=HARD, allowSeparation=OFF, constraintEnforcementMethod=DEFAULT)

        shell_dimension = {
            'l_c1_c2': l_c1_c2,
            'ellipse_ratio': ellipse_ratio,
            'shell_r_in': shell_r_in,
            'shell_r_out': shell_r_out,
            'a_front': a_front,
            'a_behind': a_behind,
            'shell_theta_in_deg_front': shell_theta_in_deg_front,
            'shell_theta_in_deg_behind': shell_theta_in_deg_behind,
            'shell_theta_out_deg_front': shell_theta_out_deg_front,
            'shell_theta_out_deg_behind': shell_theta_out_deg_behind,
            'shell_r_out_at_a_front': shell_r_out_at_a_front,
            'shell_r_out_at_a_behind': shell_r_out_at_a_behind,
            'shell_r_in_front': shell_r_in_front,
            'shell_r_in_behind': shell_r_in_behind,
            'shell_l_c1_out': shell_l_c1_out,
            'shell_l_c2_out': shell_l_c2_out,
            'shell_points_front': shell_points_front,
            'shell_points_behind': shell_points_behind,
            'rotate_angle_deg': rotate_angle_deg,
        }
        if is_create_p_shell:
            p_shell = create_part_shell(model, 'PART-SHELL', shell_dimension)
            print('CREATE PART-SHELL DONE.')

        front_skirt_dimension = {
            'skirt_r_out_front': skirt_r_out_front,
            'skirt_r_in_1_front': skirt_r_in_1_front,
            'skirt_r_in_2_front': skirt_r_in_2_front,
            'skirt_l_1_front': skirt_l_1_front,
            'skirt_l_2_front': skirt_l_2_front,
            'skirt_offset_front': skirt_offset_front,
            'rotate_angle_deg': rotate_angle_deg,
        }
        if is_create_p_skirt_front:
            p_skirt_front = create_part_skirt_front(model, 'PART-SKIRT-FRONT', front_skirt_dimension)
            print('CREATE PART-SKIRT-FRONT DONE.')

        behind_skirt_dimension = {
            'l_c1_c2': l_c1_c2,
            'skirt_r_out_behind': skirt_r_out_behind,
            'skirt_r_in_1_behind': skirt_r_in_1_behind,
            'skirt_r_in_2_behind': skirt_r_in_2_behind,
            'skirt_l_1_behind': skirt_l_1_behind,
            'skirt_l_2_behind': skirt_l_2_behind,
            'skirt_offset_behind': skirt_offset_behind,
            'rotate_angle_deg': rotate_angle_deg,
        }
        if is_create_p_skirt_behind:
            p_skirt_behind = create_part_skirt_behind(model, 'PART-SKIRT-BEHIND', behind_skirt_dimension)
            print('CREATE PART-SKIRT-BEHIND DONE.')

        front_flange_dimension = {
            'ellipse_ratio': ellipse_ratio,
            'a_front': a_front,
            'flange_r_in_front': flange_r_in_front,
            'flange_r_out_front': flange_r_out_front,
            'cover_r_out_front': cover_r_out_front,
            'flange_offset_front': flange_offset_front,
            'flange_thickness_front': flange_thickness_front,
            'flange_slope_deg_front': flange_slope_deg_front,
            'flange_thickness_offset_front': flange_thickness_offset_front,
            'flange_fillet_radius_front': flange_fillet_radius_front,
            'rotate_angle_deg': rotate_angle_deg,
        }
        if is_create_p_flange_front:
            p_flange_front = create_part_flange_front(model, 'PART-FLANGE-FRONT', front_flange_dimension)
            print('CREATE PART-FLANGE-FRONT DONE.')

        behind_flange_dimension = {
            'l_c1_c2': l_c1_c2,
            'ellipse_ratio': ellipse_ratio,
            'a_behind': a_behind,
            'flange_r_in_behind': flange_r_in_behind,
            'flange_r_out_behind': flange_r_out_behind,
            'cover_r_out_behind': cover_r_out_behind,
            'flange_offset_behind': flange_offset_behind,
            'flange_thickness_behind': flange_thickness_behind,
            'flange_slope_deg_behind': flange_slope_deg_behind,
            'flange_thickness_offset_behind': flange_thickness_offset_behind,
            'flange_fillet_radius_behind': flange_fillet_radius_behind,
            'rotate_angle_deg': rotate_angle_deg,
        }
        if is_create_p_flange_behind:
            p_flange_behind = create_part_flange_behind(model, 'PART-FLANGE-BEHIND', behind_flange_dimension)
            print('CREATE PART-FLANGE-BEHIND DONE.')

        front_cover_dimension = {
            'cover_r_out_front': cover_r_out_front,
            'cover_thickness_front': cover_thickness_front,
            'cover_offset_front': cover_offset_front,
            'rotate_angle_deg': rotate_angle_deg
        }
        if is_create_p_cover_front:
            p_cover_front = create_part_cover_front(model, 'PART-COVER-FRONT', front_cover_dimension)
            print('CREATE PART-COVER-FRONT DONE.')

        behind_cover_dimension = {
            'cover_r_out_behind': cover_r_out_behind,
            'cover_thickness_behind': cover_thickness_behind,
            'cover_offset_behind': cover_offset_behind,
            'rotate_angle_deg': rotate_angle_deg
        }
        if is_create_p_cover_behind:
            p_cover_behind = create_part_cover_behind(model, 'PART-COVER-BEHIND', behind_cover_dimension)
            print('CREATE PART-COVER-BEHIND DONE.')

        insulation_dimension = {
            'l_c1_c2': l_c1_c2,
            'ellipse_ratio': ellipse_ratio,

            'a_front': a_front,
            'a_behind': a_behind,

            'shell_insulation_r_in': shell_insulation_r_in,
            'shell_insulation_r_out': shell_insulation_r_out,

            'shell_insulation_theta_in_deg_front': shell_insulation_theta_in_deg_front,
            'shell_insulation_theta_in_deg_behind': shell_insulation_theta_in_deg_behind,

            'shell_theta_in_deg_front': shell_theta_in_deg_front,
            'shell_theta_in_deg_behind': shell_theta_in_deg_behind,

            'shell_insulation_r_in_at_a_front': shell_insulation_r_in_at_a_front,
            'shell_insulation_r_in_at_a_behind': shell_insulation_r_in_at_a_behind,

            'shell_insulation_r_out_front': shell_insulation_r_out_front,
            'shell_insulation_r_out_behind': shell_insulation_r_out_behind,

            'shell_insulation_r_in_front': shell_insulation_r_in_front,
            'shell_insulation_r_in_behind': shell_insulation_r_in_behind,

            'shell_insulation_thickness_at_flange_front': shell_insulation_thickness_at_flange_front,
            'shell_insulation_thickness_at_flange_behind': shell_insulation_thickness_at_flange_behind,

            'shell_l_c1_out': shell_l_c1_out,
            'shell_l_c2_out': shell_l_c2_out,
            'flange_r_out_front': flange_r_out_front,
            'flange_r_out_behind': flange_r_out_behind,
            'flange_r_in_front': flange_r_in_front,
            'flange_r_in_behind': flange_r_in_behind,
            'shell_r_in_front': shell_r_in_front,
            'shell_r_in_behind': shell_r_in_behind,

            'p0_front': p0_front,
            'theta0_deg_front': theta0_deg_front,
            'p3_front': p3_front,
            'theta3_deg_front': theta3_deg_front,
            'r1_front': r1_front,
            'r2_front': r2_front,
            'r3_front': r3_front,

            'p0_behind': (p0_behind[0] + l_c1_c2, p0_behind[1]),
            'theta0_deg_behind': theta0_deg_behind,
            'p3_behind': (p3_behind[0] + l_c1_c2, p3_behind[1]),
            'theta3_deg_behind': theta3_deg_behind,
            'r1_behind': r1_behind,
            'r2_behind': r2_behind,
            'r3_behind': r3_behind,

            'shell_insulation_gap_front_r': shell_insulation_gap_front_r,
            'shell_insulation_gap_front_l1': shell_insulation_gap_front_l1,
            'shell_insulation_gap_front_l2': shell_insulation_gap_front_l2,

            'rotate_angle_deg': rotate_angle_deg,
        }
        if is_create_p_insulation:
            p_insulation = create_part_insulation(model, 'PART-INSULATION', insulation_dimension)
            print('CREATE PART-INSULATION DONE.')

        z_list_with_gap = [0, block_length / 2 - block_insulation_thickness_z, block_length / 2, block_length / 2 + block_gap_z / 2]
        index_t_with_gap = 3
        if is_shared_node:
            z_list = z_list_with_gap
            index_t = index_t_with_gap
        else:
            z_list = z_list_with_gap[:-1]
            index_t = index_t_with_gap - 1

        block_dimension = {
            'n': n,
            'z_list': z_list,
            'slot_deep': slot_deep,
            'x0': x0,
            'angle_demolding_1': angle_demolding_1,
            'slot_ellipse_a': slot_ellipse_a,
            'slot_ellipse_b': slot_ellipse_b,
            'size': size,
            'index_r': 2 + 1,
            'index_t': index_t,
            'element_size': element_size,
            'insert_czm': insert_czm,
            'beta': beta,
            'burn_offset': burn_offset
        }

        points, lines, faces = geometries(d, x0, beta, [0, wall_insulation_thickness, block_insulation_thickness_r], [0, block_gap_z / 2.0, block_insulation_thickness_t])
        if is_create_p_block:
            p_block = create_part_block(model, 'PART-BLOCK', points, lines, faces, block_dimension)
            print('CREATE PART-BLOCK DONE.')

        gap_dimension = deepcopy(block_dimension)
        gap_dimension['z_list'] = z_list_with_gap
        gap_dimension['index_r'] = 2
        gap_dimension['index_t'] = index_t_with_gap
        if is_create_p_gap:
            p_gap = create_part_gap(model, 'PART-GAP', points, lines, faces, gap_dimension)
            print('CREATE PART-GAP DONE.')

        penult_block_dimension = deepcopy(block_dimension)
        if is_create_p_block_penult:
            p_block_penult = create_part_block_penult(model, 'PART-BLOCK-PENULT', points, lines, faces, penult_block_dimension)
            print('CREATE PART-BLOCK-PENULT DONE.')

        penult_gap_dimension = deepcopy(gap_dimension)
        if is_create_p_gap_penult:
            p_gap_penult = create_part_gap_penult(model, 'PART-GAP-PENULT', points, lines, faces, penult_gap_dimension)
            print('CREATE PART-GAP-PENULT DONE.')

        points, lines, faces = geometries(d, x0, beta, [0, wall_insulation_thickness, block_insulation_thickness_r, outer_partition_offset], [0, block_gap_z / 2.0, block_insulation_thickness_t])

        z_list_with_gap = [0, front_ref_length, front_ref_length + block_insulation_thickness_z, front_ref_length + block_insulation_thickness_z + block_gap_z / 2]
        index_t_with_gap = 3
        if is_shared_node:
            z_list = z_list_with_gap
            index_t = index_t_with_gap
        else:
            z_list = z_list_with_gap[:-1]
            index_t = index_t_with_gap - 1

        first_block_dimension = deepcopy(block_dimension)
        first_block_dimension['z_list'] = z_list
        first_block_dimension['index_r'] = 3 + 1
        first_block_dimension['index_t'] = index_t

        first_block_dimension['r_cut'] = r_cut_front
        first_block_dimension['length_front'] = length_front
        first_block_dimension['p0'] = [p0_front[0] - front_offset, p0_front[1]]
        first_block_dimension['theta0_deg'] = theta0_deg_front
        first_block_dimension['p3'] = [p3_front[0] - front_offset, p3_front[1]]
        first_block_dimension['theta3_deg'] = theta3_deg_front
        first_block_dimension['r1'] = r1_front
        first_block_dimension['r2'] = r2_front
        first_block_dimension['r3'] = r3_front
        first_block_dimension['theta_in_deg'] = shell_insulation_theta_in_deg_front
        if is_create_p_block_front:
            p_block_front = create_part_block_front(model, 'PART-BLOCK-FRONT', points, lines, faces, first_block_dimension)
            print('CREATE PART-BLOCK-FRONT DONE.')

        first_gap_dimension = deepcopy(first_block_dimension)
        first_gap_dimension['z_list'] = z_list_with_gap
        if is_create_p_gap_front:
            p_gap_front = create_part_gap_front(model, 'PART-GAP-FRONT', points, lines, faces, first_gap_dimension)
            print('CREATE PART-GAP-FRONT DONE.')

        z_list_with_gap = [0, behind_ref_length, behind_ref_length + block_insulation_thickness_z, behind_ref_length + block_insulation_thickness_z + block_gap_z / 2]
        index_t_with_gap = 3
        if is_shared_node:
            z_list = z_list_with_gap
        else:
            z_list = z_list_with_gap[:-1]

        behind_block_dimension = deepcopy(first_block_dimension)
        behind_block_dimension['z_list'] = z_list
        behind_block_dimension['r_cut'] = r_cut_behind
        behind_block_dimension['length_behind'] = length_behind
        behind_block_dimension['p0'] = [p0_behind[0] + front_offset, p0_behind[1]]
        behind_block_dimension['theta0_deg'] = theta0_deg_behind
        behind_block_dimension['p3'] = [p3_behind[0] + front_offset, p3_behind[1]]
        behind_block_dimension['theta3_deg'] = theta3_deg_behind
        behind_block_dimension['r1'] = r1_behind
        behind_block_dimension['r2'] = r2_behind
        behind_block_dimension['r3'] = r3_behind
        behind_block_dimension['theta_in_deg'] = shell_insulation_theta_in_deg_behind
        if is_create_p_block_behind:
            p_block_behind = create_part_block_behind(model, 'PART-BLOCK-BEHIND', points, lines, faces, behind_block_dimension)
            print('CREATE PART-BLOCK-BEHIND DONE.')

        behind_gap_dimension = deepcopy(behind_block_dimension)
        behind_gap_dimension['z_list'] = z_list_with_gap
        if is_create_p_gap_behind:
            p_gap_behind = create_part_gap_behind(model, 'PART-GAP-BEHIND', points, lines, faces, behind_gap_dimension)
            print('CREATE PART-GAP-BEHIND DONE.')

        if is_create_p_block_behind_ab:
            r_out = 140.0

            central_angle_a = math.pi / 6
            intercept_a = -67.55
            behind_block_a_dimension = deepcopy(behind_block_dimension)
            behind_block_a_dimension['central_angle'] = central_angle_a
            behind_block_a_dimension['index_r'] = 3 + 1
            points, lines, faces = geometries_circle(d, r_out, central_angle_a, intercept_a, [0, wall_insulation_thickness, block_insulation_thickness_r, outer_partition_offset], [0, block_gap_z / 2.0, block_insulation_thickness_t])
            p_block_behind_1a = create_part_block_behind_1(model, 'PART-BLOCK-BEHIND-1A', points, lines, faces, behind_block_a_dimension)
            print('CREATE PART-BLOCK-BEHIND-1A DONE.')

            behind_block_a_dimension['index_r'] = 2 + 1
            points, lines, faces = geometries_circle(d, r_out, central_angle_a, intercept_a, [0, wall_insulation_thickness, block_insulation_thickness_r], [0, block_gap_z / 2.0, block_insulation_thickness_t])
            p_block_behind_2a = create_part_block_behind_2(model, 'PART-BLOCK-BEHIND-2A', points, lines, faces, behind_block_a_dimension)
            print('CREATE PART-BLOCK-BEHIND-2A DONE.')

            central_angle_b = 0.0
            intercept_b = 58.5
            behind_block_b_dimension = deepcopy(behind_block_dimension)
            behind_block_b_dimension['central_angle'] = central_angle_b
            behind_block_b_dimension['index_r'] = 3 + 1
            points, lines, faces = geometries_circle(d, r_out, central_angle_b, intercept_b, [0, wall_insulation_thickness, block_insulation_thickness_r, outer_partition_offset], [0, block_gap_z / 2.0, block_insulation_thickness_t])
            p_block_behind_1b = create_part_block_behind_1(model, 'PART-BLOCK-BEHIND-1B', points, lines, faces, behind_block_b_dimension)
            print('CREATE PART-BLOCK-BEHIND-1B DONE.')

            behind_block_b_dimension['index_r'] = 2 + 1
            points, lines, faces = geometries_circle(d, r_out, central_angle_b, intercept_b, [0, wall_insulation_thickness, block_insulation_thickness_r], [0, block_gap_z / 2.0, block_insulation_thickness_t])
            p_block_behind_2b = create_part_block_behind_2(model, 'PART-BLOCK-BEHIND-2B', points, lines, faces, behind_block_b_dimension)
            print('CREATE PART-BLOCK-BEHIND-2B DONE.')

        if is_save_parts_cae:
            mdb.saveAs(pathName='f2-parts.cae')

        if is_open_parts_cae:
            Mdb()
            openMdb(pathName='f2-parts.cae')
            model = mdb.models['Model-1']
            p_block_front = model.parts['PART-BLOCK-FRONT']
            p_block_penult = model.parts['PART-BLOCK-PENULT']
            p_block_behind = model.parts['PART-BLOCK-BEHIND']
            p_block = model.parts['PART-BLOCK']
            p_gap_front = model.parts['PART-GAP-FRONT']
            p_gap_penult = model.parts['PART-GAP-PENULT']
            p_gap_behind = model.parts['PART-GAP-BEHIND']
            p_gap = model.parts['PART-GAP']
            p_insulation = model.parts['PART-INSULATION']
            p_cover_front = model.parts['PART-COVER-FRONT']
            p_flange_front = model.parts['PART-FLANGE-FRONT']
            p_skirt_front = model.parts['PART-SKIRT-FRONT']
            p_cover_behind = model.parts['PART-COVER-BEHIND']
            p_flange_behind = model.parts['PART-FLANGE-BEHIND']
            p_skirt_behind = model.parts['PART-SKIRT-BEHIND']
            p_shell = model.parts['PART-SHELL']
            for p in model.parts.values():
                p.setValues(geometryRefinement=EXTRA_FINE)

        if is_assemble:
            block_types = get_block_types(block)
            ties_types = get_tie_types(block)

            # 药块字典
            block_part_dict = {
                'FRONT': p_block_front,
                'PENULT': p_block_penult,
                'BEHIND': p_block_behind,
                'MIDDLE': p_block
            }

            # 缝隙字典
            gap_part_dict = {
                'FRONT': p_gap_front,
                'PENULT': p_gap_penult,
                'BEHIND': p_gap_behind,
                'MIDDLE': p_gap
            }

            # 旋转体字典
            rotation_part_dict = {
                'INSULATION': p_insulation,
                'COVER-FRONT': p_cover_front,
                'FLANGE-FRONT': p_flange_front,
                'SKIRT-FRONT': p_skirt_front,
                'COVER-BEHIND': p_cover_behind,
                'FLANGE-BEHIND': p_flange_behind,
                'SKIRT-BEHIND': p_skirt_behind,
                'SHELL': p_shell,
            }

            a = model.rootAssembly
            a.DatumCsysByDefault(CARTESIAN)
            cylindrical_datum = a.DatumCsysByThreePoints(name='Datum csys-2', coordSysType=CYLINDRICAL, origin=(0.0, 0.0, 0.0), point1=(1.0, 0.0, 0.0), point2=(0.0, 1.0, 0.0))

            # 公共旋转参数
            origin = (0.0, 0.0, 0.0)
            axis_y = (0.0, 1.0, 0.0)
            axis_z = (0.0, 0.0, 1.0)
            y_rot_angle = -90.0

            # 根据 size 计算Z轴旋转角度
            if size == '1/2':
                z_rot_angle = -90.0
            elif size == '1':
                z_rot_angle = -90.0 - 360.0 / n / 2.0
            else:
                z_rot_angle = 0.0

            for name, part in rotation_part_dict.items():
                if part is not None:
                    a.Instance(name=name, part=part, dependent=ON)
                    a.rotate(instanceList=(name,), axisPoint=origin, axisDirection=axis_y, angle=y_rot_angle)
                    a.rotate(instanceList=(name,), axisPoint=origin, axisDirection=axis_z, angle=z_rot_angle)

            for block_loc, block_type in block_types.items():
                l, i = block_loc

                z_shift = front_offset

                if block_type == 'FRONT':
                    z_shift = front_offset
                elif block_type == 'MIDDLE':
                    z_shift = front_offset + front_ref_length + block_insulation_thickness_z + block_gap_z / 2 + (l - 1 + 0.5) * (block_gap_z + block_length)
                elif block_type == 'PENULT':
                    z_shift = front_offset + front_ref_length + block_insulation_thickness_z + block_gap_z / 2 + (l - 1 + 0.5) * (block_gap_z + block_length)
                elif block_type == 'BEHIND':
                    z_shift = front_offset + front_ref_length + block_insulation_thickness_z + block_gap_z / 2 + (l - 1) * (block_gap_z + block_length) + block_gap_z / 2 + block_insulation_thickness_z + behind_ref_length

                instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
                if block_part_dict[block_type] is not None:
                    a.Instance(name=instance_name, part=block_part_dict[block_type], dependent=ON)
                    a.translate(instanceList=(instance_name,), vector=(0.0, 0.0, z_shift))
                    a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)

                if not is_shared_node:
                    if gap_part_dict[block_type] is not None:
                        instance_name = 'GAP-%s-%s' % (l + 1, i + 1)
                        a.Instance(name=instance_name, part=gap_part_dict[block_type], dependent=ON)
                        a.translate(instanceList=(instance_name,), vector=(0.0, 0.0, z_shift))
                        a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)

            model.StaticStep(name='Step-1', previous='Initial', nlgeom=OFF, timePeriod=1.0, maxNumInc=10000, initialInc=1.0, minInc=1e-06, maxInc=1.0)
            # model.FrequencyStep(name='Step-1', previous='Initial', numEigen=10)

            model.TabularAmplitude(name='AMP-PRESSURE', timeSpan=STEP, smooth=SOLVER_DEFAULT, data=((0.0, 0.0), (1.0, 1.0)))
            model.ExpressionField(name='ANALYTICALFIELD-PRESSURE', localCsys=a.datums[cylindrical_datum.id], description='', expression='8.6-1.5*(Z+1037.75)/19263.21')
            model.ExpressionField(name='ANALYTICALFIELD-PRESSURE', localCsys=a.datums[cylindrical_datum.id], description='', expression='8.02-0.07*(Z+1037.75)/19263.21')

            # 1. 定义坐标范围
            x = np.arange(-2000, 2000, 20)
            y = np.arange(-2000, 2000, 20)
            z = np.linspace(0, 200000, 2)
            # 2. 生成完整三维网格坐标
            X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
            # 3. 计算 value（只依赖于 x, y 是否在圆内）
            value = (X ** 2 + Y ** 2 <= 900 ** 2).astype(int)
            # 4. 将四维数据展平为表格式（每行一个点）
            xyz_data = np.column_stack((X.ravel(), Y.ravel(), Z.ravel(), value.ravel()))
            model.MappedField(name='ANALYTICALFIELD-PRESSURE-INSULATION-FRONT', description='', regionType=POINT, partLevelData=False, localCsys=None, pointDataFormat=XYZ, fieldDataType=SCALAR,
                              xyzPointData=xyz_data)

            # 1. 定义坐标范围
            x = np.arange(-2000, 2000, 20)
            y = np.arange(-2000, 2000, 20)
            z = np.linspace(0, 200000, 2)
            # 2. 生成完整三维网格坐标
            X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
            # 3. 计算 value（只依赖于 x, y 是否在圆内）
            value = (X ** 2 + Y ** 2 <= 1306 ** 2).astype(int)
            # 4. 将四维数据展平为表格式（每行一个点）
            xyz_data = np.column_stack((X.ravel(), Y.ravel(), Z.ravel(), value.ravel()))
            model.MappedField(name='ANALYTICALFIELD-PRESSURE-INSULATION-BEHIND', description='', regionType=POINT, partLevelData=False, localCsys=None, pointDataFormat=XYZ, fieldDataType=SCALAR,
                              xyzPointData=xyz_data)

            # 1. 定义坐标范围
            x = np.arange(-1000, 1000, 10)
            y = np.arange(-1000, 1000, 10)
            z = np.linspace(0, 200000, 2)
            # 2. 生成完整三维网格坐标
            X, Y, Z = np.meshgrid(x, y, z, indexing='ij')
            # 3. 计算 value（只依赖于 x, y 是否在圆内）
            value = (X ** 2 + Y ** 2 <= 425 ** 2).astype(int)
            # 4. 将四维数据展平为表格式（每行一个点）
            xyz_data = np.column_stack((X.ravel(), Y.ravel(), Z.ravel(), value.ravel()))
            model.MappedField(name='ANALYTICALFIELD-PRESSURE-COVER-FRONT', description='', regionType=POINT, partLevelData=False, localCsys=None, pointDataFormat=XYZ, fieldDataType=SCALAR,
                              xyzPointData=xyz_data)

            # 壳体内表面与绝热层外表面绑定
            instance_name_1 = 'SHELL'
            surface_name_1 = 'SURFACE-INNER'
            instance_name_2 = 'INSULATION'
            surface_name_2 = 'SURFACE-OUTER'
            create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

            instance_name_1 = 'INSULATION'
            surface_name_1 = 'SURFACE-FLANGE-FRONT'
            instance_name_2 = 'FLANGE-FRONT'
            surface_name_2 = 'SURFACE-TIE'
            create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

            instance_name_1 = 'INSULATION'
            surface_name_1 = 'SURFACE-FLANGE-BEHIND'
            instance_name_2 = 'FLANGE-BEHIND'
            surface_name_2 = 'SURFACE-TIE'
            create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

            instance_name_1 = 'FLANGE-FRONT'
            surface_name_1 = 'SURFACE-X0'
            instance_name_2 = 'COVER-FRONT'
            surface_name_2 = 'SURFACE-X1'
            create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

            instance_name_1 = 'FLANGE-BEHIND'
            surface_name_1 = 'SURFACE-X1'
            instance_name_2 = 'COVER-BEHIND'
            surface_name_2 = 'SURFACE-X0'
            create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

            instance_name_1 = 'SKIRT-FRONT'
            surface_name_1 = 'SURFACE-INNER'
            instance_name_2 = 'SHELL'
            surface_name_2 = 'SURFACE-OUTER'
            create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

            instance_name_1 = 'SKIRT-BEHIND'
            surface_name_1 = 'SURFACE-INNER'
            instance_name_2 = 'SHELL'
            surface_name_2 = 'SURFACE-OUTER'
            create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

            for instance_name in rotation_part_dict.keys():
                set_name = 'SET-SURFACE-T0'
                bc_name = 'BC-' + instance_name + '-' + set_name
                model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

                set_name = 'SET-SURFACE-T1'
                bc_name = 'BC-' + instance_name + '-' + set_name
                model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

            # instance_name = 'INSULATION'
            # surface_name = 'SURFACE-INNER'
            # load_name = 'LOAD-' + instance_name + '-' + surface_name
            # model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=UNIFORM, field='', magnitude=10.8, amplitude=UNSET)

            instance_name = 'INSULATION'
            surface_name = 'SURFACE-INNER-FRONT'
            load_name = 'LOAD-' + instance_name + '-' + surface_name
            model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=FIELD, field='ANALYTICALFIELD-PRESSURE-INSULATION-FRONT', magnitude=8.02, amplitude='AMP-PRESSURE')

            instance_name = 'INSULATION'
            surface_name = 'SURFACE-RIN-FRONT'
            load_name = 'LOAD-' + instance_name + '-' + surface_name
            model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=FIELD, field='ANALYTICALFIELD-PRESSURE', magnitude=1.0, amplitude='AMP-PRESSURE')

            instance_name = 'INSULATION'
            surface_name = 'SURFACE-GAP-FRONT'
            load_name = 'LOAD-' + instance_name + '-' + surface_name
            model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=FIELD, field='ANALYTICALFIELD-PRESSURE', magnitude=1.0, amplitude='AMP-PRESSURE')

            instance_name = 'INSULATION'
            surface_name = 'SURFACE-INNER-BEHIND'
            load_name = 'LOAD-' + instance_name + '-' + surface_name
            model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=FIELD, field='ANALYTICALFIELD-PRESSURE-INSULATION-BEHIND', magnitude=7.1, amplitude='AMP-PRESSURE')

            instance_name = 'INSULATION'
            surface_name = 'SURFACE-RIN-BEHIND'
            load_name = 'LOAD-' + instance_name + '-' + surface_name
            model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=FIELD, field='ANALYTICALFIELD-PRESSURE', magnitude=1.0, amplitude='AMP-PRESSURE')

            instance_name = 'COVER-FRONT'
            surface_name = 'SURFACE-X1'
            load_name = 'LOAD-' + instance_name + '-' + surface_name
            model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=FIELD, field='ANALYTICALFIELD-PRESSURE-COVER-FRONT', magnitude=7.95, amplitude='AMP-PRESSURE')

            instance_name = 'SKIRT-FRONT'
            set_name = 'SET-SURFACE-X0'
            bc_name = 'BC-' + instance_name + '-' + set_name
            # model.DisplacementBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name],
            #                      u1=UNSET, u2=UNSET, u3=0.0, ur1=UNSET, ur2=UNSET, ur3=UNSET, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', localCsys=a.datums[cylindrical_datum.id])
            model.DisplacementBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name],
                                 u1=0.0, u2=0.0, u3=0.0, ur1=UNSET, ur2=UNSET, ur3=UNSET, amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='', localCsys=a.datums[cylindrical_datum.id])

            for block_loc, block_type in block_types.items():
                l, i = block_loc
                if is_shared_node:
                    instance_name_2 = 'BLOCK-%s-%s' % (l + 1, i + 1)
                    surface_name_2 = 'SURFACE-OUTER'
                    instance_name_1 = 'INSULATION'
                    surface_name_1 = 'SURFACE-INNER'
                    create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)
                else:
                    instance_name_1 = 'BLOCK-%s-%s' % (l + 1, i + 1)
                    surface_name_1 = 'SURFACE-TIE'
                    instance_name_2 = 'GAP-%s-%s' % (l + 1, i + 1)
                    surface_name_2 = 'SURFACE-TIE'
                    create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

                    instance_name_2 = 'BLOCK-%s-%s' % (l + 1, i + 1)
                    surface_name_2 = 'SURFACE-OUTER'
                    instance_name_1 = 'INSULATION'
                    surface_name_1 = 'SURFACE-INNER'
                    create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

                    instance_name_2 = 'GAP-%s-%s' % (l + 1, i + 1)
                    surface_name_2 = 'SURFACE-OUTER'
                    instance_name_1 = 'INSULATION'
                    surface_name_1 = 'SURFACE-INNER'
                    create_contact_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2, 'Step-1', 'IntProp-1')

            for tie_loc, tie_type in ties_types.items():
                l1, i1, l2, i2 = tie_loc
                if is_shared_node:
                    if tie_type == 'down':
                        instance_name_1 = 'BLOCK-%s-%s' % (l1 + 1, i1 + 1)
                        surface_name_1 = 'SURFACE-Z1'
                        instance_name_2 = 'BLOCK-%s-%s' % (l2 + 1, i2 + 1)
                        surface_name_2 = 'SURFACE-Z-1'
                        create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

                    elif tie_type == 'right':
                        instance_name_1 = 'BLOCK-%s-%s' % (l1 + 1, i1 + 1)
                        surface_name_1 = 'SURFACE-T1'
                        instance_name_2 = 'BLOCK-%s-%s' % (l2 + 1, i2 + 1)
                        surface_name_2 = 'SURFACE-T-1'
                        create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)

                    elif tie_type == 'circular':
                        instance_name_1 = 'BLOCK-%s-%s' % (l1 + 1, i1 + 1)
                        surface_name_1 = 'SURFACE-T-1'
                        instance_name_2 = 'BLOCK-%s-%s' % (l2 + 1, i2 + 1)
                        surface_name_2 = 'SURFACE-T1'
                        create_tie_of_instance_surface(model, instance_name_1, instance_name_2, surface_name_1, surface_name_2)
                else:
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
                model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=FIELD, field='ANALYTICALFIELD-PRESSURE', magnitude=1.0, amplitude='AMP-PRESSURE')

                if not is_shared_node:
                    instance_name = 'GAP-%s-%s' % (l + 1, i + 1)
                    surface_name = 'SURFACE-INNER'
                    load_name = 'LOAD-' + instance_name + '-' + surface_name
                    model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[instance_name].surfaces[surface_name], distributionType=FIELD, field='ANALYTICALFIELD-PRESSURE', magnitude=1.0, amplitude='AMP-PRESSURE')

            for block_loc, block_type in block_types.items():
                l, i = block_loc
                if i == 0:
                    instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
                    set_name = 'SET-SURFACE-T-1'
                    bc_name = 'BC-' + instance_name + '-' + set_name
                    model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

                    instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
                    set_name = 'SET-SURFACE-T1'
                    bc_name = 'BC-' + instance_name + '-' + set_name
                    model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

                #     instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
                #     set_name = 'SET-SURFACE-T-1'
                #     bc_name = 'BC-' + instance_name + '-' + set_name
                #     model.SubmodelBC(name=bc_name, createStepName='Step-1',
                #                      region=a.instances[instance_name].sets[set_name], globalStep='1', globalIncrement=0, timeScale=OFF, dof=(1, 2, 3), globalDrivingRegion='', absoluteExteriorTolerance=None,
                #                      exteriorTolerance=0.05, intersectionOnly=OFF)
                #
                #     instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
                #     set_name = 'SET-SURFACE-T1'
                #     bc_name = 'BC-' + instance_name + '-' + set_name
                #     model.SubmodelBC(name=bc_name, createStepName='Step-1',
                #                      region=a.instances[instance_name].sets[set_name], globalStep='1', globalIncrement=0, timeScale=OFF, dof=(1, 2, 3), globalDrivingRegion='', absoluteExteriorTolerance=None,
                #                      exteriorTolerance=0.05, intersectionOnly=OFF)
                #
                #     instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
                #     set_name = 'SET-SURFACE-Z1'
                #     bc_name = 'BC-' + instance_name + '-' + set_name
                #     model.SubmodelBC(name=bc_name, createStepName='Step-1',
                #                      region=a.instances[instance_name].sets[set_name], globalStep='1', globalIncrement=0, timeScale=OFF, dof=(1, 2, 3), globalDrivingRegion='', absoluteExteriorTolerance=None,
                #                      exteriorTolerance=0.05, intersectionOnly=OFF)
                #
                #     instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
                #     set_name = 'SET-SURFACE-Z-1'
                #     bc_name = 'BC-' + instance_name + '-' + set_name
                #     model.SubmodelBC(name=bc_name, createStepName='Step-1',
                #                      region=a.instances[instance_name].sets[set_name], globalStep='1', globalIncrement=0, timeScale=OFF, dof=(1, 2, 3), globalDrivingRegion='', absoluteExteriorTolerance=None,
                #                      exteriorTolerance=0.05, intersectionOnly=OFF)
                #
                #     instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
                #     set_name = 'SET-SURFACE-T0'
                #     bc_name = 'BC-' + instance_name + '-' + set_name
                #     model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])
                #
                # if i == 2:
                #     instance_name = 'BLOCK-%s-%s' % (l + 1, i + 1)
                #     set_name = 'SET-SURFACE-T1'
                #     bc_name = 'BC-' + instance_name + '-' + set_name
                #     model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])
                #
                #     instance_name = 'GAP-%s-%s' % (l + 1, i + 1)
                #     set_name = 'SET-SURFACE-T2'
                #     bc_name = 'BC-' + instance_name + '-' + set_name
                #     model.YsymmBC(name=bc_name, createStepName='Step-1', region=a.instances[instance_name].sets[set_name], localCsys=a.datums[cylindrical_datum.id])

            # model.Gravity(name='Load-1', createStepName='Step-1', comp2=-9800.0, distributionType=UNIFORM, field='')

            if major_version >= 2022:
                mdb.Job(name='Job-1', model='Model-1', description='', type=ANALYSIS,
                        atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
                        memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
                        explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
                        modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
                        scratch='', resultsFormat=ODB, numThreadsPerMpiProcess=1,
                        multiprocessingMode=DEFAULT, numCpus=16, numDomains=16, numGPUs=0)
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

            mdb.saveAs(pathName='f2.cae')
