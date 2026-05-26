import os
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import requests
from scipy.interpolate import LinearNDInterpolator, RBFInterpolator


def load_status(url='http://127.0.0.1:5000/'):
    response = requests.get(url)
    result = response.json()
    jobs = result['data']
    jobs_status = {}
    for job in jobs:
        job_id = job['job_id']
        jobs_status[job_id] = {}
        for key in job.keys():
            jobs_status[job_id][key] = job[key]
    return jobs_status


def load_region_data(npz_file, regions):
    npz = np.load(npz_file, allow_pickle=True, encoding='latin1')
    data = npz['data'][()]
    time = npz['time']
    step_time = npz['step_time'][()]

    # print(step_time)

    all_regions = data.keys()
    odb_data = {}
    out_data = {}

    for r in regions:
        odb_data[r] = {}
        region_elementLabels = []
        region_nodeLabels = []
        region_nodeCoords = []
        for e in data[r]['elements']:
            region_elementLabels.append(e['label'])
        for n in data[r]['nodes']:
            region_nodeLabels.append(n['label'])
            region_nodeCoords.append(n['coordinates'])

        odb_data[r]['region_elementLabels'] = region_elementLabels
        odb_data[r]['region_nodeLabels'] = region_nodeLabels
        odb_data[r]['region_nodeCoords'] = np.array(region_nodeCoords)
        odb_data[r]['regionType'] = data[r]['regionType']
        odb_data[r]['fieldOutputs'] = {}

        # print(region_nodeLabels[9])

        # stress = np.array(data[r]['fieldOutputs']['S']['values'])
        # try:
        #     strain = np.array(data[r]['fieldOutputs']['E']['values'])
        # except:
        #     strain = np.array(data[r]['fieldOutputs']['LE']['values'])

        u = np.array(data[r]['fieldOutputs']['U']['values'])

        # print(u[:,9,:])

        out_data[r] = {}
        out_data[r]['step_time'] = step_time
        out_data[r]['time'] = time
        out_data[r]['u'] = u
        out_data[r]['coords'] = odb_data[r]['region_nodeCoords']

    return out_data


def cart2cyl(points):
    """
    points: (N, 3) 数组，每行为 (x, y, z)
    返回: (N, 3) 数组，每行为 (ρ, φ, z)
    """
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    rho = np.hypot(x, y)  # sqrt(x^2+y^2)
    phi = np.arctan2(y, x)  # 弧度
    return np.column_stack((rho, phi, z))


def cartesian_to_cylindrical_displacement_batch(points, displacements):
    """
    将一组笛卡尔位移向量批量转换到柱坐标系。

    参数:
        points: numpy array, shape (N, 3) -> 每个点的 (x, y, z)
        displacements: numpy array, shape (N, M, 3) -> N 个点，每个点 M 个位移向量，每个向量 (dx, dy, dz)

    返回:
        cyl_displacements: numpy array, shape (N, M, 3) -> 柱坐标位移 (d_rho, d_phi, d_z)
    """
    N, M, _ = displacements.shape
    x = points[:, 0]
    y = points[:, 1]

    # 计算每个点的方位角
    phi = np.arctan2(y, x)  # shape (N,)
    cos_phi = np.cos(phi).reshape(N, 1)  # (N, 1)
    sin_phi = np.sin(phi).reshape(N, 1)  # (N, 1)

    # 提取位移分量 (N, M)
    dx = displacements[..., 0]
    dy = displacements[..., 1]
    dz = displacements[..., 2]

    # 柱坐标下的位移分量（广播： (N,M) * (N,1) -> (N,M)）
    drho = dx * cos_phi + dy * sin_phi
    dphi = -dx * sin_phi + dy * cos_phi
    dz_out = dz

    # 合并结果 (N, M, 3)
    cyl_displacements = np.stack([drho, dphi, dz_out], axis=-1)
    return cyl_displacements


def fit_plane_lsq(points):
    """
    最小二乘法拟合三维点集的最佳平面
    points: (N, 3) 数组，N 个三维点
    返回: (a, b, c, d) 满足 a*x + b*y + c*z + d = 0, 且 (a,b,c) 为单位向量
    """
    # 1. 计算质心
    centroid = np.mean(points, axis=0)

    # 2. 数据中心化
    centered = points - centroid

    # 3. 计算协方差矩阵
    # 方法一：直接矩阵乘法 (N,3)^T * (N,3) -> (3,3)
    S = centered.T @ centered  # 或 np.dot(centered.T, centered)

    # 4. 特征分解，取最小特征值对应的特征向量
    eigenvalues, eigenvectors = np.linalg.eigh(S)  # 升序排列
    normal = eigenvectors[:, 0]  # 最小特征值对应的列向量

    # 5. 计算 d
    a, b, c = normal
    d = -np.dot(normal, centroid)

    return a, b, c, d


def normal_component(displacement, a, b, c, d=None):
    """
    计算位移向量垂直于平面 a*x + b*y + c*z + d = 0 的分量。

    参数：
        displacement: ndarray，形状 (N, T, 3) 或 (N*T, 3)
        a, b, c, d: 平面系数（d 不参与计算）

    返回：
        normal_part: ndarray，形状同 displacement，为垂直分量
    """
    n = np.array([a, b, c], dtype=float)
    norm = np.linalg.norm(n)
    if norm == 0:
        raise ValueError("法向量不能为零")
    n_unit = n / norm

    dot = np.dot(displacement, n_unit)  # (N, T) 或 (N*T,)
    # 将点积广播为形状 (..., 3)
    normal_part = np.outer(dot, n_unit).reshape(displacement.shape)
    return normal_part


def distance(point1, point2):
    """
    计算两个点之间的欧氏距离。

    参数:
        point1, point2: 点的坐标，可以是列表或元组，如 (x1, y1) 或 (x1, y1, z1)

    返回:
        两点之间的欧氏距离（浮点数）
    """
    if len(point1) != len(point2):
        raise ValueError("两个点的维度必须相同")

    squared_diff_sum = sum((p1 - p2) ** 2 for p1, p2 in zip(point1, point2))
    return math.sqrt(squared_diff_sum)


def normal_scalar_projection(displacement, a, b, c, d=None):
    """
    计算位移向量在平面法向上的有符号投影长度。

    参数：
        displacement: ndarray，形状 (198, 83, 3)
        a, b, c: 平面法向量系数

    返回：
        scalar_proj: ndarray，形状 (198, 83)，每个值为 v·n_hat
    """
    n = np.array([a, b, c], dtype=float)
    norm = np.linalg.norm(n)
    if norm == 0:
        raise ValueError("法向量不能为零")
    n_unit = n / norm

    # 点积：自动将最后维度 (3) 与 n_unit 进行点积
    scalar_proj = np.dot(displacement, n_unit)  # 结果形状 (198, 83)
    return scalar_proj


data = {}

jobs_status = load_status('https://www.sunjingyu.com:8010/abaqus/project_jobs_status/70')

job_ids = [8]

set_a = 'BLOCK-2-1.SET-FACES-INSULATION-GLUE-A-T1'
set_b = 'BLOCK-2-2.SET-FACES-INSULATION-GLUE-A-T-1'

for job_id in job_ids:
    job_status = jobs_status[job_id]
    job_path = job_status['path']
    npz_file = os.path.join(job_path, job_status['job'] + '.npz')
    # npz_file = os.path.join(job_path, 'Job-0' + '.npz')
    data[job_id] = load_region_data(npz_file, [set_a, set_b])

for job_id in data.keys():
    time = data[job_id][set_a]['time']
    step_time = data[job_id][set_a]['step_time']
    u_a = data[job_id][set_a]['u']
    u_b = data[job_id][set_b]['u']
    coords_a = data[job_id][set_a]['coords']
    coords_b = data[job_id][set_b]['coords']

# 指定顺序
order = ['Step-1', 'Step-2', 'Step-3']
# 累加偏移量，初始为0
offset = 0.0
total_time = []
for step in order:
    times = step_time[step]
    # 当前step的所有时间点加上累积偏移量
    shifted = [t + offset for t in times]
    total_time.extend(shifted)
    # 更新偏移量为当前step最后一个时间点（即当前step结束的绝对时间）
    offset = shifted[-1]

print(coords_a[9, :])
print(coords_b[9, :])

cyl_coords_a = cart2cyl(coords_a)
cyl_coords_b = cart2cyl(coords_b)

print(cyl_coords_a[9, :])
print(cyl_coords_b[9, :])

u_a = np.swapaxes(u_a, 0, 1)
u_b = np.swapaxes(u_b, 0, 1)

print(u_a[9, 82, :])
print(u_b[9, 82, :])

print(u_a.shape, coords_a.shape)
u_max = []

# for nt in range(0, 83):
for nt in [82]:
    a, b, c, d = fit_plane_lsq(coords_a + u_a[:, nt, :])
    # print(f"拟合平面: {a:.4f}*x + {b:.4f}*y + {c:.4f}*z + {d:.4f} = 0")
    # print(f"法向量模长: {np.sqrt(a * a + b * b + c * c):.6f}")
    u_a_normal = normal_scalar_projection(u_a[:, nt, :], a, b, c, d)
    u_b_normal = normal_scalar_projection(u_b[:, nt, :], a, b, c, d)
    linear_interp = LinearNDInterpolator(list(zip(cyl_coords_a[:, 0], cyl_coords_a[:, 2])), u_a_normal)

    u = linear_interp(list(zip(cyl_coords_b[:, 0], cyl_coords_b[:, 2]))) - u_b_normal
    u_max.append(u.max())
    # print(u)
    # x = cyl_coords_a[:,0]
    # y = cyl_coords_a[:,2]
    # z = u
    # plt.figure(figsize=(8, 6))
    # plt.scatter(x, y, c=z, edgecolor='k', cmap='rainbow')
    # plt.colorbar(label='z')
    # plt.show()

# plt.plot(total_time, u_max)
# plt.show()
