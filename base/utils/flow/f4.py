# -*- coding: utf-8 -*-
"""

"""
import json
import math

import numpy as np
import regionToolset
from abaqus import mdb
from abaqusConstants import *
from abaqusConstants import (CLOCKWISE, COUNTERCLOCKWISE, THREE_D, MIDDLE_SURFACE, FROM_SECTION, CYLINDRICAL, EXTRA_FINE,
                             DEFORMABLE_BODY, STANDARD, C3D4, XAXIS, YAXIS, ZAXIS, TOP, XYPLANE, YZPLANE, C3D8T, COPLANAR_EDGES,
                             C3D6, C3D8, STEP, ON, OFF, CARTESIAN, SIDE1, RIGHT, FORWARD)
from caeModules import mesh


def load_json(file_path, encoding='utf-8'):
    """
    Read JSON data from file.
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def is_unicode_all_uppercase(obj):
    return isinstance(obj, unicode) and obj.isupper() and any(c.isalpha() for c in obj)


def set_obj(obj, attr, attr_dict):
    args = {}
    for arg_key, arg_value in attr_dict.items():
        if is_unicode_all_uppercase(arg_value):
            args[str(arg_key)] = eval(arg_value)
        else:
            args[str(arg_key)] = arg_value
    method = getattr(obj, attr)
    method(**args)


def set_material(material_obj, material_dict):
    for material_key, material_value in material_dict.items():
        print(material_key)
        if '.' in material_key:
            if hasattr(material_obj, material_key.split('.')[1]):
                material_sub_obj = getattr(material_obj, material_key.split('.')[1])
                for material_sub_key, material_sub_value in material_value.items():
                    if hasattr(material_sub_obj, material_sub_key):
                        set_obj(material_sub_obj, material_sub_key, material_sub_value)
        else:
            if hasattr(material_obj, material_key):
                set_obj(material_obj, material_key, material_value)


def get_z_list(layer_height, layer_insulation_thickness, layer_gap, layer_number):
    z = []
    for i in range(layer_number):
        z += (np.array([0.0, layer_insulation_thickness, layer_height - layer_insulation_thickness, layer_height]) + i * (layer_height + layer_gap)).tolist()
    return z


def polar_to_cartesian(r, theta_rad):
    """
    将极坐标(r, theta)转换为直角坐标(x, y)

    参数:
    r -- 极径(半径)
    theta_rad -- 极角(弧度制)

    返回:
    (x, y) -- 直角坐标的元组
    """
    # 计算x和y坐标
    x = r * math.cos(theta_rad)
    y = r * math.sin(theta_rad)

    return (x, y)


def mirror_y_axis(point):
    """
    计算点关于 y 轴的镜像坐标
    """
    return [-point[0], point[1]]


def line_intersection(p1, p2, p3, p4):
    """
    计算两条直线的交点

    参数:
    p1, p2: 第一条直线上的两个点，格式为(x, y)
    p3, p4: 第二条直线上的两个点，格式为(x, y)

    返回:
    交点坐标(x, y)，如果两直线平行则返回None
    """
    # 计算第一条直线的斜率和截距
    x1, y1 = p1
    x2, y2 = p2

    # 计算第二条直线的斜率和截距
    x3, y3 = p3
    x4, y4 = p4

    # 计算分母 (为了判断是否平行)
    denominator = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)

    # 如果分母为0，说明两直线平行或重合
    if denominator == 0:
        return None  # 无交点或无数交点

    # 计算分子a和b
    a = (x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)
    b = (x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)

    # 计算参数u_a和u_b
    u_a = a / denominator
    u_b = b / denominator

    # 计算交点坐标
    x = x1 + u_a * (x2 - x1)
    y = y1 + u_a * (y2 - y1)

    return x, y


def line_segment_circle_intersection(x1, y1, x2, y2, r):
    """
    计算线段 (x1,y1)-(x2,y2) 与圆心在原点、半径为 r 的圆的交点坐标
    返回交点列表，如果没有交点则返回空列表
    """
    print(x1, y1, x2, y2)
    # 确保 x1 <= x2，方便后续判断
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1

    dx = x2 - x1
    dy = y2 - y1
    intersections = []

    if abs(dx) < 1.0e-6:
        # 垂直线 x = x1
        x = x1
        if abs(x) <= r:
            # 代入圆的方程 x^2 + y^2 = r^2 => y = ±sqrt(r^2 - x^2)
            y_plus = math.sqrt(r ** 2 - x ** 2)
            y_minus = -y_plus
            # 检查 y 是否在 y1 和 y2 之间
            for y in [y_plus, y_minus]:
                if (y >= min(y1, y2) and y <= max(y1, y2)):
                    intersections.append((x, y))
    else:
        # 斜截式：y = m x + c
        m = dy / dx
        c = y1 - m * x1
        # 代入圆的方程：x^2 + (m x + c)^2 = r^2
        A = 1 + m ** 2
        B = 2 * m * c
        C = c ** 2 - r ** 2
        discriminant = B ** 2 - 4 * A * C

        if discriminant >= 0:
            sqrt_discriminant = math.sqrt(discriminant)
            x_plus = (-B + sqrt_discriminant) / (2 * A)
            x_minus = (-B - sqrt_discriminant) / (2 * A)
            # 检查 x 是否在 x1 和 x2 之间
            for x in [x_plus, x_minus]:
                if (x >= x1 and x <= x2):
                    y = m * x + c
                    intersections.append((x, y))

    return intersections


def find_perpendicular_foot(A, B, P):
    """
    计算从点P到直线AB的垂足Q的坐标。

    参数:
    A -- 直线上的第一个点，格式为 (x, y)
    B -- 直线上的第二个点，格式为 (x, y)
    P -- 直线外的点，格式为 (x, y)

    返回:
    Q -- 垂足的坐标，格式为 (x, y)
    """
    # 将点转换为坐标
    x1, y1 = A
    x2, y2 = B
    x_p, y_p = P

    # 计算向量AB和AP
    ab_x = x2 - x1
    ab_y = y2 - y1
    ap_x = x_p - x1
    ap_y = y_p - y1

    # 计算向量AB和AP的点积
    dot_product = ap_x * ab_x + ap_y * ab_y
    # 计算向量AB的模的平方
    ab_squared = ab_x ** 2 + ab_y ** 2

    # 如果AB是一个点（即A和B重合），则无法定义直线，返回None
    if ab_squared == 0:
        return None

    # 计算投影参数t
    t = dot_product / ab_squared

    # 计算垂足Q的坐标
    q_x = x1 + t * ab_x
    q_y = y1 + t * ab_y

    return (q_x, q_y)


def geometries(model, geo_type, d, e, epsilon, beta, zeta, r1, r2, d2, rt1, rt2, rt3, rt4, vt1, vt2):
    number_vertical_line = 2
    number_radius = 8
    number_theta = 4 + number_vertical_line
    radius_list = [0.0 for _ in range(number_radius)]
    theta_list = [0.0 for _ in range(number_theta)]

    radius_list[2] = d / 2.0 - e * 0.9
    radius_list[3] = d / 2.0
    radius_list[4] = d / 2.0 + rt1
    radius_list[5] = d / 2.0 + rt1 + rt2
    radius_list[6] = d / 2.0 + rt1 + rt2 + rt3
    radius_list[7] = d / 2.0 + rt1 + rt2 + rt3 + rt4

    theta_list[0] = math.pi / 2.0 + beta
    theta_list[1] = math.pi / 2.0 + beta / 2.0
    theta_list[2] = math.pi / 2.0 + beta / 5.0
    theta_list[-1] = math.pi / 2.0

    vertical_line_x_list = [-vt1 - vt2, -vt1]

    points = np.zeros([number_radius, number_theta, 2])

    c1 = math.tan((math.pi + zeta) / 2.0 - beta)
    c2 = (r1 - (d / 2.0 - e)) * math.tan((1.0 - epsilon) * beta) - r1
    c3 = (-r2 * c1 + c1 * c2 + (d / 2.0 - e) - r1)
    c4 = c1 - 1.0 / math.tan(beta)

    points[0, 0] = np.array([(c3 / c4) + r2 * math.sin(beta), (-1.0 / math.tan(beta) * (c3 / c4)) - r2 * math.cos(beta)])
    points[0, 1] = np.array([(c3 / c4) + r2, -1.0 / math.tan(beta) * (c3 / c4)])
    points[0, 2] = np.array([(r1 - (d / 2.0 - e)) * math.tan((1.0 - epsilon) * beta), d / 2.0 - e - r1])

    points[1, 0] = np.array([c3 / c4, -1.0 / math.tan(beta) * (c3 / c4)])
    points[1, 1] = np.array([(r1 - (d / 2.0 - e)) * math.tan((1.0 - epsilon) * beta) - r1, d / 2.0 - e - r1])
    points[1, 2] = np.array([(r1 - (d / 2.0 - e)) * math.tan((1.0 - epsilon) * beta), d / 2.0 - e])
    points[1, number_theta - 1] = np.array([0.0, d / 2.0 - e])

    if number_vertical_line > 0:
        for j in range(3, number_theta - number_vertical_line + 1):
            points[1, j] = np.array([vertical_line_x_list[j - 3], d / 2.0 - e])

    for i in range(2, number_radius):
        for j in [0, 1, 2, number_theta - 1]:
            points[i, j] = np.array(polar_to_cartesian(radius_list[i], theta_list[j]))

        if number_vertical_line > 0:
            for j in range(3, number_theta - number_vertical_line + 1):
                points[i, j] = np.array([vertical_line_x_list[j - 3], math.sqrt(radius_list[i] ** 2 - vertical_line_x_list[j - 3] ** 2)])

    s = model.ConstrainedSketch(name='geometries', sheetSize=200.0)

    if geo_type == 'inner_polygon':
        point = line_segment_circle_intersection(points[0, 1][0], points[0, 1][1], points[1, 1][0], points[1, 1][1], d2)
        points[0, 1] = np.array(point)
        point = find_perpendicular_foot(points[0, 0], points[2, 0], points[0, 1])
        points[1, 0] = np.array(point)

    lines = {}
    for i in range(points.shape[0]):
        for j in range(points.shape[1]):
            point1 = points[i, j]
            if i - 1 > 0:
                point2 = points[i - 1, j]
                lines['%s%s-%s%s' % (i, j, i - 1, j)] = [point1, point2, s.Line(point1=point1, point2=point2).pointOn]
            if i + 1 < points.shape[0]:
                point2 = points[i + 1, j]
                lines['%s%s-%s%s' % (i, j, i + 1, j)] = [point1, point2, s.Line(point1=point1, point2=point2).pointOn]
            if j - 1 > 0:
                point2 = points[i, j - 1]
                lines['%s%s-%s%s' % (i, j, i, j - 1)] = [point1, point2,
                                                         s.ArcByCenterEnds(center=(0.0, 0.0), point1=point1, point2=point2, direction=COUNTERCLOCKWISE).pointOn]
            if j + 1 < points.shape[1]:
                point2 = points[i, j + 1]
                lines['%s%s-%s%s' % (i, j, i, j + 1)] = [point1, point2,
                                                         s.ArcByCenterEnds(center=(0.0, 0.0), point1=point1, point2=point2, direction=CLOCKWISE).pointOn]

    point1 = points[1, 0]
    point2 = points[0, 1]
    lines['%s%s-%s%s' % (1, 0, 0, 1)] = [point1, point2, s.Line(point1=point1, point2=point2).pointOn]

    faces = np.zeros([number_radius - 1, number_theta - 1, 2])
    for i in range(faces.shape[0]):
        for j in range(faces.shape[1]):
            point = (np.array(lines['%s%s-%s%s' % (i, j, i, j + 1)][2]) + np.array(lines['%s%s-%s%s' % (i + 1, j, i + 1, j + 1)][2])) / 2.0
            faces[i, j, 0] = point[0]
            faces[i, j, 1] = point[1]

    point = (np.array(lines['%s%s-%s%s' % (0, 0, 0, 1)][2]) + np.array(lines['%s%s-%s%s' % (0, 0, 1, 0)][2])) / 2.0
    faces[0, 0, 0] = point[0]
    faces[0, 0, 1] = point[1]

    return points, lines, faces


def create_sketch_section(model, sketch_name, geo_type, n, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)

    geom_list = []

    if geo_type == 'inner_polygon':
        geom_list.append(s.Line(point1=points[1, -1], point2=points[1, 2]))
        geom_list.append(s.ArcByCenterEnds(center=points[0, 2], point1=points[1, 2], point2=points[1, 1], direction=COUNTERCLOCKWISE))
        geom_list.append(s.Line(point1=points[1, 1], point2=points[0, 1]))
        geom_list.append(s.Line(point1=points[1, 0], point2=points[0, 1]))

        geom_list.append(s.Line(point1=mirror_y_axis(points[1, -1]), point2=mirror_y_axis(points[1, 2])))
        geom_list.append(
            s.ArcByCenterEnds(center=mirror_y_axis(points[0, 2]), point1=mirror_y_axis(points[1, 2]), point2=mirror_y_axis(points[1, 1]), direction=CLOCKWISE))
        geom_list.append(s.Line(point1=mirror_y_axis(points[1, 1]), point2=mirror_y_axis(points[0, 1])))
        geom_list.append(s.Line(point1=mirror_y_axis(points[1, 0]), point2=mirror_y_axis(points[0, 1])))
    else:
        geom_list.append(s.Line(point1=points[1, -1], point2=points[1, 2]))
        geom_list.append(s.ArcByCenterEnds(center=points[0, 2], point1=points[1, 2], point2=points[1, 1], direction=COUNTERCLOCKWISE))
        geom_list.append(s.Line(point1=points[1, 1], point2=points[0, 1]))
        geom_list.append(s.ArcByCenterEnds(center=points[1, 0], point1=points[0, 1], point2=points[0, 0], direction=CLOCKWISE))

        geom_list.append(s.Line(point1=mirror_y_axis(points[1, -1]), point2=mirror_y_axis(points[1, 2])))
        geom_list.append(
            s.ArcByCenterEnds(center=mirror_y_axis(points[0, 2]), point1=mirror_y_axis(points[1, 2]), point2=mirror_y_axis(points[1, 1]), direction=CLOCKWISE))
        geom_list.append(s.Line(point1=mirror_y_axis(points[1, 1]), point2=mirror_y_axis(points[0, 1])))
        geom_list.append(s.ArcByCenterEnds(center=mirror_y_axis(points[1, 0]), point1=mirror_y_axis(points[0, 1]), point2=mirror_y_axis(points[0, 0]),
                                           direction=COUNTERCLOCKWISE))

    s.radialPattern(geomList=geom_list, vertexList=(), number=n, totalAngle=360.0, centerPoint=(0.0, 0.0))

    s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=points[-1, -1])

    return s


def create_sketch_block(model, sketch_name, geo_type, n, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)

    geom_list = []
    geom_mirrored_list = []

    if geo_type == 'inner_polygon':
        geom_list.append(s.Line(point1=points[1, -2], point2=points[1, 2]))
        geom_list.append(s.ArcByCenterEnds(center=points[0, 2], point1=points[1, 2], point2=points[1, 1], direction=COUNTERCLOCKWISE))
        geom_list.append(s.Line(point1=points[1, 1], point2=points[0, 1]))
        geom_list.append(s.Line(point1=points[1, 0], point2=points[0, 1]))
        geom_list.append(s.Line(point1=points[1, -2], point2=points[-4, -2]))

        geom_mirrored_list.append(s.Line(point1=mirror_y_axis(points[1, -2]), point2=mirror_y_axis(points[1, 2])))
        geom_mirrored_list.append(
            s.ArcByCenterEnds(center=mirror_y_axis(points[0, 2]), point1=mirror_y_axis(points[1, 2]), point2=mirror_y_axis(points[1, 1]), direction=CLOCKWISE))
        geom_mirrored_list.append(s.Line(point1=mirror_y_axis(points[1, 1]), point2=mirror_y_axis(points[0, 1])))
        geom_mirrored_list.append(s.Line(point1=mirror_y_axis(points[1, 0]), point2=mirror_y_axis(points[0, 1])))
        geom_mirrored_list.append(s.Line(point1=mirror_y_axis(points[1, -2]), point2=mirror_y_axis(points[-4, -2])))
    else:
        geom_list.append(s.Line(point1=points[1, -2], point2=points[1, 2]))
        geom_list.append(s.ArcByCenterEnds(center=points[0, 2], point1=points[1, 2], point2=points[1, 1], direction=COUNTERCLOCKWISE))
        geom_list.append(s.Line(point1=points[1, 1], point2=points[0, 1]))
        geom_list.append(s.ArcByCenterEnds(center=points[1, 0], point1=points[0, 1], point2=points[0, 0], direction=CLOCKWISE))
        geom_list.append(s.Line(point1=points[1, -2], point2=points[-4, -2]))

        geom_mirrored_list.append(s.Line(point1=mirror_y_axis(points[1, -2]), point2=mirror_y_axis(points[1, 2])))
        geom_mirrored_list.append(
            s.ArcByCenterEnds(center=mirror_y_axis(points[0, 2]), point1=mirror_y_axis(points[1, 2]), point2=mirror_y_axis(points[1, 1]), direction=CLOCKWISE))
        geom_mirrored_list.append(s.Line(point1=mirror_y_axis(points[1, 1]), point2=mirror_y_axis(points[0, 1])))
        geom_mirrored_list.append(s.ArcByCenterEnds(center=mirror_y_axis(points[1, 0]), point1=mirror_y_axis(points[0, 1]), point2=mirror_y_axis(points[0, 0]),
                                                    direction=COUNTERCLOCKWISE))
        geom_mirrored_list.append(s.Line(point1=mirror_y_axis(points[1, -2]), point2=mirror_y_axis(points[-4, -2])))

    s.radialPattern(geomList=geom_mirrored_list, vertexList=(), number=2, totalAngle=360.0 / n * 1, centerPoint=(0.0, 0.0))
    s.delete(objectList=geom_mirrored_list)

    theta = 2.0 * math.pi / n
    x = mirror_y_axis(points[-4, -2])[0]
    y = mirror_y_axis(points[-4, -2])[1]
    x_p = x * math.cos(theta) - y * math.sin(theta)
    y_p = x * math.sin(theta) + y * math.cos(theta)

    s.ArcByCenterEnds(center=(0.0, 0.0), point1=points[-4, -2], point2=(x_p, y_p), direction=COUNTERCLOCKWISE)

    return s


def create_sketch_block_front(model, sketch_name, n, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)

    geom_list = []
    geom_mirrored_list = []

    x_p, y_p = line_intersection(points[1, 0], points[0, 1], points[1, -2], points[-4, -2])
    geom_list.append(s.Line(point1=points[1, 0], point2=(x_p, y_p)))
    geom_list.append(s.Line(point1=(x_p, y_p), point2=points[-4, -2]))

    geom_mirrored_list.append(s.Line(point1=mirror_y_axis(points[1, 0]), point2=mirror_y_axis([x_p, y_p])))
    geom_mirrored_list.append(s.Line(point1=mirror_y_axis([x_p, y_p]), point2=mirror_y_axis(points[-4, -2])))

    s.radialPattern(geomList=geom_mirrored_list, vertexList=(), number=2, totalAngle=360.0 / n * 1, centerPoint=(0.0, 0.0))
    s.delete(objectList=geom_mirrored_list)

    theta = 2.0 * math.pi / n
    x = mirror_y_axis(points[-4, -2])[0]
    y = mirror_y_axis(points[-4, -2])[1]
    x_p = x * math.cos(theta) - y * math.sin(theta)
    y_p = x * math.sin(theta) + y * math.cos(theta)

    s.ArcByCenterEnds(center=(0.0, 0.0), point1=points[-4, -2], point2=(x_p, y_p), direction=COUNTERCLOCKWISE)

    return s


def create_sketch_block_front_half(model, sketch_name, n, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)

    x_p, y_p = line_intersection(points[1, 0], points[0, 1], points[1, -2], points[-4, -2])
    s.Line(point1=points[1, 0], point2=(x_p, y_p))
    s.Line(point1=(x_p, y_p), point2=points[-4, -2])

    theta = 2.0 * math.pi / n / 2.0
    x = mirror_y_axis(points[-4, -1])[0]
    y = mirror_y_axis(points[-4, -1])[1]
    x_p = x * math.cos(theta) - y * math.sin(theta)
    y_p = x * math.sin(theta) + y * math.cos(theta)

    s.ArcByCenterEnds(center=(0.0, 0.0), point1=points[-4, -2], point2=(x_p, y_p), direction=COUNTERCLOCKWISE)

    s.Line(point1=(x_p, y_p), point2=points[1, 0])

    return s


def create_sketch_block_front_cut(model, sketch_name, n, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)

    geom_list = []
    geom_mirrored_list = []

    geom_list.append(s.Line(point1=points[1, -2], point2=points[1, 2]))
    geom_list.append(s.ArcByCenterEnds(center=points[0, 2], point1=points[1, 2], point2=points[1, 1], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[1, 1], point2=points[0, 1]))
    geom_list.append(s.Line(point1=points[1, 0], point2=points[0, 1]))

    geom_list.append(s.Line(point1=points[1, -2], point2=[points[1, -2][0], points[1, 0][1]]))
    geom_list.append(s.Line(point1=points[1, 0], point2=[points[1, -2][0], points[1, 0][1]]))

    s.radialPattern(geomList=geom_mirrored_list, vertexList=(), number=2, totalAngle=360.0 / n * 1, centerPoint=(0.0, 0.0))
    s.delete(objectList=geom_mirrored_list)

    theta = 2.0 * math.pi / n
    x = mirror_y_axis(points[-4, -2])[0]
    y = mirror_y_axis(points[-4, -2])[1]
    x_p = x * math.cos(theta) - y * math.sin(theta)
    y_p = x * math.sin(theta) + y * math.cos(theta)

    l = s.Line(point1=points[1, 0], point2=[points[1, -2][0], points[1, 0][1]])
    s.setAsConstruction(objectList=(l,))
    s.sketchOptions.setValues(constructionGeometry=ON)
    s.assignCenterline(line=l)

    return s


def create_sketch_section_cut_radius(model, sketch_name, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200)
    for i in range(2, points.shape[0]):
        s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=points[i, -1])
    return s


def create_sketch_section_cut_theta(model, sketch_name, n, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200)

    geom_list = []

    # middle
    geom_list.append(s.Line(point1=points[1, -1], point2=points[-1, -1]))

    # left
    geom_list.append(s.Line(point1=points[0, 0], point2=points[-1, 0]))
    geom_list.append(s.Line(point1=points[1, 0], point2=points[0, 1]))

    for j in [1, 2]:
        geom_list.append(s.Line(point1=points[1, j], point2=points[2, j]))
        geom_list.append(s.Line(point1=points[2, j], point2=points[-1, j]))

    for j in range(3, points.shape[1] - 1):
        geom_list.append(s.Line(point1=points[1, j], point2=points[-1, j]))

    # right
    geom_list.append(s.Line(point1=mirror_y_axis(points[0, 0]), point2=mirror_y_axis(points[-1, 0])))
    geom_list.append(s.Line(point1=mirror_y_axis(points[1, 0]), point2=mirror_y_axis(points[0, 1])))

    for j in [1, 2]:
        geom_list.append(s.Line(point1=mirror_y_axis(points[1, j]), point2=mirror_y_axis(points[2, j])))
        geom_list.append(s.Line(point1=mirror_y_axis(points[2, j]), point2=mirror_y_axis(points[-1, j])))

    for j in range(3, points.shape[1] - 1):
        geom_list.append(s.Line(point1=mirror_y_axis(points[1, j]), point2=mirror_y_axis(points[-1, j])))

    s.radialPattern(geomList=geom_list, vertexList=(), number=n, totalAngle=360.0, centerPoint=(0.0, 0.0))

    return s


def create_sketch_4(model, sketch_name, n, points):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)

    geom_list = []
    geom_list.append(s.Line(point1=points[1, -2], point2=points[-4, -2]))
    geom_list.append(s.Line(point1=mirror_y_axis(points[1, -2]), point2=mirror_y_axis(points[-4, -2])))
    geom_list.append(s.ArcByCenterEnds(center=[0.0, 0.0], point1=mirror_y_axis(points[-4, -2]), point2=points[-4, -2], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[1, -2], point2=mirror_y_axis(points[1, -2])))

    return s


def create_part(model, sketch, part_name, z_length):
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(sketch=sketch, depth=z_length)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_front_2(model, part, part_name, shift, sketch_cut_outer):
    p = model.Part(name=part_name, objectToCopy=part)

    plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    edge = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    d = p.datums

    plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    t = p.MakeSketchTransform(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s = model.ConstrainedSketch(name='__profile__', sheetSize=100.0, gridSpacing=100.0, transform=t)
    g = s.geometry
    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    s.retrieveSketch(sketch=sketch_cut_outer)
    s.move(vector=(-shift, 0.0), objectList=g.values())
    l = s.ConstructionLine(point1=(0.0, 0.0), angle=0.0)
    s.sketchOptions.setValues(constructionGeometry=ON)
    s.assignCenterline(line=l)
    p.CutRevolve(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s, angle=90.0,
                 flipRevolveDirection=OFF)
    del model.sketches['__profile__']

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_behind_3(model, part, part_name, points):
    p = model.Part(name=part_name, objectToCopy=part)
    plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    edge = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    d = p.datums
    t = p.MakeSketchTransform(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s = model.ConstrainedSketch(name='__profile__', sheetSize=100.0, gridSpacing=100.0, transform=t)

    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)

    p1 = (0.0, points[1, -1, 1] + 5.0)
    p2 = (-points[1, -1, 1] + 5.0, 0)
    p3 = (0.0, 0.0)

    s.Line(point1=p1, point2=p2)
    s.Line(point1=p2, point2=p3)
    s.Line(point1=p3, point2=p1)
    l = s.ConstructionLine(point1=(0.0, 0.0), angle=0.0)
    s.assignCenterline(line=l)
    p.CutRevolve(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s, angle=90.0,
                 flipRevolveDirection=OFF)
    s.unsetPrimaryObject()
    del model.sketches['__profile__']

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_behind_2(model, part, part_name, radius):
    p = model.Part(name=part_name, objectToCopy=part)
    plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    edge = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    d = p.datums
    t = p.MakeSketchTransform(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s = model.ConstrainedSketch(name='__profile__', sheetSize=100.0, gridSpacing=100.0, transform=t)
    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(0.0, radius))
    p.CutExtrude(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s, flipExtrudeDirection=ON)
    s.unsetPrimaryObject()
    del model.sketches['__profile__']

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_behind_1(model, part, part_name, radius, sketch_cut_outer):
    p = model.Part(name=part_name, objectToCopy=part)
    plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    edge = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    d = p.datums
    t = p.MakeSketchTransform(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s = model.ConstrainedSketch(name='__profile__', sheetSize=100.0, gridSpacing=100.0, transform=t)
    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    s.CircleByCenterPerimeter(center=(0.0, 0.0), point1=(0.0, radius))
    p.CutExtrude(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s, flipExtrudeDirection=ON)
    s.unsetPrimaryObject()
    del model.sketches['__profile__']

    plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    t = p.MakeSketchTransform(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s = model.ConstrainedSketch(name='__profile__', sheetSize=100.0, gridSpacing=100.0, transform=t)
    g = s.geometry
    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    s.retrieveSketch(sketch=sketch_cut_outer)
    s.move(vector=(0.0, 0.0), objectList=g.values())
    l = s.ConstructionLine(point1=(0.0, 0.0), angle=0.0)
    s.sketchOptions.setValues(constructionGeometry=ON)
    s.assignCenterline(line=l)
    p.CutRevolve(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s, angle=90.0,
                 flipRevolveDirection=OFF)
    del model.sketches['__profile__']

    # p.deleteFeatures(('Datum plane-1', 'Partition cell-5',))

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_front(model, sketch, sketch_cut, sketch_cut_outer, part_name, z_length):
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(sketch=sketch, depth=z_length)

    d = p.datums

    cut_depth = 183.418843

    plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    edge = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    p.CutExtrude(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=sketch_cut, depth=cut_depth,
                 flipExtrudeDirection=ON)

    plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=cut_depth)
    t = p.MakeSketchTransform(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s = model.ConstrainedSketch(name='__profile__', sheetSize=100.0, gridSpacing=100.0, transform=t)
    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    s.retrieveSketch(sketch=sketch_cut)
    p.CutRevolve(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s, angle=90.0,
                 flipRevolveDirection=ON)
    del model.sketches['__profile__']

    plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    t = p.MakeSketchTransform(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s = model.ConstrainedSketch(name='__profile__', sheetSize=100.0, gridSpacing=100.0, transform=t)
    g = s.geometry
    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    s.retrieveSketch(sketch=sketch_cut_outer)
    s.move(vector=(-1391.0, 0.0), objectList=g.values())
    l = s.ConstructionLine(point1=(0.0, 0.0), angle=0.0)
    s.sketchOptions.setValues(constructionGeometry=ON)
    s.assignCenterline(line=l)
    p.CutRevolve(sketchPlane=d[plane.id], sketchUpEdge=d[edge.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s, angle=90.0,
                 flipRevolveDirection=OFF)
    del model.sketches['__profile__']

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_shell(model, sketch, part_name, z_length):
    p = model.Part(name=part_name, dimensionality=THREE_D, type=DEFORMABLE_BODY)
    p.BaseSolidExtrude(sketch=sketch, depth=z_length)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def partition_part_front(model, part, sketch_cut_latitude, sketch_cut_longitude, geo_type, n, points, lines, z_list):
    z_0 = 0.0
    part_type = 'block'
    p = part
    d = p.datums
    datum_id = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS).id
    # p.PartitionFaceBySketch(sketchUpEdge=p.datums[datum_id],
    #                         faces=p.faces.getByBoundingBox(-points[-1, -1, 1], -points[-1, -1, 1], z_0, points[-1, -1, 1], points[-1, -1, 1], z_0),
    #                         sketchOrientation=TOP, sketch=sketch_cut_latitude)
    #
    # p.PartitionFaceBySketch(sketchUpEdge=p.datums[datum_id],
    #                         faces=p.faces.getByBoundingBox(-points[-1, -1, 1], -points[-1, -1, 1], z_0, points[-1, -1, 1], points[-1, -1, 1], z_0),
    #                         sketchOrientation=TOP, sketch=sketch_cut_longitude)

    f, e, d = p.faces, p.edges, p.datums
    t = p.MakeSketchTransform(sketchPlane=f[13], sketchUpEdge=d[3], sketchPlaneSide=SIDE1, origin=(0.0, 0.0, 0.0))
    s = model.ConstrainedSketch(name='__profile__', sheetSize=100.0, gridSpacing=100.0, transform=t)
    g = s.geometry
    p.projectReferencesOntoSketch(sketch=s, filter=COPLANAR_EDGES)
    s.offset(distance=points[-1, -2, 0] - points[-1, -3, 0], objectList=(g[2], g[5], g[6], g[7], g[8]), side=RIGHT)

    f = p.faces
    pickedFaces = f.getSequenceFromMask(mask=('[#2000 ]',), )
    p.PartitionFaceBySketch(sketchUpEdge=d[3], faces=pickedFaces, sketch=s)
    del model.sketches['__profile__']

    c = p.cells
    pickedCells = c.getSequenceFromMask(mask=('[#1 ]',), )
    e = p.edges
    pickedEdges = (e[0], e[1], e[2], e[3], e[4])
    p.PartitionCellBySweepEdge(sweepPath=e[14], cells=pickedCells, edges=pickedEdges)

    plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=points[-1, -3, 0])
    p.PartitionCellByDatumPlane(datumPlane=d[plane.id], cells=p.cells)
    plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=z_list[1])
    p.PartitionCellByDatumPlane(datumPlane=d[plane.id], cells=p.cells)


def partition_part(model, part, sketch_cut_latitude, sketch_cut_longitude, geo_type, part_type, n, points, lines, z_list):
    z_0 = 0.0
    p = part
    datum_id = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS).id
    p.PartitionFaceBySketch(sketchUpEdge=p.datums[datum_id],
                            faces=p.faces.getByBoundingBox(-points[-1, -1, 1], -points[-1, -1, 1], z_0, points[-1, -1, 1], points[-1, -1, 1], z_0),
                            sketchOrientation=TOP, sketch=sketch_cut_latitude)

    total_z_length = z_list[-1]

    # swap_edge = p.edges.findAt((points[1, 1, 0], points[1, 1, 1], total_z_length / 2))

    x = points[3, -2, 0]
    y = points[3, -2, 1]
    swap_edge = p.edges.getByBoundingBox(x - 5.0, y - 5.0, 0.0, x + 5.0, y + 5.0, total_z_length)[1]

    if part_type == 'block':
        cut_edges = (p.edges.findAt((points[2, 0, 0], points[2, 0, 1], z_0)),
                     p.edges.findAt((points[3, 0, 0], points[3, 0, 1], z_0)))
    else:
        cut_edges = (p.edges.findAt((points[2, 0, 0], points[2, 0, 1], z_0)),
                     p.edges.findAt((points[3, 0, 0], points[3, 0, 1], z_0)),
                     p.edges.findAt((points[4, 0, 0], points[4, 0, 1], z_0)),
                     p.edges.findAt((points[5, 0, 0], points[5, 0, 1], z_0)),
                     p.edges.findAt((points[6, 0, 0], points[6, 0, 1], z_0)))

    cut_edges = (p.edges.findAt((points[3, 0, 0], points[3, 0, 1], z_0)),)
    p.PartitionCellBySweepEdge(sweepPath=swap_edge, cells=p.cells, edges=cut_edges)

    cut_edges = (p.edges.findAt((points[2, 0, 0], points[2, 0, 1], z_0)),)
    swap_edge = p.edges.findAt((points[1, 1, 0], points[1, 1, 1], total_z_length / 2))
    p.PartitionCellBySweepEdge(sweepPath=swap_edge, cells=p.cells, edges=cut_edges)

    p.PartitionFaceBySketch(sketchUpEdge=p.datums[datum_id],
                            faces=p.faces.getByBoundingBox(-points[-1, -1, 1], -points[-1, -1, 1], z_0, points[-1, -1, 1], points[-1, -1, 1], z_0),
                            sketchOrientation=TOP, sketch=sketch_cut_longitude)

    line_keys = []
    if geo_type == 'inner_polygon':
        pass
    else:
        line_keys += ['00-10', '10-01']

    # if part_type == 'block':
    #     line_keys += ['11-21', '21-31', '31-41']
    #     line_keys += ['12-22', '22-32', '32-42']
    #     line_keys += ['13-23', '23-33', '33-43']
    if part_type == 'block':
        line_keys += ['11-21', '21-31', '31-41']
        line_keys += ['12-22', '22-32', '32-42']
        line_keys += ['13-23', '23-33', '33-43']
        line_keys += ['14-24', '24-34', '34-44']
    else:
        line_keys += ['11-21', '21-31', '31-41', '41-51', '51-61', '61-71']
        line_keys += ['12-22', '22-32', '32-42', '42-52', '52-62', '62-72']
        line_keys += ['13-23', '23-33', '33-43', '43-53', '53-63', '63-73']
        line_keys += ['14-24', '24-34', '34-44', '44-54', '54-64', '64-74']

    z_axis_id = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS).id

    for i in range(0, n, 1):
        print(i)
        theta = i * 2 * math.pi / n
        p = model.parts['PART-BLOCK-FRONT-2']
        swap_edge = p.edges.findAt((points[1, 1, 0], points[1, 1, 1], total_z_length / 2))
        partition_edges = []
        for line_key in line_keys:
            line_middle_point = lines[line_key][2]
            x, y = line_middle_point
            x_p = x * math.cos(theta) - y * math.sin(theta)
            y_p = x * math.sin(theta) + y * math.cos(theta)
            edge_sequence = p.edges.findAt(((x_p, y_p, z_0),))
            if len(edge_sequence) > 0:
                partition_edges.append(edge_sequence[0])

            x, y = line_middle_point
            x = -x
            x_p = x * math.cos(theta) - y * math.sin(theta)
            y_p = x * math.sin(theta) + y * math.cos(theta)
            edge_sequence = p.edges.findAt(((x_p, y_p, z_0),))
            if len(edge_sequence) > 0:
                partition_edges.append(edge_sequence[0])
        if partition_edges:
            # p.PartitionCellBySweepEdge(sweepPath=swap_edge, cells=p.cells, edges=partition_edges)
            p.PartitionCellByExtrudeEdge(line=p.datums[z_axis_id], cells=p.cells, edges=partition_edges, sense=FORWARD)

    if part_type == 'block':
        x = d * math.cos(-(n - 1) * math.pi / n + math.pi / 2.0)
        y = d * math.sin(-(n - 1) * math.pi / n + math.pi / 2.0)
        p.PartitionCellByPlaneThreePoints(cells=p.cells, point1=(0.0, 0.0, 0.0), point2=(0.0, 0.0, total_z_length), point3=(x, y, 0.0))
    else:
        for i in range(0, n, 1):
            x = d * math.cos(-i * math.pi / n + math.pi / 2.0)
            y = d * math.sin(-i * math.pi / n + math.pi / 2.0)
            p.PartitionCellByPlaneThreePoints(cells=p.cells, point1=(0.0, 0.0, 0.0), point2=(0.0, 0.0, total_z_length), point3=(x, y, 0.0))

    for z in z_list[1:-1]:
        print(z)
        datum_id = part.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=z).id
        part.PartitionCellByDatumPlane(datumPlane=p.datums[datum_id], cells=p.cells)


def create_sets_common(set_name, part, n, layer_number, layer_height, layer_gap, faces, z_list, cell_points):
    c = faces[cell_points[0][0], cell_points[0][1]]
    z = cell_points[0][2]
    cells = part.cells.findAt([[c[0], c[1], z], ])

    for l in range(layer_number):
        for i in range(0, n, 1):
            theta = i * 2 * math.pi / n
            for cell_point in cell_points:
                c = faces[cell_point[0], cell_point[1]]
                x = c[0] * math.cos(theta) - c[1] * math.sin(theta)
                y = c[0] * math.sin(theta) + c[1] * math.cos(theta)
                z = cell_point[2] + l * (layer_height + layer_gap)
                if z < z_list[-1]:
                    cells += part.cells.findAt([[x, y, z], ])

                x = -c[0] * math.cos(theta) - c[1] * math.sin(theta)
                y = -c[0] * math.sin(theta) + c[1] * math.cos(theta)
                z = cell_point[2] + l * (layer_height + layer_gap)
                if z < z_list[-1]:
                    cells += part.cells.findAt([[x, y, z], ])

    part.Set(cells=cells, name=set_name)


def create_surfaces_common(surface_name, part, n, layer_number, layer_height, layer_gap, faces, z_list, faces_points):
    faces = part.faces.findAt([faces_points[0], ])

    for faces_point in faces_points[1:]:
        faces += part.faces.findAt([faces_point, ])

    part.Surface(side1Faces=faces, name=surface_name)


def create_sets(part, geo_type, n, layer_number, layer_height, layer_gap, faces, z_list):
    print(z_list)
    p = part

    # SET-INSULATION-GRAIN
    cell_points = []
    z = (z_list[0] + z_list[1]) / 2.0
    if geo_type == 'inner_polygon':
        pass
    else:
        cell_points.append([0, 0, z])
    for i in range(1, faces.shape[0] - 3):
        for j in range(0, faces.shape[1] - 1):
            cell_points.append([i, j, z])

    z = (z_list[1] + z_list[2]) / 2.0
    for i in range(3, 4):
        for j in range(0, faces.shape[1] - 1):
            cell_points.append([i, j, z])
    for i in range(1, 3):
        for j in range(3, 4):
            cell_points.append([i, j, z])

    z = (z_list[2] + z_list[3]) / 2.0
    if geo_type == 'inner_polygon':
        pass
    else:
        cell_points.append([0, 0, z])
    for i in range(1, faces.shape[0] - 3):
        for j in range(0, faces.shape[1] - 1):
            cell_points.append([i, j, z])

    create_sets_common('SET-INSULATION-GRAIN', part, n, layer_number, layer_height, layer_gap, faces, z_list, cell_points)

    # SET-GRAIN
    cell_points = []
    z = (z_list[1] + z_list[2]) / 2.0
    if geo_type == 'inner_polygon':
        pass
    else:
        cell_points.append([0, 0, z])
    for i in range(1, faces.shape[0] - 4):
        for j in range(0, faces.shape[1] - 2):
            cell_points.append([i, j, z])

    create_sets_common('SET-GRAIN', part, n, layer_number, layer_height, layer_gap, faces, z_list, cell_points)

    # SET-GAP
    cell_points = []
    z = (z_list[0] + z_list[1]) / 2.0
    for i in range(1, faces.shape[0] - 3):
        cell_points.append([i, faces.shape[1] - 1, z])

    z = (z_list[1] + z_list[2]) / 2.0
    for i in range(1, faces.shape[0] - 3):
        cell_points.append([i, faces.shape[1] - 1, z])

    z = (z_list[2] + z_list[3]) / 2.0
    for i in range(1, faces.shape[0] - 3):
        cell_points.append([i, faces.shape[1] - 1, z])

    z = (z_list[3] + z_list[4]) / 2.0
    if geo_type == 'inner_polygon':
        pass
    else:
        cell_points.append([0, 0, z])
    for i in range(1, faces.shape[0] - 3):
        for j in range(0, faces.shape[1]):
            cell_points.append([i, j, z])

    create_sets_common('SET-GAP', part, n, layer_number, layer_height, layer_gap, faces, z_list, cell_points)

    # SET-TIE
    cell_points = []
    z = (z_list[0] + z_list[1]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 3, j, z])

    z = (z_list[1] + z_list[2]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 3, j, z])

    z = (z_list[2] + z_list[3]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 3, j, z])

    z = (z_list[3] + z_list[4]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 3, j, z])

    create_sets_common('SET-TIE', part, n, layer_number, layer_height, layer_gap, faces, z_list, cell_points)

    # SET-INSULATION-SHELL
    cell_points = []
    z = (z_list[0] + z_list[1]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 2, j, z])

    z = (z_list[1] + z_list[2]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 2, j, z])

    z = (z_list[2] + z_list[3]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 2, j, z])

    z = (z_list[3] + z_list[4]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 2, j, z])

    create_sets_common('SET-INSULATION-SHELL', part, n, layer_number, layer_height, layer_gap, faces, z_list, cell_points)

    # SET-SHELL
    cell_points = []
    z = (z_list[0] + z_list[1]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 1, j, z])

    z = (z_list[1] + z_list[2]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 1, j, z])

    z = (z_list[2] + z_list[3]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 1, j, z])

    z = (z_list[3] + z_list[4]) / 2.0
    for j in range(0, faces.shape[1]):
        cell_points.append([faces.shape[0] - 1, j, z])

    create_sets_common('SET-SHELL', part, n, layer_number, layer_height, layer_gap, faces, z_list, cell_points)

    f1 = p.faces.getByBoundingCylinder(center1=(0, 0, 0), center2=(0, 0, z_list[-1]), radius=points[2, -1, 1] - 1.0)
    p.Surface(side1Faces=f1, name='SURF-INNER')

    b = p.cells.getBoundingBox()
    x0 = b['low'][0]
    y0 = b['low'][1]
    z0 = b['low'][2]
    x1 = b['high'][0]
    y1 = b['high'][1]
    z1 = b['high'][2]
    p.Set(faces=p.faces.getByBoundingBox(x0, y0, z0, x1, y1, z0), name='SET-Z0')
    p.Set(faces=p.faces.getByBoundingBox(x0, y0, z1, x1, y1, z1), name='SET-Z1')

    f2 = p.faces.getByBoundingCylinder(center1=(0, 0, 0), center2=(0, 0, 1e-6), radius=points[4, -1, 1] - 1.0)
    p.Surface(side1Faces=f2, name='SURF-Z0-PRESSURE')


def create_sets_block(part, geo_type, n, layer_number, layer_height, layer_gap, faces, z_list):
    print(z_list)
    p = part
    m = n

    # SET-INSULATION-GRAIN
    cell_points = []
    z = (z_list[0] + z_list[1]) / 2.0
    if geo_type == 'inner_polygon':
        pass
    else:
        cell_points.append([0, 0, z])
    for i in range(1, faces.shape[0] - 3):
        for j in range(0, faces.shape[1] - 1):
            cell_points.append([i, j, z])

    z = (z_list[1] + z_list[2]) / 2.0
    for i in range(3, 4):
        for j in range(0, faces.shape[1] - 1):
            cell_points.append([i, j, z])
    for i in range(1, 3):
        for j in range(3, 4):
            cell_points.append([i, j, z])

    z = (z_list[2] + z_list[3]) / 2.0
    if geo_type == 'inner_polygon':
        pass
    else:
        cell_points.append([0, 0, z])
    for i in range(1, faces.shape[0] - 3):
        for j in range(0, faces.shape[1] - 1):
            cell_points.append([i, j, z])

    create_sets_common('SET-INSULATION-GRAIN', part, m, layer_number, layer_height, layer_gap, faces, z_list, cell_points)

    # SET-GRAIN
    cell_points = []
    z = (z_list[1] + z_list[2]) / 2.0
    if geo_type == 'inner_polygon':
        pass
    else:
        cell_points.append([0, 0, z])
    for i in range(1, faces.shape[0] - 4):
        for j in range(0, faces.shape[1] - 2):
            cell_points.append([i, j, z])

    create_sets_common('SET-GRAIN', part, m, layer_number, layer_height, layer_gap, faces, z_list, cell_points)

    faces_points = []
    for key in ['14-24', '24-34', '34-44']:
        for z in [(z_list[0] + z_list[1]) / 2.0, (z_list[1] + z_list[2]) / 2.0, (z_list[2] + z_list[3]) / 2.0]:
            x = lines[key][2][0]
            y = lines[key][2][1]
            faces_points.append([x, y, z])
    create_surfaces_common('SURF-T0', part, n, layer_number, layer_height, layer_gap, faces, z_list, faces_points)

    faces_points = []
    theta = 1 * 2 * math.pi / n
    for key in ['14-24', '24-34', '34-44']:
        for z in [(z_list[0] + z_list[1]) / 2.0, (z_list[1] + z_list[2]) / 2.0, (z_list[2] + z_list[3]) / 2.0]:
            xm = lines[key][2][0]
            ym = lines[key][2][1]
            x = -xm * math.cos(theta) - ym * math.sin(theta)
            y = -xm * math.sin(theta) + ym * math.cos(theta)
            faces_points.append([x, y, z])
    create_surfaces_common('SURF-T1', part, n, layer_number, layer_height, layer_gap, faces, z_list, faces_points)

    faces_points = []
    for key in ['40-41', '41-42', '42-43']:
        for z in [(z_list[0] + z_list[1]) / 2.0, (z_list[1] + z_list[2]) / 2.0, (z_list[2] + z_list[3]) / 2.0]:
            x = lines[key][2][0]
            y = lines[key][2][1]
            faces_points.append([x, y, z])

    theta = 1 * 2 * math.pi / n
    for key in ['40-41', '41-42', '42-43']:
        for z in [(z_list[0] + z_list[1]) / 2.0, (z_list[1] + z_list[2]) / 2.0, (z_list[2] + z_list[3]) / 2.0]:
            xm = lines[key][2][0]
            ym = lines[key][2][1]
            x = -xm * math.cos(theta) - ym * math.sin(theta)
            y = -xm * math.sin(theta) + ym * math.cos(theta)
            faces_points.append([x, y, z])

    create_surfaces_common('SURF-OUTER', part, n, layer_number, layer_height, layer_gap, faces, z_list, faces_points)

    f1 = p.faces.getByBoundingCylinder(center1=(0, 0, 0), center2=(0, 0, z_list[-1]), radius=points[2, -1, 1] - 1.0)
    p.Surface(side1Faces=f1, name='SURF-INNER')

    b = p.cells.getBoundingBox()
    x0 = b['low'][0]
    y0 = b['low'][1]
    z0 = b['low'][2]
    x1 = b['high'][0]
    y1 = b['high'][1]
    z1 = b['high'][2]

    p.Surface(side1Faces=p.faces.getByBoundingBox(x0, y0, z0, x1, y1, z0), name='SURF-Z0')
    p.Surface(side1Faces=p.faces.getByBoundingBox(x0, y0, z1, x1, y1, z1), name='SURF-Z1')


if __name__ == "__main__":
    geo_type = 'inner_polygon'
    part_type = 'block'

    epsilon = 0.95
    n = 9
    beta = math.pi / n
    zeta = beta * 2.0 + 3.0 * math.pi / 180.0
    r1 = 35.0
    r2 = 50.0
    d2 = 513.8
    radius_insulation_thickness = 3.0
    radius_gap = 4.0
    shell_insulation_thickness = 10.0
    shell_thickness = 30.0

    d = (1767.5 - radius_insulation_thickness) * 2.0
    e = 862.9 - radius_insulation_thickness

    theta_insulation_thickness = 3.0
    theta_gap = 9.0

    layer_height = 1229.0
    layer_insulation_thickness = 2.5
    layer_gap = 18.0
    layer_number = 11

    z_list = get_z_list(layer_height, layer_insulation_thickness, layer_gap, layer_number)
    if part_type == 'block':
        z_list = z_list[:4]
    block_z_length = z_list[3]
    total_z_length = z_list[-1]

    element_size = 80

    first_layer_height = 1391.0
    shell_insulation_ref_z = 407.581146

    model = mdb.models['Model-1']
    model.setValues(absoluteZero=-273.15)

    set_material(model.Material(name='MATERIAL-GRAIN'), load_json('material_grain_prony.json'))
    set_material(model.Material(name='MATERIAL-INSULATION'), load_json('material_insulation.json'))
    set_material(model.Material(name='MATERIAL-KINEMATIC'), load_json('material_kinematic.json'))
    set_material(model.Material(name='MATERIAL-SHELL'), load_json('material_shell.json'))

    model.HomogeneousSolidSection(name='SECTION-GRAIN', material='MATERIAL-GRAIN', thickness=None)
    model.HomogeneousSolidSection(name='SECTION-INSULATION', material='MATERIAL-INSULATION', thickness=None)
    model.HomogeneousSolidSection(name='SECTION-KINEMATIC', material='MATERIAL-KINEMATIC', thickness=None)
    model.HomogeneousSolidSection(name='SECTION-SHELL', material='MATERIAL-SHELL', thickness=None)

    mdb.ModelFromInputFile(name='PART-INSULATION-SHELL', inputFileName='F:/GitHub/base/base/utils/flow/part_insulation_shell.inp')
    p_insulation_shell = mdb.models['Model-1'].Part('PART-INSULATION-SHELL', mdb.models['PART-INSULATION-SHELL'].parts['PART-INSULATION-SHELL'])

    mdb.ModelFromInputFile(name='PART-SHELL', inputFileName='F:/GitHub/base/base/utils/flow/part_shell.inp')
    p_shell = mdb.models['Model-1'].Part('PART-SHELL', mdb.models['PART-SHELL'].parts['PART-SHELL'])

    points, lines, faces = geometries(model, geo_type, d, e, epsilon, beta, zeta, r1, r2, d2, radius_insulation_thickness, radius_gap,
                                      shell_insulation_thickness,
                                      shell_thickness,
                                      theta_gap, theta_insulation_thickness)

    s_section = create_sketch_section(model, 'SKETCH-SECTION', geo_type, n, points)

    s_section_cut_radius = create_sketch_section_cut_radius(model, 'SKETCH-SECTION-CUT-RADIUS', points)

    s_section_cut_theta = create_sketch_section_cut_theta(model, 'SKETCH-SECTION-CUT-THETA', n, points)

    s4 = create_sketch_4(model, 'SKETCH-SECTION-4', n, points)

    s_block = create_sketch_block(model, 'SKETCH-BLOCK', geo_type, n, points)

    s_block_front_half = create_sketch_block_front_half(model, 'SKETCH-BLOCK-FRONT-HALF', n, points)

    s_block_front_cut = create_sketch_block_front_cut(model, 'SKETCH-BLOCK-FRONT-CUT', n, points)

    acis = mdb.openAcis('SKETCH-BLOCK-FRONT-CUT-OUTER.sat', scaleFromFile=OFF)
    s_block_front_cut_outer = model.ConstrainedSketchFromGeometryFile(name='SKETCH-BLOCK-FRONT-CUT-OUTER', geometryFile=acis)

    acis = mdb.openAcis('SKETCH-BLOCK-BEHIND-CUT-OUTER.sat', scaleFromFile=OFF)
    s_block_behind_cut_outer = model.ConstrainedSketchFromGeometryFile(name='SKETCH-BLOCK-BEHIND-CUT-OUTER', geometryFile=acis)

    # p_block_front = create_part_block_front(model, s_block_front_half, s_block_front_cut, s_block_front_cut_outer, 'PART-BLOCK-FRONT', first_layer_height)
    #
    # partition_part_front(model, p_block_front, s2, s3, geo_type, n, points, lines, z_list)
    #
    # p_block_front.Mirror(mirrorPlane=p_block_front.faces[15], keepOriginal=ON)
    #
    # p_block = create_part(model, s_block, 'PART-BLOCK', block_z_length)
    #
    # p_block_front_2 = create_part_front_2(model, p_block, 'PART-BLOCK-FRONT-2', first_layer_height + layer_height + layer_gap, s_block_front_cut_outer)

    # partition_part(model, p_block, s2, s3, geo_type, part_type, n, points, lines, z_list)

    # partition_part(model, p_block_front_2, s2, s3, geo_type, part_type, n, points, lines, z_list)
    #
    # create_sets_block(p_block, geo_type, n, layer_number, layer_height, layer_gap, faces, z_list)
    #
    # p_block_behind_3 = create_part_block_behind_3(model, p_block, 'PART-BLOCK-BEHIND-3', points)
    #
    # p_block_behind_2 = create_part_block_behind_2(model, p_block, 'PART-BLOCK-BEHIND-2', 905.0)
    #
    # p_block_0 = create_part(model, s_block, 'PART-BLOCK-0', block_z_length)
    #
    # p_block_behind_1 = create_part_block_behind_1(model, p_block_0, 'PART-BLOCK-BEHIND-1', 905.0, s_block_behind_cut_outer)

    # partition_part(model, p_block_behind_1, s2, s3, geo_type, part_type, n, points, lines, z_list)

    # p_block.SectionAssignment(region=p_block.sets['SET-GRAIN'], sectionName='SECTION-GRAIN', offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
    #                           thicknessAssignment=FROM_SECTION)
    # p_block.SectionAssignment(region=p_block.sets['SET-INSULATION-GRAIN'], sectionName='SECTION-INSULATION', offset=0.0, offsetType=MIDDLE_SURFACE,
    #                           offsetField='',
    #                           thicknessAssignment=FROM_SECTION)
    #
    # p_insulation_shell.SectionAssignment(region=p_insulation_shell.sets['ESET-ALL'], sectionName='SECTION-INSULATION',
    #                                      offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
    #                                      thicknessAssignment=FROM_SECTION)
    #
    # p_shell.SectionAssignment(region=p_shell.sets['ESET-ALL'], sectionName='SECTION-SHELL',
    #                           offset=0.0, offsetType=MIDDLE_SURFACE, offsetField='',
    #                           thicknessAssignment=FROM_SECTION)
    #
    # c = p_block.cells
    # elemType1 = mesh.ElemType(elemCode=C3D8H, secondOrderAccuracy=OFF, distortionControl=DEFAULT)
    # elemType2 = mesh.ElemType(elemCode=C3D6H, secondOrderAccuracy=OFF, distortionControl=DEFAULT)
    # elemType3 = mesh.ElemType(elemCode=C3D4H, secondOrderAccuracy=OFF, distortionControl=DEFAULT)
    # p_block.setElementType(regions=regionToolset.Region(cells=p_block.cells), elemTypes=(elemType1, elemType2, elemType3))
    # p_block.seedPart(size=element_size, deviationFactor=0.1, minSizeFactor=0.1)
    # p_block.generateMesh()
    #
    # a = model.rootAssembly
    # a.DatumCsysByDefault(CARTESIAN)
    #
    # a.Instance(name='PART-INSULATION-SHELL-1', part=p_insulation_shell, dependent=ON)
    # a.rotate(instanceList=('PART-INSULATION-SHELL-1',), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 1.0, 0.0), angle=90.0)
    #
    # a.Instance(name='PART-SHELL-1', part=p_shell, dependent=ON)
    # a.rotate(instanceList=('PART-SHELL-1',), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 1.0, 0.0), angle=90.0)
    #
    # m = n
    # m = 1

    # for i in range(m):
    #     instance_name = 'PART-BLOCK-FRONT-%s' % (i + 1)
    #     a.Instance(name=instance_name, part=p_block_front, dependent=ON)
    #     a.translate(instanceList=(instance_name,), vector=(0.0, 0.0, shell_insulation_ref_z - first_layer_height))
    #     a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)
    # layer_number = 3
    # m = 1
    # for l in range(1, layer_number):
    #     for i in range(m):
    #         instance_name = 'PART-BLOCK-%s-%s' % (l + 2, i + 1)
    #         a.Instance(name=instance_name, part=p_block, dependent=ON)
    #         a.translate(instanceList=(instance_name,), vector=(0.0, 0.0, shell_insulation_ref_z - first_layer_height - (l + 1) * (layer_gap + layer_height)))
    #         a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)

    # for i in range(m):
    #     instance_name = 'PART-BLOCK-BEHIND-3-%s' % (i + 1)
    #     a.Instance(name=instance_name, part=p_block_behind_3, dependent=ON)
    #     a.translate(instanceList=(instance_name,),
    #                 vector=(0.0, 0.0, shell_insulation_ref_z - first_layer_height - (layer_number + 1) * (layer_gap + layer_height)))
    #     a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)

    # for i in range(m):
    #     instance_name = 'PART-BLOCK-BEHIND-2-%s' % (i + 1)
    #     a.Instance(name=instance_name, part=p_block_behind_2, dependent=ON)
    #     a.translate(instanceList=(instance_name,),
    #                 vector=(0.0, 0.0, shell_insulation_ref_z - first_layer_height - (layer_number + 2) * (layer_gap + layer_height)))
    #     a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)

    # for i in range(m):
    #     instance_name = 'PART-BLOCK-BEHIND-1-%s' % (i + 1)
    #     a.Instance(name=instance_name, part=p_block_behind_1, dependent=ON)
    #     a.translate(instanceList=(instance_name,),
    #                 vector=(0.0, 0.0, shell_insulation_ref_z - first_layer_height - (layer_number + 3) * (layer_gap + layer_height)))
    #     a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)

    # model.Tie(name='CONSTRAINT-1',
    #           main=a.instances['PART-INSULATION-SHELL-1'].surfaces['SURF-OUTER'],
    #           secondary=a.instances['PART-SHELL-1'].surfaces['SURF-INNER'],
    #           positionToleranceMethod=COMPUTED, adjust=OFF, tieRotations=ON, thickness=ON)
    #
    # for l in range(1, layer_number):
    #     for i in range(m):
    #         name_1 = 'PART-INSULATION-SHELL-1'
    #         name_2 = 'PART-BLOCK-%s-%s' % (l + 2, i + 1)
    #         tie_name = 'CONSTRAINT-%s-%s' % (name_1, name_2)
    #         model.Tie(name=tie_name,
    #                   main=a.instances[name_1].surfaces['SURF-INNER'],
    #                   secondary=a.instances[name_2].surfaces['SURF-OUTER'],
    #                   positionToleranceMethod=COMPUTED, adjust=OFF, tieRotations=ON, thickness=ON)

    # model.CoupledTempDisplacementStep(name='Step-1', previous='Initial', deltmx=10.0, nlgeom=ON)
    # model.ImplicitDynamicsStep(name='Step-1', previous='Initial', nlgeom=ON, timePeriod=1.0, maxNumInc=1000000, initialInc=0.2, minInc=2e-05, maxInc=0.2)
    # model.StaticStep(name='Step-1', previous='Initial', nlgeom=ON, timePeriod=1.0, maxNumInc=1000000, initialInc=0.2, minInc=2e-05, maxInc=0.2)
    # model.HeatTransferStep(name='Step-1', previous='Initial', timePeriod=70.0, maxNumInc=1000000, initialInc=0.1, minInc=1e-9, maxInc=1.0, deltmx=100.0)
    #
    # model.fieldOutputRequests['F-Output-1'].setValues(frequency=2)
    # model.HistoryOutputRequest(name='H-Output-1', createStepName='Step-1', variables=('HTL',))
    #
    # model.TabularAmplitude(name='AMP-PRESSURE', timeSpan=STEP, smooth=SOLVER_DEFAULT, data=((0.0, 0.0), (1.0, 1.0)))
    # model.TabularAmplitude(name='AMP-TEMPERATURE', timeSpan=STEP, smooth=SOLVER_DEFAULT, data=((0.0, 20.0), (20.0, 2000.0)))
    # model.ExpressionField(name='ANALYTICALFIELD-PRESSURE', localCsys=None, description='', expression='1.0+0.05*fabs (  Z  ) / 18200.0')
    # model.ExpressionField(name='ANALYTICALFIELD-FILM', localCsys=None, description='', expression='1.0+0.2*fabs (  Z  ) / 18200.0')
    # model.ZsymmBC(name='BC-1', createStepName='Step-1', region=a.instances['PART-1-1'].sets['SET-Z0'], localCsys=None)
    # model.ZsymmBC(name='BC-2', createStepName='Step-1', region=a.instances['PART-1-1'].sets['SET-Z1'], localCsys=None)

    # model.DisplacementBC(name='BC-1', createStepName='Step-1', region=a.instances['PART-SHELL-1'].sets['NSET-OUTER'],
    #                      u1=0.0, u2=0.0, u3=0.0, ur1=0.0, ur2=0.0, ur3=0.0,
    #                      amplitude=UNSET, fixed=OFF, distributionType=UNIFORM, fieldName='',
    #                      localCsys=None)
    #
    # for l in range(1, layer_number):
    #     for i in range(m):
    #         for set_name in ['SURF-INNER', 'SURF-T0', 'SURF-T1', 'SURF-Z0', 'SURF-Z1']:
    #             part_name = 'PART-BLOCK-%s-%s' % (l + 2, i + 1)
    #             load_name = 'LOAD-%s-%s' % (part_name, set_name)
    #             model.Pressure(name=load_name, createStepName='Step-1', region=a.instances[part_name].surfaces[set_name], distributionType=FIELD,
    #                            field='ANALYTICALFIELD-PRESSURE', magnitude=11.6, amplitude='AMP-PRESSURE')

    # for l in range(1, layer_number):
    #     for i in range(m):
    #         for surf_name in ['SURF-INNER', 'SURF-T0', 'SURF-T1', 'SURF-Z0', 'SURF-Z1']:
    #             part_name = 'PART-BLOCK-%s-%s' % (l + 2, i + 1)
    #             int_name = 'INT-%s-%s' % (part_name, surf_name)
    #             model.FilmCondition(name=int_name, createStepName='Step-1',
    #                                 surface=a.instances[part_name].surfaces[surf_name], definition=FIELD, filmCoeff=100.0,
    #                                 field='ANALYTICALFIELD-FILM', filmCoeffAmplitude='', sinkTemperature=1.0, sinkAmplitude='AMP-TEMPERATURE',
    #                                 sinkDistributionType=UNIFORM, sinkFieldName='')
    #
    # for l in range(1, layer_number):
    #     for i in range(m):
    #         for set_name in ['SET-GRAIN', 'SET-INSULATION-GRAIN']:
    #             part_name = 'PART-BLOCK-%s-%s' % (l + 2, i + 1)
    #             field_name = 'PRE-%s-%s' % (part_name, set_name)
    #             model.Field(name=field_name, createStepName='Step-1',
    #                         region=a.instances[part_name].sets[set_name], distributionType=UNIFORM,
    #                         crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, fieldVariableNum=1,
    #                         magnitudes=(20.0,))
    #
    # model.Temperature(name='Predefined Field-1',
    #                   createStepName='Initial', region=a.instances['PART-SHELL-1'].sets['NSET-ALL'], distributionType=UNIFORM,
    #                   crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=(20.0,))
    #
    # model.Temperature(name='Predefined Field-2',
    #                   createStepName='Initial', region=a.instances['PART-INSULATION-SHELL-1'].sets['NSET-ALL'], distributionType=UNIFORM,
    #                   crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, magnitudes=(20.0,))
    #
    # elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
    # p_shell.setElementType(regions=(p_shell.elements,), elemTypes=(elemType1,))
    # p_insulation_shell.setElementType(regions=(p_insulation_shell.elements,), elemTypes=(elemType1,))
    # p_block.setElementType(regions=(p_block.cells,), elemTypes=(elemType1,))
    #
    # mdb.Job(name='Job-1', model='Model-1', description='', type=ANALYSIS,
    #         atTime=None, waitMinutes=0, waitHours=0, queue=None, memory=90,
    #         memoryUnits=PERCENTAGE, getMemoryFromAnalysis=True,
    #         explicitPrecision=SINGLE, nodalOutputPrecision=SINGLE, echoPrint=OFF,
    #         modelPrint=OFF, contactPrint=OFF, historyPrint=OFF, userSubroutine='',
    #         scratch='', resultsFormat=ODB, numThreadsPerMpiProcess=1,
    #         multiprocessingMode=DEFAULT, numCpus=1, numGPUs=0)
    #
    # mdb.jobs['Job-1'].writeInput(consistencyChecking=OFF)
