# -*- coding: utf-8 -*-
"""

"""

import numpy as np
from numpy import ndarray
from scipy.interpolate import interp1d


def get_elastic_module(strain: ndarray, stress: ndarray) -> tuple[float, float]:
    coefficients = np.polyfit(strain, stress, 1)
    E = float(coefficients[0])
    shift = float(coefficients[1])
    return E, shift


def get_elastic_limit(strain: ndarray, stress: ndarray, strain_start: float, strain_end: float, threshold: float) -> tuple[list[float], float, float]:
    elastic_part = (strain > strain_start) & (strain < strain_end)
    elastic_strain = strain[elastic_part]
    elastic_stress = stress[elastic_part]
    E, shift = get_elastic_module(elastic_strain, elastic_stress)
    error = abs(E * strain + shift - stress)
    elastic_limit_index = strain[error < threshold].shape[0]
    elastic_limit = [float(strain[elastic_limit_index]), float(stress[elastic_limit_index])]
    return elastic_limit, E, shift


def get_fracture_strain(strain: ndarray, stress: ndarray, slop_criteria: float) -> tuple[float, float]:
    ultimate_stress_index = np.argmax(stress)
    stress_after_ultimate = stress[ultimate_stress_index:]
    strain_after_ultimate = strain[ultimate_stress_index:]
    diff_stress = np.diff(stress_after_ultimate)
    diff_strain = np.diff(strain_after_ultimate)
    none_zero_indices = (diff_strain != 0.0)
    derivative = diff_stress[none_zero_indices] / diff_strain[none_zero_indices]
    if not np.all(derivative < slop_criteria):
        fracture_strain_index = np.array(range(derivative.shape[0]))[derivative < slop_criteria][0]
        fracture_strain = strain_after_ultimate[1:][none_zero_indices][fracture_strain_index]
        fracture_stress = stress_after_ultimate[1:][none_zero_indices][fracture_strain_index]
        return float(fracture_strain), float(fracture_stress)
    else:
        return float(strain[-1]), float(stress[-1])


def preproc_data(data: dict,
                 mode: str = '基础预处理',
                 strain_shift: float = 0.0,
                 strain_start: float = 0.0,
                 strain_end: float = 1.0,
                 stress_start: float = 0.0,
                 stress_end: float = 1.0,
                 threshold: float = 0.1,
                 target_rows: int = None,
                 fracture_slope_criteria: float = -50.0) -> dict:
    """
    对数据进行统一预处理

    参数:
        data: 原始数据字典
        mode: 预处理模式，可选值:
            - 'default': 基础预处理（去重 + 应变平移）
            - 'elastic_limit': 截取弹性极限之前的部分
            - 'fracture_strain': 截取断裂应变之前的部分
            - 'ultimate_stress': 截取极限应力之前的部分
            - 'strain_range': 截取指定应变范围
        strain_shift: 应变平移量
        strain_start: 应变范围起始值（用于strain_range模式）
        strain_end: 应变范围结束值（用于strain_range模式）
        stress_start: 应变范围起始值（用于stress_range模式）
        stress_end: 应变范围结束值（用于stress_range模式）
        threshold: 弹性极限判断阈值
        stress_limit: 应力限制值
        target_rows: 目标数据行数（用于数据缩减）
        fracture_slope_criteria: 断裂应变判断的斜率阈值

    返回:
        处理后的数据字典
    """
    processed_data = {}

    for key in data.keys():
        time = np.array(data[key]['Time_s'])
        strain = np.array(data[key]['Strain'])
        stress = np.array(data[key]['Stress_MPa'])

        # 步骤1: 去除时间重复的数据点
        if len(time) > 0:
            is_duplicate = np.full(len(time), False)
            values, counts = np.unique(time, return_index=True)
            is_duplicate[counts] = True
            time = time[is_duplicate]
            strain = strain[is_duplicate]
            stress = stress[is_duplicate]

        # 步骤2: 应变平移（如果指定了平移量）
        if strain_shift > 0 and len(strain) > 0:
            shift_indices = strain < strain_shift
            if np.any(shift_indices):
                shift = len(time[shift_indices])
                if shift < len(strain):
                    strain = strain[shift:] - strain_shift
                    time = time[shift:] - time[shift]
                    stress = stress[shift:]

        # 步骤3: 根据模式进行数据截取
        if len(strain) > 0:
            if mode == '截取弹性极限之前的部分':
                try:
                    elastic_limit, E, shift = get_elastic_limit(strain, stress, strain_start, strain_end, threshold)
                    elastic_indices = strain < elastic_limit[0]
                    time = time[elastic_indices]
                    strain = strain[elastic_indices]
                    stress = stress[elastic_indices]
                except Exception as e:
                    print(f'Warning: Elastic limit calculation failed for {key}: {e}')
                    # 如果计算失败，保持原数据

            elif mode == '截取断裂应变之前的部分':
                try:
                    fracture_strain, fracture_stress = get_fracture_strain(strain, stress, fracture_slope_criteria)
                    elastic_indices = strain < (fracture_strain - 0.05)
                    time = time[elastic_indices]
                    strain = strain[elastic_indices]
                    stress = stress[elastic_indices]
                except Exception as e:
                    print(f'Warning: Fracture strain calculation failed for {key}: {e}')

            elif mode == '截取极限应力之前的部分':
                try:
                    ultimate_stress_index = np.argmax(stress)
                    time = time[:ultimate_stress_index]
                    strain = strain[:ultimate_stress_index]
                    stress = stress[:ultimate_stress_index]
                except Exception as e:
                    print(f'Warning: Ultimate stress calculation failed for {key}: {e}')

            elif mode == '截取指定应变范围':
                is_in_strain_range = (strain > strain_start) & (strain < strain_end)
                if np.any(is_in_strain_range):
                    time = time[is_in_strain_range]
                    strain = strain[is_in_strain_range]
                    stress = stress[is_in_strain_range]

            elif mode == '截取指定应力范围':
                is_in_stress_range = (stress > stress_start) & (stress < stress_end)
                if np.any(is_in_stress_range):
                    time = time[is_in_stress_range]
                    strain = strain[is_in_stress_range]
                    stress = stress[is_in_stress_range]

        # 步骤4: 数据缩减（如果指定了目标行数）
        if target_rows is not None and len(time) > target_rows:
            total_rows = len(time)
            interval = total_rows // target_rows
            time = time[::interval]
            strain = strain[::interval]
            stress = stress[::interval]

        processed_data[key] = create_data_dict(time, strain, stress)

    return processed_data


def create_data_dict(time: ndarray, strain: ndarray, stress: ndarray) -> dict:
    f_strain_stress = interp1d(strain, stress, kind='linear', fill_value='extrapolate')
    f_time_strain = interp1d(time, strain, kind='linear', fill_value='extrapolate')
    f_time_stress = interp1d(time, stress, kind='linear', fill_value='extrapolate')
    data = {'Time_s': time,
            'Strain': strain,
            'Stress_MPa': stress,
            'f_strain_stress': f_strain_stress,
            'f_time_strain': f_time_strain,
            'f_time_stress': f_time_stress}
    return data
