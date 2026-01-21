# -*- coding: utf-8 -*-
"""

"""
import json
import math

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

    ABAQUS_ENV = True
except ImportError as e:
    print(e)
    ABAQUS_ENV = False


class Line2D:
    """2D空间直线类"""

    def __init__(self, *args):
        """
        初始化直线
        支持四种方式：
        1. 一般式方程系数: (A, B, C) 表示 Ax + By + C = 0
        2. 点斜式: (point, slope) 表示过点point，斜率为slope
        3. 两点式: [(x1,y1), (x2,y2)]
        4. 斜截式: (slope, intercept) 表示 y = slope*x + intercept
        5. 点+方向向量: (point, direction) 适用于垂直线等情况
        """
        if len(args) == 3:
            # 一般式方程系数: (A, B, C)
            self.A, self.B, self.C = args
            # 确保至少一个系数不为零
            if abs(self.A) < 1e-10 and abs(self.B) < 1e-10:
                raise ValueError('A和B不能同时为零')

        elif len(args) == 2:
            arg1, arg2 = args[0], args[1]

            if isinstance(arg1, (int, float)) and isinstance(arg2, (int, float)):
                # 斜截式: (slope, intercept)
                slope, intercept = arg1, arg2
                # y = slope*x + intercept  =>  slope*x - y + intercept = 0
                self.A = slope
                self.B = -1
                self.C = intercept

            elif (isinstance(arg1, (tuple, list, np.ndarray)) and
                  isinstance(arg2, (int, float))):
                # 点斜式: (point, slope)
                point, slope = np.array(arg1, dtype=float), arg2
                # y - y1 = slope*(x - x1)  =>  slope*x - y + (y1 - slope*x1) = 0
                x1, y1 = point[0], point[1]
                self.A = slope
                self.B = -1
                self.C = y1 - slope * x1

            elif (isinstance(arg1, (tuple, list, np.ndarray)) and
                  isinstance(arg2, (tuple, list, np.ndarray))):
                # 两点式或点+方向向量
                p1, p2 = np.array(arg1, dtype=float), np.array(arg2, dtype=float)

                if len(p1) == 2 and len(p2) == 2:
                    # 两点式
                    if np.allclose(p1, p2):
                        raise ValueError('两个点不能相同')

                    # 计算直线方程: (y2-y1)x + (x1-x2)y + (x2*y1 - x1*y2) = 0
                    self.A = p2[1] - p1[1]  # y2 - y1
                    self.B = p1[0] - p2[0]  # x1 - x2
                    self.C = p2[0] * p1[1] - p1[0] * p2[1]  # x2*y1 - x1*y2
                else:
                    raise ValueError('点和方向向量都必须是二维坐标')
            else:
                raise ValueError('参数格式错误')
        else:
            raise ValueError('请输入正确的参数格式')

        # 标准化方程系数（可选）
        self._normalize_coefficients()

    def _normalize_coefficients(self):
        """标准化方程系数，使A² + B² = 1"""
        norm = np.sqrt(self.A ** 2 + self.B ** 2)
        if norm > 0:
            self.A /= norm
            self.B /= norm
            self.C /= norm

    @classmethod
    def from_two_points(cls, p1, p2):
        """
        从两点创建直线
        p1: 第一个点
        p2: 第二个点
        """
        return cls(p1, p2)

    @classmethod
    def from_point_slope(cls, point, slope):
        """
        从点和斜率创建直线
        point: 点坐标
        slope: 斜率
        """
        return cls(point, slope)

    @classmethod
    def from_slope_intercept(cls, slope, intercept):
        """
        从斜率和截距创建直线
        slope: 斜率
        intercept: y轴截距
        """
        return cls(slope, intercept)

    def distance_to_point(self, point):
        """
        计算点到直线的距离
        公式: d = |Ax + By + C| / √(A² + B²)
        """
        point = np.array(point, dtype=float)
        x, y = point[0], point[1]
        numerator = abs(self.A * x + self.B * y + self.C)
        denominator = np.sqrt(self.A ** 2 + self.B ** 2)
        return numerator / denominator if denominator != 0 else float('inf')

    def distance_to_line(self, other_line):
        """
        计算两条直线之间的距离
        如果平行：返回任意一点到另一条直线的距离
        如果不平行：返回0（相交）
        """
        if self.is_parallel(other_line):
            # 平行直线间的距离：取self上一点到other_line的距离
            # 找一个点：如果B不为0，取x=0，则y=-C/B
            if abs(self.B) > 1e-10:
                point = (0, -self.C / self.B)
            else:
                point = (-self.C / self.A, 0)
            return other_line.distance_to_point(point)
        else:
            # 相交直线距离为0
            return 0.0

    def is_point_on_line(self, point, tolerance=1e-6):
        """判断点是否在直线上"""
        return self.distance_to_point(point) < tolerance

    def is_parallel(self, other_line, tolerance=1e-6):
        """判断两条直线是否平行"""
        # 在2D中，两条直线平行当且仅当法向量平行
        # 即 A1/B1 = A2/B2，但需考虑B为0的情况
        if abs(self.B) < tolerance:
            return abs(other_line.B) < tolerance

        if abs(other_line.B) < tolerance:
            return abs(self.B) < tolerance

        # 比较斜率
        return abs(self.slope - other_line.slope) < tolerance

    def is_perpendicular(self, other_line, tolerance=1e-6):
        """判断两条直线是否垂直"""
        # 两条直线垂直当且仅当它们的法向量垂直
        # 即 A1*A2 + B1*B2 = 0
        dot_product = self.A * other_line.A + self.B * other_line.B
        return abs(dot_product) < tolerance

    def angle_with_line(self, other_line):
        """计算两条直线的夹角（弧度）"""
        # 两条直线的夹角：cosθ = |A1*A2 + B1*B2| / (√(A1²+B1²) * √(A2²+B2²))
        numerator = abs(self.A * other_line.A + self.B * other_line.B)
        denominator = np.sqrt(self.A ** 2 + self.B ** 2) * np.sqrt(other_line.A ** 2 + other_line.B ** 2)

        if denominator < 1e-10:
            return float('nan')

        cos_theta = numerator / denominator
        cos_theta = np.clip(cos_theta, 0.0, 1.0)  # 避免浮点误差

        return np.arccos(cos_theta)

    @property
    def slope(self):
        """获取直线的斜率"""
        if abs(self.B) < 1e-10:
            # 垂直线，斜率不存在（返回无穷大）
            return float('inf') if self.A > 0 else -float('inf')
        return -self.A / self.B

    @property
    def intercept(self):
        """获取y轴截距"""
        if abs(self.B) < 1e-10:
            # 垂直线，没有y轴截距
            return float('nan')
        return -self.C / self.B

    @property
    def normal_vector(self):
        """获取法向量"""
        return np.array([self.A, self.B])

    @property
    def direction_vector(self):
        """获取方向向量"""
        # 方向向量与法向量垂直
        return np.array([-self.B, self.A])

    def get_intersection(self, other_line):
        """
        获取两条直线的交点
        返回交点坐标，如果平行则返回None
        """
        if self.is_parallel(other_line):
            return None

        # 解线性方程组
        # A1x + B1y + C1 = 0
        # A2x + B2y + C2 = 0

        # 使用克莱姆法则
        D = self.A * other_line.B - other_line.A * self.B

        if abs(D) < 1e-10:
            return None

        Dx = -self.C * other_line.B + other_line.C * self.B
        Dy = -self.A * other_line.C + other_line.A * self.C

        x = Dx / D
        y = Dy / D

        return np.array([x, y])

    def get_equation_general(self):
        """获取一般式方程字符串"""
        return '{:.4f}x + {:.4f}y + {:.4f} = 0'.format(self.A, self.B, self.C)

    def get_equation_slope_intercept(self):
        """获取斜截式方程字符串"""
        if abs(self.B) < 1e-10:
            # 垂直线
            x_intercept = -self.C / self.A
            return 'x = {:.4f}'.format(x_intercept)

        slope = self.slope
        intercept = self.intercept

        if abs(slope) < 1e-10:
            # 水平线
            return 'y = {:.4f}'.format(intercept)

        sign = '+' if intercept >= 0 else '-'
        return 'y = {:.4f}x {} {:.4f}'.format(slope, sign, abs(intercept))

    def get_perpendicular_line(self, point):
        """
        获取过给定点且垂直于当前直线的直线
        """
        point = np.array(point, dtype=float)
        # 新直线的法向量是当前直线的方向向量
        # 或者新直线的方向向量是当前直线的法向量

        # 新直线的法向量与当前直线相同，过点point
        # A(x - x0) + B(y - y0) = 0
        x0, y0 = point[0], point[1]
        A = self.A
        B = self.B
        C = -(A * x0 + B * y0)

        return Line2D(A, B, C)

    def get_parallel_line(self, point):
        """
        获取过给定点且平行于当前直线的直线
        """
        point = np.array(point, dtype=float)
        # 平行直线的法向量相同
        x0, y0 = point[0], point[1]
        A = self.A
        B = self.B
        C = -(A * x0 + B * y0)

        return Line2D(A, B, C)

    def project_point(self, point):
        """
        获取点在直线上的投影点
        """
        point = np.array(point, dtype=float)
        x0, y0 = point[0], point[1]

        # 投影点公式
        denominator = self.A ** 2 + self.B ** 2

        if denominator < 1e-10:
            return point  # 直线不正常，返回原点

        x_proj = (self.B * (self.B * x0 - self.A * y0) - self.A * self.C) / denominator
        y_proj = (self.A * (-self.B * x0 + self.A * y0) - self.B * self.C) / denominator

        return np.array([x_proj, y_proj])

    def __repr__(self):
        """字符串表示"""
        return "Line2D(A={:.4f}, B={:.4f}, C={:.4f})".format(self.A, self.B, self.C)


class Plane:
    """平面类"""

    def __init__(self, *args):
        """
        初始化平面
        支持两种方式：
        1. 平面方程系数: (A, B, C, D)
        2. 三个点: [(x1,y1,z1), (x2,y2,z2), (x3,y3,z3)]
        """
        if len(args) == 4:
            # 平面方程系数
            self.A, self.B, self.C, self.D = args
        elif len(args) == 3:
            # 三个点
            self._from_three_points(args[0], args[1], args[2])
        elif len(args) == 2:
            # 点+法向量
            self._from_point_and_normal(args[0], args[1])
        else:
            raise ValueError('请输入平面方程系数(A,B,C,D)或三个点')

    def _from_three_points(self, p1, p2, p3):
        """从三个点计算平面方程"""
        v1 = np.array(p2) - np.array(p1)
        v2 = np.array(p3) - np.array(p1)
        normal = np.cross(v1, v2)

        self.A, self.B, self.C = normal
        self.D = -np.dot(normal, p1)
        self.normalize()

    def _from_point_and_normal(self, point, normal_vector):
        """从点和法向量计算平面方程"""
        self.A, self.B, self.C = normal_vector
        # D = - (A*x0 + B*y0 + C*z0)
        self.D = -(self.A * point[0] + self.B * point[1] + self.C * point[2])
        self.normalize()

    def normalize(self):
        """归一化平面方程，使法向量为单位向量"""
        norm = np.sqrt(self.A ** 2 + self.B ** 2 + self.C ** 2)
        if norm > 0:
            self.A /= norm
            self.B /= norm
            self.C /= norm
            self.D /= norm

    def distance_to_point(self, point):
        """计算点到平面的距离"""
        x, y, z = point[0], point[1], point[2]
        numerator = abs(self.A * x + self.B * y + self.C * z + self.D)
        denominator = np.sqrt(self.A ** 2 + self.B ** 2 + self.C ** 2)
        return numerator / denominator if denominator != 0 else float('inf')

    def is_point_on_plane(self, point, tolerance=1e-6):
        """判断点是否在平面上"""
        return self.distance_to_point(point) < tolerance

    def get_equation(self):
        """获取平面方程字符串"""
        return '%sx + %sy + %sz + %s = 0' % (self.A, self.B, self.C, self.D)

    def project_point(self, point):
        """投影点到平面上"""
        x, y, z = point
        d = self.A * x + self.B * y + self.C * z + self.D
        return [
            x - self.A * d,
            y - self.B * d,
            z - self.C * d
        ]

    def get_normal(self):
        """获取单位法向量"""
        return np.array([self.A, self.B, self.C])

    def intersection_with_circle(self, circle, tolerance=1e-6):
        """
        计算平面与圆形曲线的交点

        参数:
            circle: Circle对象，圆形曲线
            tolerance: 容差

        返回:
            交点列表，可能包含0、1或2个点，或者无穷多个点（圆在平面上）
        """
        # 1. 检查圆所在平面与当前平面的关系
        circle_plane = circle.plane
        plane_intersection = self._plane_intersection(circle_plane, tolerance)

        if plane_intersection is None:
            # 两平面平行或重合
            if self._are_planes_parallel(circle_plane, tolerance):
                # 检查是否重合
                if self._are_planes_coincident(circle_plane, tolerance):
                    # 圆在平面上，需要检查圆是否在当前平面上
                    if self.is_point_on_plane(circle.center, tolerance):
                        # 圆完全在当前平面上，返回无穷多个点
                        return "infinite"  # 或返回圆的参数方程
                    else:
                        # 两平面重合但圆不在当前平面上（可能偏移）
                        return []
                else:
                    # 两平面平行但不重合，无交点
                    return []

        # 2. 两平面相交于一条直线
        line_point, line_direction = plane_intersection

        # 3. 计算直线与圆的交点（在圆所在平面内）
        intersections = self._line_circle_intersection_in_plane(
            line_point, line_direction, circle, circle_plane, tolerance
        )

        return intersections

    def _plane_intersection(self, other_plane, tolerance=1e-6):
        """
        计算两平面交线

        返回:
            (point, direction) 或 None（如果平面平行）
        """
        # 检查两平面是否平行
        if self._are_planes_parallel(other_plane, tolerance):
            return None

        # 计算交线方向（两平面法向量的叉积）
        n1 = np.array([self.A, self.B, self.C])
        n2 = np.array([other_plane.A, other_plane.B, other_plane.C])
        direction = np.cross(n1, n2)
        direction = direction / np.linalg.norm(direction)  # 归一化

        # 找一个同时满足两个平面方程的点
        # 解方程组：n1·p + d1 = 0, n2·p + d2 = 0
        # 固定一个变量（如z=0），解另外两个变量
        A = np.array([
            [self.A, self.B],
            [other_plane.A, other_plane.B]
        ])

        # 检查矩阵是否可逆
        if abs(np.linalg.det(A)) > tolerance:
            b = np.array([-self.D, -other_plane.D])
            xy = np.linalg.solve(A, b)
            point = np.array([xy[0], xy[1], 0])
        else:
            # 尝试固定y=0
            A = np.array([
                [self.A, self.C],
                [other_plane.A, other_plane.C]
            ])
            if abs(np.linalg.det(A)) > tolerance:
                b = np.array([-self.D, -other_plane.D])
                xz = np.linalg.solve(A, b)
                point = np.array([xz[0], 0, xz[1]])
            else:
                # 固定x=0
                A = np.array([
                    [self.B, self.C],
                    [other_plane.B, other_plane.C]
                ])
                b = np.array([-self.D, -other_plane.D])
                yz = np.linalg.solve(A, b)
                point = np.array([0, yz[0], yz[1]])

        return point, direction

    def _are_planes_parallel(self, other_plane, tolerance=1e-6):
        """判断两平面是否平行"""
        n1 = np.array([self.A, self.B, self.C])
        n2 = np.array([other_plane.A, other_plane.B, other_plane.C])

        # 检查法向量是否平行
        cross = np.cross(n1, n2)
        return np.linalg.norm(cross) < tolerance

    def _are_planes_coincident(self, other_plane, tolerance=1e-6):
        """判断两平面是否重合"""
        if not self._are_planes_parallel(other_plane, tolerance):
            return False

        # 检查原点距离是否相同
        dist1 = self.distance_to_point([0, 0, 0])
        dist2 = other_plane.distance_to_point([0, 0, 0])

        return abs(dist1 - dist2) < tolerance

    def _line_circle_intersection_in_plane(self, line_point, line_direction,
                                           circle, circle_plane, tolerance=1e-6):
        """
        在圆所在平面内计算直线与圆的交点

        参数:
            line_point: 直线上的点
            line_direction: 直线方向向量
            circle: 圆对象
            circle_plane: 圆所在平面

        返回:
            交点列表
        """
        # 1. 将问题转换到圆所在平面的二维坐标系
        # 找到圆所在平面的两个基向量
        normal = circle_plane.get_normal()

        # 找一个与法向量不平行的基础向量
        if abs(normal[0]) > tolerance or abs(normal[1]) > tolerance:
            basis1 = np.array([-normal[1], normal[0], 0])
        else:
            basis1 = np.array([1, 0, 0])
        basis1 = basis1 / np.linalg.norm(basis1)

        # 第二个基向量
        basis2 = np.cross(normal, basis1)
        basis2 = basis2 / np.linalg.norm(basis2)

        # 2. 将直线上的点、方向向量和圆心转换到二维坐标系
        # 以圆心为原点
        center_3d = circle.center

        def to_2d(point_3d):
            """将三维点转换到二维平面坐标系"""
            vec = point_3d - center_3d
            x = np.dot(vec, basis1)
            y = np.dot(vec, basis2)
            return np.array([x, y])

        # 直线参数方程: p = line_point + t * line_direction
        p0_2d = to_2d(line_point)
        v_2d = to_2d(line_point + line_direction) - p0_2d

        # 归一化v_2d
        v_norm = np.linalg.norm(v_2d)
        if v_norm < tolerance:
            # 直线方向在平面上投影为零，直线垂直于圆所在平面
            # 检查线点是否在圆上
            p0_3d = line_point
            dist = np.linalg.norm(p0_3d - center_3d)
            if abs(dist - circle.radius) < tolerance:
                return [p0_3d.tolist()]
            else:
                return []

        v_2d = v_2d / v_norm

        # 3. 在二维坐标系中解直线与圆的交点
        # 直线方程: p = p0 + t*v
        # 圆方程: |p|² = r²
        # 代入: |p0 + t*v|² = r²
        # 展开: (p0·p0) + 2t(p0·v) + t²(v·v) = r²
        # 因为v是单位向量: t² + 2(p0·v)t + (|p0|² - r²) = 0

        a = 1.0  # v·v = 1 (单位向量)
        b = 2.0 * np.dot(p0_2d, v_2d)
        c = np.dot(p0_2d, p0_2d) - circle.radius ** 2

        # 判别式
        discriminant = b ** 2 - 4 * a * c

        if discriminant < -tolerance:
            # 无实数解
            return []

        if abs(discriminant) < tolerance:
            # 一个解（相切）
            t = -b / (2 * a)
            p_2d = p0_2d + t * v_2d
            # 转换回三维坐标
            p_3d = center_3d + p_2d[0] * basis1 + p_2d[1] * basis2
            # 验证点在直线上（考虑数值误差）
            return [p_3d.tolist()]
        else:
            # 两个解
            sqrt_disc = math.sqrt(discriminant)
            t1 = (-b + sqrt_disc) / (2 * a)
            t2 = (-b - sqrt_disc) / (2 * a)

            p1_2d = p0_2d + t1 * v_2d
            p2_2d = p0_2d + t2 * v_2d

            # 转换回三维坐标
            p1_3d = center_3d + p1_2d[0] * basis1 + p1_2d[1] * basis2
            p2_3d = center_3d + p2_2d[0] * basis1 + p2_2d[1] * basis2

            # 验证两个点都在直线上（考虑数值误差）
            # 计算参数t对应的三维点，验证是否在直线上
            return [p1_3d.tolist(), p2_3d.tolist()]


class Circle3D:
    """三维空间中的圆形曲线类"""

    def __init__(self, center, radius, plane):
        """
        初始化圆形曲线

        参数:
            center: 圆心坐标 [x, y, z]
            radius: 半径
            plane: 圆所在平面（Plane对象）
        """
        self.center = np.array(center)
        self.radius = radius
        self.plane = plane

        # 验证圆心在平面上
        if not plane.is_point_on_plane(self.center):
            raise ValueError("圆心不在指定的平面上")

    def is_point_on_circle(self, point, tolerance=1e-6):
        """判断点是否在圆上"""
        # 1. 点必须在圆所在平面上
        if not self.plane.is_point_on_plane(point, tolerance):
            return False

        # 2. 点到圆心的距离等于半径
        dist = np.linalg.norm(np.array(point) - self.center)
        return abs(dist - self.radius) < tolerance

    def get_equation_description(self):
        """获取圆的描述"""
        return "Center: {0}, Radius: {1}, Plane: {2}".format(self.center, self.radius, self.plane.get_equation())


class Cylinder:
    """圆柱面类"""

    def __init__(self, *args):
        """
        初始化圆柱面
        支持两种方式：
        1. 轴线点和方向: (axis_point, axis_direction, radius)
        2. 两端面中心点: (center1, center2, radius)
        """
        if len(args) == 3:
            if isinstance(args[0], tuple) and isinstance(args[1], tuple):
                if len(args[0]) == 3 and len(args[1]) == 3:
                    # 轴线点和方向
                    self.axis_point = np.array(args[0])
                    self.axis_direction = np.array(args[1])
                    self.radius = args[2]
                else:
                    # 两端面中心点
                    self._from_two_centers(args[0], args[1], args[2])
            else:
                raise ValueError("参数格式错误")
        else:
            raise ValueError("请输入轴线点和方向或两端面中心点")

        # 标准化方向向量
        self.axis_unit = self.axis_direction / np.linalg.norm(self.axis_direction)

    def _from_two_centers(self, center1, center2, radius):
        """从两端面中心点计算圆柱面参数"""
        self.axis_point = np.array(center1)
        self.axis_direction = np.array(center2) - np.array(center1)
        self.radius = radius

    def distance_to_surface(self, point):
        """计算点到圆柱面的距离"""
        p = np.array(point)

        # 向量从轴线上点到目标点
        p_to_axis = p - self.axis_point

        # 计算在轴线方向上的投影长度
        projection_length = np.dot(p_to_axis, self.axis_unit)

        # 计算投影点坐标
        projection_point = self.axis_point + projection_length * self.axis_unit

        # 计算点到轴线的垂直距离
        distance_to_axis = np.linalg.norm(p - projection_point)

        # 点到圆柱面的距离
        return abs(distance_to_axis - self.radius)

    def is_point_on_cylinder(self, point, tolerance=1e-6):
        """判断点是否在圆柱面上"""
        return self.distance_to_surface(point) < tolerance

    def get_parameters(self):
        """获取圆柱面参数"""
        return {
            'axis_point': tuple(self.axis_point),
            'axis_direction': tuple(self.axis_direction),
            'radius': self.radius
        }


def load_json(file_path, encoding='utf-8'):
    """
    Read JSON data from file.
    """
    with open(file_path, 'r') as f:
        return json.load(f)


def degrees_to_radians(degrees):
    """
    将度数转换为弧度
    参数: degrees - 角度值（度数）
    返回: 对应的弧度值
    """
    return degrees * math.pi / 180


def radians_to_degrees(radians):
    """
    将弧度转换为度数
    参数: radians - 弧度值
    返回: 对应的角度值（度数）
    """
    return radians * 180 / math.pi


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


def get_z_list(block_length, block_insulation_thickness, block_gap, block_number):
    z = []
    for i in range(block_number):
        z += (np.array([0.0, block_insulation_thickness, block_length - block_insulation_thickness, block_length]) + i * (block_length + block_gap)).tolist()
    return z


def line_circle_intersection(k, b, r):
    """
    计算直线 y = kx + b 与圆 x^2 + y^2 = r^2 的交点。

    参数:
        k: 直线斜率
        b: 直线截距
        r: 圆的半径

    返回:
        交点列表，每个交点为元组 (x, y)。如果没有交点返回空列表。
    """
    A = 1 + k ** 2
    B = 2 * k * b
    C = b ** 2 - r ** 2

    D = B ** 2 - 4 * A * C

    if D < 0:
        return []
    elif D == 0:
        x = -B / (2 * A)
        y = k * x + b
        return [(x, y)]
    else:
        sqrt_D = math.sqrt(D)
        x1 = (-B + sqrt_D) / (2 * A)
        x2 = (-B - sqrt_D) / (2 * A)
        y1 = k * x1 + b
        y2 = k * x2 + b
        return [(x1, y1), (x2, y2)]


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

    return x, y


def mirror_y_axis(point):
    """
    计算点关于 y 轴的镜像坐标
    """
    return [-point[0], point[1]]


def min_difference(target, numbers):
    numbers_array = np.array(numbers)
    differences = np.abs(numbers_array - target)
    return np.min(differences)


def calc_arc(center, start, end):
    """
    计算起点和终点相对于圆心的角度，并返回圆弧中点

    参数:
        center: 圆心坐标 (cx, cy)
        start: 起点坐标 (sx, sy)
        end: 终点坐标 (ex, ey)

    返回:
        theta1: 起始角度（度）
        theta2: 终止角度（度）
        radius: 半径
        mid_point: 圆弧中点坐标 (mx, my)
    """
    # 计算向量
    vec_start = (start[0] - center[0], start[1] - center[1])
    vec_end = (end[0] - center[0], end[1] - center[1])

    # 计算角度（弧度）
    angle_start = np.arctan2(vec_start[1], vec_start[0])
    angle_end = np.arctan2(vec_end[1], vec_end[0])

    # 转换为角度
    theta1 = np.degrees(angle_start)
    theta2 = np.degrees(angle_end)

    # 计算半径（假设起点和终点在同一圆上）
    radius_start = np.sqrt(vec_start[0] ** 2 + vec_start[1] ** 2)
    radius_end = np.sqrt(vec_end[0] ** 2 + vec_end[1] ** 2)
    radius = (radius_start + radius_end) / 2  # 取平均值

    # 计算圆弧中点
    # 使用角度平均值来计算中点
    mid_angle_rad = (angle_start + angle_end) / 2

    # 计算中点坐标
    mid_x = center[0] + radius * np.cos(mid_angle_rad)
    mid_y = center[1] + radius * np.sin(mid_angle_rad)
    mid_point = (mid_x, mid_y)

    return theta1, theta2, radius, mid_point


def solve_three_arcs(p0, theta0_deg, p3, theta3_deg, r1, r2, r3, tol=1e-6):
    """
    求解三段相切圆弧的几何参数。

    参数:
        p0: 起点坐标 (x0, y0)
        theta0_deg: 起点切线方向（角度制，从x轴逆时针测量）
        p3: 终点坐标 (x3, y3)
        theta3_deg: 终点切线方向（角度制）
        r1, r2, r3: 三个圆弧的半径（正数）
        tol: 数值容差

    返回:
        字典，包含以下键：
            's': 弯曲方向（1表示圆心在左侧，-1表示右侧）
            'c1', 'c2', 'c3': 圆心坐标
            'p1', 'p2': 中间切点坐标
            'arc1': (start_angle, end_angle) 弧1的起始角和终止角（弧度，相对于圆心）
            'arc2': (start_angle, end_angle)
            'arc3': (start_angle, end_angle)
            'delta1', 'delta2', 'delta3': 各圆弧的圆心角（弧度，带符号）
        若无解，返回None。
    """
    # 角度转换为弧度
    theta0 = math.radians(theta0_deg)
    theta3 = math.radians(theta3_deg)

    # 切线方向单位向量
    d0 = (math.cos(theta0), math.sin(theta0))
    d3 = (math.cos(theta3), math.sin(theta3))

    # 左手法向量（逆时针旋转90度）
    n0_perp = (-d0[1], d0[0])
    n3_perp = (-d3[1], d3[0])

    solutions = []
    for s in [1, -1]:  # s=1: 圆心在左侧（逆时针），s=-1: 圆心在右侧（顺时针）
        # 计算起点和终点的圆心
        c1 = (p0[0] + s * r1 * n0_perp[0], p0[1] + s * r1 * n0_perp[1])
        c3 = (p3[0] + s * r3 * n3_perp[0], p3[1] + s * r3 * n3_perp[1])

        # 相邻圆弧内切，圆心距为半径差
        d1 = abs(r1 - r2)
        d2 = abs(r2 - r3)

        # 求圆C1（半径d1）和圆C3（半径d2）的交点（候选C2）
        x1, y1 = c1
        x3, y3 = c3
        dx = x3 - x1
        dy = y3 - y1
        d = math.hypot(dx, dy)

        # 检查两圆是否相交
        if d > d1 + d2 + tol or d < abs(d1 - d2) - tol:
            continue
        if d < tol:  # 圆心重合，跳过
            continue

        # 计算交点参数
        a = (d1 * d1 - d2 * d2 + d * d) / (2 * d)
        h_sq = d1 * d1 - a * a
        if h_sq < -tol:
            continue
        if h_sq < 0:
            h_sq = 0
        h = math.sqrt(h_sq)

        # 中点
        xp = x1 + a * dx / d
        yp = y1 + a * dy / d

        # 垂直方向单位向量
        if abs(dy) < tol and abs(dx) > tol:
            vx, vy = 0, dx
        else:
            vx, vy = -dy, dx
        norm_v = math.hypot(vx, vy)
        if norm_v < tol:
            continue
        vx /= norm_v
        vy /= norm_v

        # 两个候选C2
        for sign in [1, -1]:
            c2 = (xp + sign * h * vx, yp + sign * h * vy)

            # 计算切点P1和P2（使用内切公式）
            if abs(r1 - r2) < tol or abs(r2 - r3) < tol:
                # 半径相等的情况需要特殊处理，此处跳过
                continue
            p1 = ((r1 * c2[0] - r2 * c1[0]) / (r1 - r2), (r1 * c2[1] - r2 * c1[1]) / (r1 - r2))
            p2 = ((r2 * c3[0] - r3 * c2[0]) / (r2 - r3), (r2 * c3[1] - r3 * c2[1]) / (r2 - r3))

            # 验证距离条件
            if (abs(math.hypot(p1[0] - c1[0], p1[1] - c1[1]) - r1) > tol or
                    abs(math.hypot(p1[0] - c2[0], p1[1] - c2[1]) - r2) > tol or
                    abs(math.hypot(p2[0] - c2[0], p2[1] - c2[1]) - r2) > tol or
                    abs(math.hypot(p2[0] - c3[0], p2[1] - c3[1]) - r3) > tol):
                continue

            # 计算各圆弧的圆心角
            def included_angle(center, start, end):
                v_start = (start[0] - center[0], start[1] - center[1])
                v_end = (end[0] - center[0], end[1] - center[1])
                ang_start = math.atan2(v_start[1], v_start[0])
                ang_end = math.atan2(v_end[1], v_end[0])
                delta = ang_end - ang_start
                # 归一化到 [-pi, pi]
                if delta > math.pi:
                    delta -= 2 * math.pi
                elif delta < -math.pi:
                    delta += 2 * math.pi
                return ang_start, ang_end, delta

            _, _, delta1 = included_angle(c1, p0, p1)
            _, _, delta2 = included_angle(c2, p1, p2)
            _, _, delta3 = included_angle(c3, p2, p3)

            print(s, delta1, delta2, delta3)

            def same_sign(a, b, c):
                """通过乘积判断三个数是否同号"""
                return (a * b > 0) and (b * c > 0)

            # 检查圆心角是否满足条件（绝对值小于90度，且符号一致）
            if not (0 < abs(delta1) < math.pi / 2 + tol and
                    0 < abs(delta2) < math.pi / 2 + tol and
                    0 < abs(delta3) < math.pi / 2 + tol):
                continue

            if not same_sign(delta1, delta2, delta3):
                continue

            # 计算各圆弧的起始角和终止角
            start1, end1, _ = included_angle(c1, p0, p1)
            start2, end2, _ = included_angle(c2, p1, p2)
            start3, end3, _ = included_angle(c3, p2, p3)

            # 存储解
            solutions.append({
                's': s,
                'c1': c1, 'c2': c2, 'c3': c3,
                'p1': p1, 'p2': p2,
                'arc1': (start1, end1),
                'arc2': (start2, end2),
                'arc3': (start3, end3),
                'delta1': delta1, 'delta2': delta2, 'delta3': delta3
            })

    if solutions:
        # 返回第一个解（通常只有一个可行解）
        return solutions[0]
    else:
        return None


def plot_three_arcs(result, p0, p3, figsize=(10, 8)):
    """
    绘制三段圆弧及其几何要素
    """
    if result is None:
        print('无解，无法绘制')
        return

    # 创建图形
    fig, ax = plt.subplots(figsize=figsize)

    # 提取数据
    c1, c2, c3 = result['c1'], result['c2'], result['c3']
    p1, p2 = result['p1'], result['p2']
    arc1_angles, arc2_angles, arc3_angles = result['arc1'], result['arc2'], result['arc3']
    r1 = math.hypot(p0[0] - c1[0], p0[1] - c1[1])
    r2 = math.hypot(p1[0] - c2[0], p1[1] - c2[1])
    r3 = math.hypot(p3[0] - c3[0], p3[1] - c3[1])

    # 绘制圆弧
    def draw_arc(ax, center, start_angle, end_angle, radius, color='blue', linewidth=2):
        # 确保角度顺序正确
        if result['s'] == -1 and start_angle < end_angle:
            start_angle, end_angle = end_angle, start_angle

        # 生成圆弧上的点
        angle_range = np.linspace(start_angle, end_angle, 100)
        x = center[0] + radius * np.cos(angle_range)
        y = center[1] + radius * np.sin(angle_range)
        ax.plot(x, y, color=color, linewidth=linewidth, label='Arc' if 'Arc' not in plt.gca().get_legend_handles_labels()[1] else '')

    # 绘制三段圆弧
    draw_arc(ax, c1, arc1_angles[0], arc1_angles[1], r1, color='blue')
    draw_arc(ax, c2, arc2_angles[0], arc2_angles[1], r2, color='green')
    draw_arc(ax, c3, arc3_angles[0], arc3_angles[1], r3, color='red')

    # 绘制圆心
    ax.plot(c1[0], c1[1], 'ro', markersize=8, label='Center c1')
    ax.plot(c2[0], c2[1], 'go', markersize=8, label='Center c2')
    ax.plot(c3[0], c3[1], 'bo', markersize=8, label='Center c3')

    # 绘制起点、终点和切点
    ax.plot(p0[0], p0[1], 'ks', markersize=10, label='Start p0')
    ax.plot(p3[0], p3[1], 'k^', markersize=10, label='End p3')
    ax.plot(p1[0], p1[1], 'mo', markersize=8, label='Tangent p1')
    ax.plot(p2[0], p2[1], 'co', markersize=8, label='Tangent p2')

    # 绘制圆心到切点的连线
    ax.plot([c1[0], p0[0]], [c1[1], p0[1]], 'r--', alpha=0.5)
    ax.plot([c1[0], p1[0]], [c1[1], p1[1]], 'r--', alpha=0.5)
    ax.plot([c2[0], p1[0]], [c2[1], p1[1]], 'g--', alpha=0.5)
    ax.plot([c2[0], p2[0]], [c2[1], p2[1]], 'g--', alpha=0.5)
    ax.plot([c3[0], p2[0]], [c3[1], p2[1]], 'b--', alpha=0.5)
    ax.plot([c3[0], p3[0]], [c3[1], p3[1]], 'b--', alpha=0.5)

    # 绘制圆心之间的连线
    ax.plot([c1[0], c2[0]], [c1[1], c2[1]], 'k:', alpha=0.5)
    ax.plot([c2[0], c3[0]], [c2[1], c3[1]], 'k:', alpha=0.5)

    # 设置图形属性
    ax.set_aspect('equal', adjustable='box')
    ax.grid(True, alpha=0.3)
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_title('Three Tangent Arcs Curve')

    # 添加文本标注
    def add_text_annotation(ax, point, text, offset=(0, 5)):
        ax.annotate(text, xy=point, xytext=offset, textcoords='offset points',
                    ha='center', va='bottom', fontsize=9, bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))

    add_text_annotation(ax, p0, 'p0({:.3f}, {:.3f})'.format(p0[0], p0[1]))
    add_text_annotation(ax, p3, 'p3({:.3f}, {:.3f})'.format(p3[0], p3[1]))
    add_text_annotation(ax, p1, 'p1({:.3f}, {:.3f})'.format(p1[0], p1[1]))
    add_text_annotation(ax, p2, 'p2({:.3f}, {:.3f})'.format(p2[0], p2[1]))
    add_text_annotation(ax, c1, 'c1(r={:.1f})'.format(r1), offset=(0, -10))
    add_text_annotation(ax, c2, 'c2(r={:.1f})'.format(r2), offset=(0, -10))
    add_text_annotation(ax, c3, 'c3(r={:.1f})'.format(r3), offset=(0, -10))

    # 添加圆弧角度信息
    ax.text(0.02, 0.98, 'Arc1 angle: {:.1f}°'.format(math.degrees(abs(result['delta1']))),
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightblue', alpha=0.8))
    ax.text(0.02, 0.94, 'Arc2 angle: {:.1f}°'.format(math.degrees(abs(result['delta2']))),
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.8))
    ax.text(0.02, 0.90, 'Arc3 angle: {:.1f}°'.format(math.degrees(abs(result['delta3']))),
            transform=ax.transAxes, fontsize=10, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='lightcoral', alpha=0.8))

    # 添加图例
    ax.legend(loc=0)

    # 自动调整坐标轴范围
    all_points = [p0, p3, c1, c2, c3, p1, p2]
    x_vals = [p[0] for p in all_points]
    y_vals = [p[1] for p in all_points]
    x_margin = max(0.1 * (max(x_vals) - min(x_vals)), 1)
    y_margin = max(0.1 * (max(y_vals) - min(y_vals)), 1)
    ax.set_xlim(min(x_vals) - x_margin, max(x_vals) + x_margin)
    ax.set_ylim(min(y_vals) - y_margin, max(y_vals) + y_margin)

    plt.tight_layout()
    plt.show()

    # 打印结果摘要
    print('=' * 50)
    print('三段圆弧曲线参数汇总:')
    print('=' * 50)
    print('弯曲方向: {}'.format('逆时针 (圆心在左侧)' if result['s'] == 1 else '顺时针 (圆心在右侧)'))
    print('半径: r1={:.3f}, r2={:.3f}, r3={:.3f}'.format(r1, r2, r3))
    print('圆心坐标:')
    print('  c1: ({:.3f}, {:.3f})'.format(c1[0], c1[1]))
    print('  c2: ({:.3f}, {:.3f})'.format(c2[0], c2[1]))
    print('  c3: ({:.3f}, {:.3f})'.format(c3[0], c3[1]))
    print('切点坐标:')
    print('  p1: ({:.3f}, {:.3f})'.format(p1[0], p1[1]))
    print('  p2: ({:.3f}, {:.3f})'.format(p2[0], p2[1]))
    print('圆心角:')
    print('  Δθ1: {:.2f}°'.format(math.degrees(result['delta1'])))
    print('  Δθ2: {:.2f}°'.format(math.degrees(result['delta2'])))
    print('  Δθ3: {:.2f}°'.format(math.degrees(result['delta3'])))
    print('=' * 50)


def geometries(d, x0, beta, rt, tt):
    nr = len(rt)
    nt = len(tt)

    r = [0.0 for _ in range(nr)]
    b = [0.0 for _ in range(nt)]

    for i in range(nr):
        r[i] = d / 2.0 - sum(rt[0:nr - i])

    for i in range(nt):
        b[i] = -sum(tt[0:nt - i]) / np.cos(beta)

    points = np.zeros([nr + 1, nt + 1, 2])

    k = np.tan(beta)

    # 遍历所有点
    for j in range(nt + 1):
        for i in range(nr + 1):
            if j == 0:  # 第一列
                if i == 0:  # 第一行，第一列
                    points[i, j] = np.array([x0, 0])
                else:  # 其他行，第一列
                    points[i, j] = np.array([r[i - 1], 0])
            else:  # 其他列
                if i == 0:  # 第一行，其他列
                    points[i, j] = np.array([x0, k * x0 + b[j - 1]])
                else:  # 其他行，其他列
                    points[i, j] = line_circle_intersection(k, b[j - 1], r[i - 1])[0]

    lines = {}
    center = (0, 0)
    for i in range(points.shape[0]):
        for j in range(points.shape[1]):
            point1 = points[i, j]
            if i - 1 > 0:
                point2 = points[i - 1, j]
                mid_point = 0.5 * (point1 + point2)
                lines['%s%s-%s%s' % (i, j, i - 1, j)] = ['line', point1, point2, mid_point]
            if i + 1 < points.shape[0]:
                point2 = points[i + 1, j]
                mid_point = 0.5 * (point1 + point2)
                lines['%s%s-%s%s' % (i, j, i + 1, j)] = ['line', point1, point2, mid_point]
            if j - 1 > 0:
                point2 = points[i, j - 1]
                if i == 0:
                    mid_point = 0.5 * (point1 + point2)
                    lines['%s%s-%s%s' % (i, j, i, j - 1)] = ['line', point1, point2, mid_point]
                else:
                    theta1, theta2, radius, mid_point = calc_arc(center, point2, point1)
                    lines['%s%s-%s%s' % (i, j, i, j - 1)] = ['arc', point1, point2, mid_point]
            if j + 1 < points.shape[1]:
                point2 = points[i, j + 1]
                if i == 0:
                    mid_point = 0.5 * (point1 + point2)
                    lines['%s%s-%s%s' % (i, j, i, j + 1)] = ['line', point1, point2, mid_point]
                else:
                    theta1, theta2, radius, mid_point = calc_arc(center, point1, point2)
                    lines['%s%s-%s%s' % (i, j, i, j + 1)] = ['arc', point1, point2, mid_point]

    faces = np.zeros([nr, nt, 2])
    for i in range(faces.shape[0]):
        for j in range(faces.shape[1]):
            point = (np.array(lines['%s%s-%s%s' % (i, j, i, j + 1)][3]) + np.array(lines['%s%s-%s%s' % (i + 1, j, i + 1, j + 1)][3])) / 2.0
            faces[i, j, 0] = point[0]
            faces[i, j, 1] = point[1]

    return points, lines, faces


def plot_geometries(points, lines, faces):
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    center = (0, 0)
    ax.plot(center[0], center[1], marker='o', markersize=8, color='black')

    for line_key, line_value in lines.items():
        line_type = line_value[0]
        point1 = line_value[1]
        point2 = line_value[2]
        mid_point = line_value[3]
        if line_type == 'line':
            ax.plot([point1[0], point2[0]], [point1[1], point2[1]], color='blue')
            ax.plot(mid_point[0], mid_point[1], marker='x', markersize=4, color='black')
        elif line_type == 'arc':
            theta1, theta2, radius, mid_point = calc_arc(center, point1, point2)
            arc = patches.Arc(center, width=2 * radius, height=2 * radius, angle=0, theta1=min(theta1, theta2), theta2=max(theta1, theta2), color='blue')
            ax.plot(mid_point[0], mid_point[1], marker='x', markersize=4, color='black')
            ax.add_patch(arc)

    # 为每个节点添加编号
    for i in range(points.shape[0]):
        for j in range(points.shape[1]):
            ax.annotate('({},{})'.format(i, j),
                        (points[i, j][0], points[i, j][1]),
                        textcoords="offset points",
                        xytext=(5, 5),  # 文本偏移量，避免与点重叠
                        ha='left',
                        fontsize=8,
                        color='red')

    ax.plot(points.reshape(-1, 2)[:, 0], points.reshape(-1, 2)[:, 1], ls='', marker='o', color='red')
    ax.plot(faces.reshape(-1, 2)[:, 0], faces.reshape(-1, 2)[:, 1], ls='', marker='s', color='green')
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    ax.set_aspect('equal')
    plt.show()


def create_sketch_block(model, sketch_name, points, index_r, index_t):
    s = model.ConstrainedSketch(name=sketch_name, sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s.Line(point1=points[0, 0], point2=points[index_r, 0]))
    geom_list.append(s.ArcByCenterEnds(center=center, point1=points[index_r, 0], point2=points[index_r, index_t], direction=COUNTERCLOCKWISE))
    geom_list.append(s.Line(point1=points[index_r, index_t], point2=points[0, index_t]))
    geom_list.append(s.Line(point1=points[0, index_t], point2=points[0, 0]))
    return s


def get_same_volume_cells(p, cells):
    cell_volumes = []
    for cell in cells:
        cell_volume = cell.getSize()
        cell_volumes.append(cell_volume)

    if cell_volumes != []:
        cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
        for cell_id in range(len(p.cells)):
            cell_size = p.cells[cell_id].getSize()
            if min_difference(cell_size, cell_volumes) < 1e-6:
                cells += p.cells[cell_id:cell_id + 1]
        return cells
    else:
        return None


def get_direction(delta):
    if delta > 0:
        return COUNTERCLOCKWISE
    else:
        return CLOCKWISE


def create_part_block_a(model, part_name, points, lines, faces, dimension):
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
    p.BaseSolidExtrude(sketch=s_block, depth=length / 2.0)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums

    # SKETCH-PATH
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=origin)
    s_path = model.ConstrainedSketch(name='SKETCH-PATH', sheetSize=4000, gridSpacing=100, transform=t)
    point1 = (0.0, x0)
    point2 = (length_up / 2.0, x0)
    point4 = (0.0, x0 + deep)
    slope = -math.tan(degrees_to_radians(angle_demolding_2))
    point3 = (slope * (point4[1] - point2[1]) + point2[0], point4[1])
    l1 = s_path.Line(point1=point1, point2=point2)
    l2 = s_path.Line(point1=point2, point2=point3)
    l3 = s_path.Line(point1=point3, point2=point4)
    l4 = s_path.Line(point1=point4, point2=point1)
    mid_point2_point3 = ((point2[0] + point3[0]) / 2.0, (point2[1] + point3[1]) / 2.0)
    mid_point3_point4 = ((point3[0] + point4[0]) / 2.0, (point3[1] + point4[1]) / 2.0)
    arc = s_path.FilletByRadius(radius=fillet_radius, curve1=l2, nearPoint1=mid_point2_point3, curve2=l3, nearPoint2=mid_point3_point4)

    # SKETCH-ELLIPSE
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=origin)
    s_ellipse = model.ConstrainedSketch(name='SKETCH-ELLIPSE', sheetSize=4000, gridSpacing=100, transform=t)
    s_ellipse.EllipseByCenterPerimeter(center=(0.0, x0 + deep), axisPoint1=(a, x0 + deep), axisPoint2=(0.0, x0 + deep + b))

    # Cut
    p.CutExtrude(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT,
                 sketch=s_path, depth=width / 2.0, flipExtrudeDirection=ON)
    p.CutSweep(pathPlane=d[xz_plane.id], pathUpEdge=d[x_axis.id], sketchPlane=d[xy_plane.id], sketchUpEdge=d[x_axis.id],
               pathOrientation=RIGHT, path=s_path, sketchOrientation=RIGHT, profile=s_ellipse, flipSweepDirection=ON)

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
    # index_r = 2, index_t = 2
    # line_keys = ['10-11', '11-12']
    # index_r = 3, index_t = 3
    # line_keys = ['10-11', '11-12', '12-13', '20-21', '21-22', '22-23']
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
    # index_r = 2, index_t = 2
    # line_keys = ['01-11', '11-21']
    # index_r = 3, index_t = 3
    # line_keys = ['01-11', '11-21', '21-31', '02-12', '12-22', '22-32']
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

    cut_edges = (
        p.edges.findAt((l2.pointOn[1], width / 2.0, l2.pointOn[0])),
        p.edges.findAt((l3.pointOn[1], width / 2.0, l3.pointOn[0])),
        p.edges.findAt((arc.pointOn[1], width / 2.0, arc.pointOn[0]))
    )
    p.PartitionCellByExtrudeEdge(line=d[y_axis.id], cells=p.cells, edges=cut_edges, sense=FORWARD)

    edge = p.edges.findAt((l3.pointOn[1], width / 2.0, l3.pointOn[0]))
    point = p.vertices.findAt((l3.getVertices()[0].coords[1], width / 2.0, l3.getVertices()[0].coords[0]))
    p.PartitionCellByPlaneNormalToEdge(edge=edge, point=point, cells=p.cells)

    edge = p.edges.findAt((l2.pointOn[1], width / 2.0, l2.pointOn[0]))
    point = p.vertices.findAt((l2.getVertices()[1].coords[1], width / 2.0, l2.getVertices()[1].coords[0]))
    p.PartitionCellByPlaneNormalToEdge(edge=edge, point=point, cells=p.cells.getByBoundingBox(0, 0, l3.pointOn[0], pen, pen, pen))

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

    # 根据Set中cells的体积，将镜像后同体积的cells归类到其对应的Set中
    for set_name in set_names:
        cells = p.sets[set_name].cells
        cell_volumes = []
        for cell in cells:
            cell_volume = cell.getSize()
            cell_volumes.append(cell_volume)
        cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
        for cell_id in range(len(p.cells)):
            cell_size = p.cells[cell_id].getSize()
            if min_difference(cell_size, cell_volumes) < tol:
                cells += p.cells[cell_id:cell_id + 1]
        p.Set(cells=cells, name=set_name)

    create_block_surface_common(p, points, dimension)

    p_faces = p.faces.getByBoundingBox(0, 0, 0, x0 + deep + b, width / 2.0, length_up / 2.0 + b / math.cos(degrees_to_radians(angle_demolding_2)))
    face_areas = []
    for face in p_faces:
        face_area = face.getSize()
        face_areas.append(face_area)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        face_size = p.faces[face_id].getSize()
        if min_difference(face_size, face_areas) < tol:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_front_a(model, part_name, points, lines, faces, dimension):
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
    p.BaseSolidExtrude(sketch=s_block, depth=length / 2.0)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums

    # SKETCH-PATH
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=origin)
    s_path = model.ConstrainedSketch(name='SKETCH-PATH', sheetSize=4000, gridSpacing=100, transform=t)
    point1 = (0.0, x0)
    point2 = (length_up / 2.0, x0)
    point4 = (0.0, x0 + deep)
    slope = -math.tan(degrees_to_radians(angle_demolding_2))
    point3 = (slope * (point4[1] - point2[1]) + point2[0], point4[1])
    l1 = s_path.Line(point1=point1, point2=point2)
    l2 = s_path.Line(point1=point2, point2=point3)
    l3 = s_path.Line(point1=point3, point2=point4)
    l4 = s_path.Line(point1=point4, point2=point1)
    mid_point2_point3 = ((point2[0] + point3[0]) / 2.0, (point2[1] + point3[1]) / 2.0)
    mid_point3_point4 = ((point3[0] + point4[0]) / 2.0, (point3[1] + point4[1]) / 2.0)
    arc = s_path.FilletByRadius(radius=fillet_radius, curve1=l2, nearPoint1=mid_point2_point3, curve2=l3, nearPoint2=mid_point3_point4)

    # SKETCH-ELLIPSE
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=origin)
    s_ellipse = model.ConstrainedSketch(name='SKETCH-ELLIPSE', sheetSize=4000, gridSpacing=100, transform=t)
    s_ellipse.EllipseByCenterPerimeter(center=(0.0, x0 + deep), axisPoint1=(a, x0 + deep), axisPoint2=(0.0, x0 + deep + b))

    # Cut
    p.CutExtrude(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT,
                 sketch=s_path, depth=width / 2.0, flipExtrudeDirection=ON)
    p.CutSweep(pathPlane=d[xz_plane.id], pathUpEdge=d[x_axis.id], sketchPlane=d[xy_plane.id], sketchUpEdge=d[x_axis.id],
               pathOrientation=RIGHT, path=s_path, sketchOrientation=RIGHT, profile=s_ellipse, flipSweepDirection=ON)

    # SKETCH-BLOCK-PARTITION
    s_block_partition = model.ConstrainedSketch(name='SKETCH-BLOCK-PARTITION', sheetSize=200.0)
    center = (0, 0)
    geom_list = []
    geom_list.append(s_block_partition.Line(point1=points[0, 1], point2=points[2, 1]))
    geom_list.append(s_block_partition.ArcByCenterEnds(center=center, point1=points[1, 0], point2=points[1, 2], direction=COUNTERCLOCKWISE))

    # Partition
    faces = p.faces.getByBoundingBox(0, 0, 0, pen, pen, tol)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=faces, sketchOrientation=BOTTOM, sketch=s_block_partition)

    # partition_edges = []
    # line_keys = ['10-11', '11-12']
    # for line_key in line_keys:
    #     line_middle_point = lines[line_key][3]
    #     x, y = line_middle_point
    #     edge_sequence = p.edges.findAt(((x, y, 0),))
    #     if len(edge_sequence) > 0:
    #         partition_edges.append(edge_sequence[0])
    # p.PartitionCellByExtrudeEdge(line=p.datums[z_axis.id], cells=p.cells, edges=partition_edges, sense=FORWARD)
    #
    # partition_edges = []
    # line_keys = ['01-11', '11-21']
    # for line_key in line_keys:
    #     line_middle_point = lines[line_key][3]
    #     x, y = line_middle_point
    #     edge_sequence = p.edges.findAt(((x, y, 0),))
    #     if len(edge_sequence) > 0:
    #         partition_edges.append(edge_sequence[0])
    # p.PartitionCellByExtrudeEdge(line=p.datums[z_axis.id], cells=p.cells, edges=partition_edges, sense=FORWARD)

    cut_edges = (
        p.edges.findAt((l2.pointOn[1], width / 2.0, l2.pointOn[0])),
        p.edges.findAt((l3.pointOn[1], width / 2.0, l3.pointOn[0])),
        p.edges.findAt((arc.pointOn[1], width / 2.0, arc.pointOn[0]))
    )
    p.PartitionCellByExtrudeEdge(line=d[y_axis.id], cells=p.cells, edges=cut_edges, sense=FORWARD)

    edge = p.edges.findAt((l3.pointOn[1], width / 2.0, l3.pointOn[0]))
    point = p.vertices.findAt((l3.getVertices()[0].coords[1], width / 2.0, l3.getVertices()[0].coords[0]))
    p.PartitionCellByPlaneNormalToEdge(edge=edge, point=point, cells=p.cells)

    edge = p.edges.findAt((l2.pointOn[1], width / 2.0, l2.pointOn[0]))
    point = p.vertices.findAt((l2.getVertices()[1].coords[1], width / 2.0, l2.getVertices()[1].coords[0]))
    p.PartitionCellByPlaneNormalToEdge(edge=edge, point=point, cells=p.cells.getByBoundingBox(0, 0, l3.pointOn[0], pen, pen, pen))

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

    xy_plane_z1 = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=z_list[1])

    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, z_list[1]))
    s_block_extrude = model.ConstrainedSketch(name='SKETCH-BLOCK-EXTRUDE', sheetSize=4000, gridSpacing=100, transform=t)
    s_block_extrude.retrieveSketch(sketch=s_block)
    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_block_extrude, depth=1000.0, flipExtrudeDirection=OFF)
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z1.id], cells=p.cells)

    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_block_cut_revolve = model.ConstrainedSketch(name='SKETCH-BLOCK-CUT-REVOLVE', sheetSize=200.0, transform=t)
    p0 = (1600, 700)
    theta0_deg = -90
    p3 = (640, 1764.5)
    theta3_deg = 0.0
    r1, r2, r3 = 600, 1600, 800

    result = solve_three_arcs(p0, theta0_deg, p3, theta3_deg, r1, r2, r3)

    p1 = result['p1']
    p2 = result['p2']
    c1 = result['c1']
    c2 = result['c2']
    c3 = result['c3']
    delta1 = result['delta1']
    delta2 = result['delta2']
    delta3 = result['delta3']

    def get_direction(delta):
        if delta > 0:
            return COUNTERCLOCKWISE
        else:
            return CLOCKWISE

    s_block_cut_revolve.ArcByCenterEnds(center=c1, point1=p0, point2=p1, direction=get_direction(delta1))
    s_block_cut_revolve.ArcByCenterEnds(center=c2, point1=p1, point2=p2, direction=get_direction(delta2))
    s_block_cut_revolve.ArcByCenterEnds(center=c3, point1=p2, point2=p3, direction=get_direction(delta3))
    s_block_cut_revolve.Line(point1=p0, point2=(p0[0], 1))
    s_block_cut_revolve.Line(point1=(p0[0], 1), point2=(pen, 1))
    s_block_cut_revolve.Line(point1=(pen, 1), point2=(pen, pen))
    s_block_cut_revolve.Line(point1=(pen, pen), point2=(p3[0], pen))
    s_block_cut_revolve.Line(point1=(p3[0], pen), point2=p3)
    center_line = s_block_cut_revolve.ConstructionLine(point1=(0.0, 0.0), point2=(1000.0, 0.0))
    s_block_cut_revolve.assignCenterline(line=center_line)

    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_block_cut_revolve, angle=360.0,
                 flipRevolveDirection=ON)

    create_block_surface_common(p, points, dimension)

    p_faces = p.faces.getByBoundingBox(0, 0, 0, x0 + deep + b, width / 2.0, length_up / 2.0 + b / math.cos(degrees_to_radians(angle_demolding_2)))
    face_areas = []
    for face in p_faces:
        face_area = face.getSize()
        face_areas.append(face_area)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        face_size = p.faces[face_id].getSize()
        if min_difference(face_size, face_areas) < tol:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

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
    origin = (0.0, 0.0, 0.0)
    length = z_list[-1] * 2.0
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
    t = p.MakeSketchTransform(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id],
                              sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, length / 2.0))
    s_gap_t = model.ConstrainedSketch(name='SKETCH-GAP-T', sheetSize=4000.0, gridSpacing=100.0, transform=t)
    center = (0, 0)
    geom_list = []
    geom_list.append(s_gap_t.Line(point1=points[0, 0], point2=points[2, 0]))
    geom_list.append(s_gap_t.ArcByCenterEnds(center=center, point1=points[2, 0], point2=points[2, 3], direction=COUNTERCLOCKWISE))
    geom_list.append(s_gap_t.Line(point1=points[2, 3], point2=points[0, 3]))
    geom_list.append(s_gap_t.Line(point1=points[0, 3], point2=points[0, 0]))
    p.SolidExtrude(sketchPlane=d[xy_plane_z1.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1,
                   sketchOrientation=RIGHT, sketch=s_gap_t, depth=(z_list[4] - z_list[3]) / 2.0, flipExtrudeDirection=OFF)

    # Partition
    p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_z1.id], cells=p.cells)
    cut_edges = (
        p.edges.findAt((lines['02-12'][3][0], lines['02-12'][3][1], length / 2.0)),
    )
    p.PartitionCellByExtrudeEdge(line=d[z_axis.id], cells=p.cells, edges=cut_edges, sense=FORWARD)

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

    p1 = (points[0, 0][0], points[0, 0][1], z_list[3] / 2.0)
    p2 = (points[0, 1][0], points[0, 1][1], z_list[3] / 2.0)
    p3 = (points[1, 0][0], points[1, 0][1], z_list[3] / 2.0)
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-Z1')

    p1 = (points[0, 0][0], points[0, 0][1], z_list[4] / 2.0)
    p2 = (points[0, 1][0], points[0, 1][1], z_list[4] / 2.0)
    p3 = (points[1, 0][0], points[1, 0][1], z_list[4] / 2.0)
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-Z2')

    p1 = (points[0, 0][0], points[0, 0][1], -z_list[3] / 2.0)
    p2 = (points[0, 1][0], points[0, 1][1], -z_list[3] / 2.0)
    p3 = (points[1, 0][0], points[1, 0][1], -z_list[3] / 2.0)
    plane = Plane(p1, p2, p3)
    faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        if plane.is_point_on_plane(p.faces[face_id].pointOn[0]) and len(p.faces[face_id].getCells()) == 1:
            faces += p.faces[face_id:face_id + 1]
    if faces:
        p.Surface(side1Faces=faces, name='SURFACE-Z-1')

    p1 = (points[0, 0][0], points[0, 0][1], -z_list[4] / 2.0)
    p2 = (points[0, 1][0], points[0, 1][1], -z_list[4] / 2.0)
    p3 = (points[1, 0][0], points[1, 0][1], -z_list[4] / 2.0)
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
        p.Surface(side1Faces=faces, name='SURFACE-R1')

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_b(model, part_name, points, lines, faces, dimension):
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
    p.BaseSolidExtrude(sketch=s_block, depth=length / 2.0)
    xy_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XYPLANE, offset=0.0)
    yz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=0.0)
    xz_plane = p.DatumPlaneByPrincipalPlane(principalPlane=XZPLANE, offset=0.0)
    x_axis = p.DatumAxisByPrincipalAxis(principalAxis=XAXIS)
    y_axis = p.DatumAxisByPrincipalAxis(principalAxis=YAXIS)
    z_axis = p.DatumAxisByPrincipalAxis(principalAxis=ZAXIS)
    d = p.datums

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
    s_cut = model.ConstrainedSketch(name='SKETCH-CUT', sheetSize=200.0)
    x1 = 400.0
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
    face_areas = []
    for face in p_faces:
        face_area = face.getSize()
        face_areas.append(face_area)
    p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for face_id in range(len(p.faces)):
        face_size = p.faces[face_id].getSize()
        if min_difference(face_size, face_areas) < tol:
            p_faces += p.faces[face_id:face_id + 1]
    if p_faces:
        p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

    # Partition
    p1 = [x0 + deep, -a]
    offset = p1[0] * np.cos(degrees_to_radians(180.0 / n)) - p1[1] * np.sin(degrees_to_radians(180.0 / n))
    yz_plane_2 = p.DatumPlaneByPrincipalPlane(principalPlane=YZPLANE, offset=offset)
    p.PartitionCellByDatumPlane(datumPlane=d[yz_plane_2.id], cells=p.cells)

    p.setValues(geometryRefinement=EXTRA_FINE)

    return p


def create_part_block_front_b(model, part_name, points, lines, faces, dimension):
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

    r_front = 460.0
    length_front = 1500.0

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
    s_block_cut_revolve = model.ConstrainedSketch(name='SKETCH-BLOCK-CUT-REVOLVE', sheetSize=4000.0, transform=t)
    p0 = (-1207.5, 794)
    theta0_deg = 90
    p3 = (-350, 1762.5)
    theta3_deg = 0.0
    r1, r2, r3 = 929.4, 1524, 655.2
    theta_in_deg = 0.16

    result = solve_three_arcs(p0, theta0_deg, p3, theta3_deg, r1, r2, r3)
    l1 = Line2D(p3, np.tan(degrees_to_radians(theta_in_deg)))
    l2 = Line2D((z_list[-1], 0.0), (z_list[-1], 1.0))
    p4 = l1.get_intersection(l2)

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
    s_block_cut_revolve.Line(point1=(-pen, pen), point2=(p4[0], pen))
    s_block_cut_revolve.Line(point1=(p4[0], pen), point2=p4)
    s_block_cut_revolve.Line(point1=p3, point2=p4)
    center_line = s_block_cut_revolve.ConstructionLine(point1=(0.0, 0.0), point2=(pen, 0.0))
    s_block_cut_revolve.assignCenterline(line=center_line)

    p.CutRevolve(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_block_cut_revolve, angle=360.0, flipRevolveDirection=ON)

    # 草图切割环向面
    t = p.MakeSketchTransform(sketchPlane=d[xz_plane.id], sketchUpEdge=d[x_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, origin=(0.0, 0.0, 0.0))
    s_block_cut_revolve_shift = model.ConstrainedSketch(name='SKETCH-BLOCK-CUT-REVOLVE-SHIFT', sheetSize=4000.0, transform=t)
    geom_list = []
    geom_list.append(s_block_cut_revolve_shift.Line(point1=(p0[0], x0), point2=p0))
    geom_list.append(s_block_cut_revolve_shift.ArcByCenterEnds(center=c1, point1=p0, point2=p1, direction=get_direction(delta1)))
    geom_list.append(s_block_cut_revolve_shift.ArcByCenterEnds(center=c2, point1=p1, point2=p2, direction=get_direction(delta2)))
    geom_list.append(s_block_cut_revolve_shift.ArcByCenterEnds(center=c3, point1=p2, point2=p3, direction=get_direction(delta3)))
    geom_list.append(s_block_cut_revolve_shift.Line(point1=p3, point2=p4))
    # 逆序循环，保证轮廓线从外到内的顺序排列
    for i in range(index_r - 1, 0, -1):
        s_block_cut_revolve_shift.offset(distance=float(points[index_r, 0][0] - points[i, 0][0]), objectList=geom_list, side=RIGHT)

    g = s_block_cut_revolve_shift.geometry
    faces_xz_plane = {}
    for i in range(1, index_r):
        faces_xz_plane[i] = []
        for j in [2, 3, 4, 5, 6]:
            pa = (np.array(g[j + 5 * (i - 1)].pointOn) + np.array(g[j + 5 * i].pointOn)) / 2.0
            faces_xz_plane[i].append(pa)
            s_block_cut_revolve_shift.Spot(point=pa)

    for i in range(1, index_r):
        for j in [3, 4, 5, 6]:
            pa = g[5 * (i - 1) + j].getVertices()[0].coords
            pb = g[5 * i + j].getVertices()[0].coords
            s_block_cut_revolve_shift.Line(point1=pa, point2=pb)

    p_faces = p.faces.getByBoundingBox(0, 0, -pen, pen, tol, pen)
    p.PartitionFaceBySketch(sketchUpEdge=d[x_axis.id], faces=p_faces, sketch=s_block_cut_revolve_shift)

    # 基于p4点所在的半径拾取sweep_edge
    x, y = polar_to_cartesian(p4[1], tol)
    sweep_edge = p.edges.findAt((x, y, z_list[-1]))

    # 拾取主体弧线
    partition_edges = []
    for g in s_block_cut_revolve_shift.geometry.values()[2:15]:
        z, x = g.pointOn
        edge_sequence = p.edges.findAt((x, 0.0, z))
        if edge_sequence is not None:
            partition_edges.append(edge_sequence)
    p.PartitionCellBySweepEdge(sweepPath=sweep_edge, cells=p.cells, edges=partition_edges)

    # 基于p4点所在的半径拾取sweep_edge
    x, y = polar_to_cartesian(p4[1], tol)
    sweep_edge = p.edges.findAt((x, y, z_list[-1]))

    # 拾取分段连线
    partition_edges = []
    for g in s_block_cut_revolve_shift.geometry.values()[15:]:
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
    p_faces = p.faces.getByBoundingBox(0, 0, tol, pen, pen, pen)
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

    # SKETCH-CUT
    s_cut = model.ConstrainedSketch(name='SKETCH-CUT', sheetSize=200.0)
    x1 = 400.0
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
    center_line = s_cut.ConstructionLine(point1=(x0 + deep - r_front, -pen), point2=(x0 + deep - r_front, pen))
    geom_list = []
    for g in s_cut.geometry.values():
        geom_list.append(g)
    s_cut.rotate(centerPoint=(0.0, 0.0), angle=180.0 / n, objectList=geom_list)
    s_cut.assignCenterline(line=center_line)

    # CutExtrude
    p.CutExtrude(sketchPlane=d[xy_plane.id], sketchUpEdge=d[y_axis.id], sketchPlaneSide=SIDE1, sketchOrientation=RIGHT, sketch=s_cut, flipExtrudeDirection=ON)

    # 旋转切割头部燃道
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

    set_names = create_block_sets_common(p, faces, dimension)

    cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
    for pa in faces_xz_plane[1]:
        cells += p.cells.findAt(((pa[1], 0.0, pa[0]),))
        center = (pa[0], 0.0, 0.0)
        plane_1 = Plane(center, (0.0, 0.0, 1.0))
        c = Circle3D(center, abs(pa[1]), plane_1)
        
        print(c.get_equation_description())

    p.Set(cells=cells, name='SET-1')

    # def is_cell_in_set(cell, p_set):
    #     for c in p_set.cells:
    #         if c == cell:
    #             return True
    #     return False
    #
    # # 寻找与SET-CELL-GRAIN相邻的cells
    # p_cells = p.cells.getByBoundingBox(0, 0, 0, 0, 0, 0)
    # for cell in p.cells:
    #     is_adjacent_grain = False
    #     for c in cell.getAdjacentCells():
    #         if is_cell_in_set(c, p.sets['SET-CELL-GRAIN']):
    #             is_adjacent_grain = True
    #             break
    #     if is_adjacent_grain:
    #         p_cells += p.cells[cell.index:cell.index + 1]
    # p.Set(cells=p_cells, name='SET-CELL-GRAIN-ADJACENT')

    # xy_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=10.0)
    # p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_rot.id], cells=p.cells)

    # xy_plane_rot = p.DatumPlaneByRotation(plane=d[xz_plane.id], axis=d[z_axis.id], angle=-10.0)
    # p.PartitionCellByDatumPlane(datumPlane=d[xy_plane_rot.id], cells=p.cells)

    # p.PartitionCellByDatumPlane(datumPlane=d[xy_plane.id], cells=p.cells)

    # pickedEdges = (p.edges[8], p.edges[42])
    # p.PartitionCellByExtrudeEdge(line=d[y_axis.id], cells=p.cells, edges=pickedEdges, sense=REVERSE)

    # create_block_surface_common(p, points, dimension)
    #
    # p_faces = p.faces.getByBoundingBox(0, 0, 0, x0 + deep + b, width / 2.0, length_up / 2.0 + b / math.cos(degrees_to_radians(angle_demolding_2)))
    # face_areas = []
    # for face in p_faces:
    #     face_area = face.getSize()
    #     face_areas.append(face_area)
    # p_faces = p.faces.getByBoundingBox(0, 0, 0, 0, 0, 0)
    # for face_id in range(len(p.faces)):
    #     face_size = p.faces[face_id].getSize()
    #     if min_difference(face_size, face_areas) < tol:
    #         p_faces += p.faces[face_id:face_id + 1]
    # if p_faces:
    #     p.Surface(side1Faces=p_faces, name='SURFACE-INNER')

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
        try:
            cells += p.cells.findAt(((faces[rtz[0], rtz[1]][0], faces[rtz[0], rtz[1]][1], z_centers[rtz[2]]),))
        except:
            pass
    cells = get_same_volume_cells(p, cells)
    if cells is not None:
        set_name = 'SET-CELL-GLUE-A'
        p.Set(cells=cells, name=set_name)
        set_names.append(set_name)

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
        try:
            cells += p.cells.findAt(((faces[rtz[0], rtz[1]][0], faces[rtz[0], rtz[1]][1], z_centers[rtz[2]]),))
        except:
            pass
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
        p.Surface(side1Faces=p_faces, name='SURFACE-R1')


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
    block_number = 10
    z_list = get_z_list(block_length, block_insulation_thickness, block_gap, block_number)

    element_size = 80

    first_block_height = 1391.0
    shell_insulation_ref_z = 407.581146

    block_dimension = {
        # 'z_list': [0, block_length / 2 - block_insulation_thickness, block_length / 2, block_length / 2 + block_gap / 2],
        'z_list': [0, 183.4, 183.4 + 3.0, 183.4 + 11.0],
        'deep': 380.0,
        'x0': x0,
        'length_up': 1039.2,
        'width': 100.0,
        'angle_demolding_1': 1.5,
        'angle_demolding_2': 10.0,
        'fillet_radius': 50.0,
        'a': 50.0,
        'b': 25.0,
        'size': '1/2',
        'index_r': 3,
        'index_t': 3
    }

    # points, lines, faces = geometries(d, x0, beta, [0, 3, 3], [0, 9, 3])
    points, lines, faces = geometries(d, x0, beta, [0, 100, 100], [0, 20, 20])

    if not ABAQUS_ENV:
        points, lines, faces = geometries(d, x0, beta, [0, 100, 100, 100], [0, 50, 50])
        # plot_geometries(points, lines, faces)

        # print(z_list)
        # p0 = (1600, 700)
        # theta0_deg = -90
        # p3 = (614.5, 1764.5)
        # theta3_deg = 0.0
        # r1, r2, r3 = 600, 1600, 800
        # result = solve_three_arcs(p0, theta0_deg, p3, theta3_deg, r1, r2, r3)
        # plot_three_arcs(result, p0, p3)
        # p = Plane((0, 0, 0), (1, 0, 0), (0, 1, 0))

        # p0 = (0.0, 794)
        # theta0_deg = 90
        # p3 = (857.6, 1762.5)
        # theta3_deg = 0.0
        # r1, r2, r3 = 850, 1524, 655.2
        # result = solve_three_arcs(p0, theta0_deg, p3, theta3_deg, r1, r2, r3)
        # plot_three_arcs(result, p0, p3)

    if ABAQUS_ENV:
        model = mdb.models['Model-1']
        model.setValues(absoluteZero=-273.15)

        # p_block_a = create_part_block_a(model, 'PART-BLOCK-A', points, lines, faces, block_dimension)
        # p_block_b = create_part_block_b(model, 'PART-BLOCK-B', points, lines, faces, block_dimension)
        # p_gap = create_part_gap(model, 'PART-GAP', points, lines, faces, block_dimension)
        p_block_front = create_part_block_front_b(model, 'PART-BLOCK-FRONT-B', points, lines, faces, block_dimension)

        # a = model.rootAssembly
        # a.DatumCsysByDefault(CARTESIAN)
        #
        # m = n
        # m = 2
        # for l in range(1, block_number):
        #     for i in range(m):
        #         instance_name = 'PART-BLOCK-%s-%s' % (l + 2, i + 1)
        #         a.Instance(name=instance_name, part=p_block_b, dependent=ON)
        #         a.translate(instanceList=(instance_name,),
        #                     vector=(0.0, 0.0, shell_insulation_ref_z - first_block_height - (l + 1) * (block_gap + block_length)))
        #         a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)
        #         instance_name = 'PART-GAP-%s-%s' % (l + 2, i + 1)
        #         a.Instance(name=instance_name, part=p_gap, dependent=ON)
        #         a.translate(instanceList=(instance_name,),
        #                     vector=(0.0, 0.0, shell_insulation_ref_z - first_block_height - (l + 1) * (block_gap + block_length)))
        #         a.rotate(instanceList=(instance_name,), axisPoint=(0.0, 0.0, 0.0), axisDirection=(0.0, 0.0, 1.0), angle=i * 360.0 / n)
