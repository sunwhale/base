# -*- coding: utf-8 -*-
"""

"""
import json
import logging
import os
import time
from logging import Logger
from pathlib import Path
from typing import Optional

import colorlog
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy import ndarray
from scipy.interpolate import interp1d
from scipy.optimize import fmin
from pyfem.Job import Job
from pyfem.io.BaseIO import BaseIO
from pyfem.database.ODB import ODB

logger = logging.getLogger('optimize')

colors = [
    '#1f77b4',  # Tableau 蓝色
    '#ff7f0e',  # Tableau 橙色
    '#2ca02c',  # Tableau 绿色
    '#d62728',  # Tableau 红色
    '#9467bd',  # Tableau 紫色
    '#8c564b',  # Tableau 棕色
    '#e377c2',  # Tableau 粉色
    '#7f7f7f',  # Tableau 灰色
    '#bcbd22',  # Tableau 黄绿色
    '#17becf',  # Tableau 浅蓝色
    '#ff9898',  # 浅红色
    '#98df8a'  # 浅绿色
]

colors += [
    '#1f77b4', '#aec7e8',  # 蓝色系
    '#ff7f0e', '#ffbb78',  # 橙色系
    '#2ca02c', '#98df8a',  # 绿色系
    '#d62728', '#ff9896',  # 红色系
    '#9467bd', '#c5b0d5',  # 紫色系
    '#8c564b', '#c49c94',  # 棕色系
    '#e377c2', '#f7b6d2',  # 粉色系
    '#7f7f7f', '#c7c7c7',  # 灰色系
    '#bcbd22', '#dbdb8d',  # 黄绿色系
    '#17becf', '#9edae5',  # 青色系
    '#393b79', '#5254a3',  # 深蓝色系
    '#637939', '#8ca252',  # 橄榄绿色系
    '#843c39', '#ad494a',  # 深红色系
    '#7b4173', '#a55194',  # 深紫色系
    '#3182bd', '#6baed6',  # 天蓝色系
    '#e6550d', '#fd8d3c',  # 深橙色系
    '#31a354', '#74c476',  # 亮绿色系
    '#756bb1', '#9e9ac8'  # 淡紫色系
]


def dump_json(file_path, data, encoding='utf-8'):
    """
    Write JSON data to file.
    """
    with open(file_path, 'w', encoding=encoding) as f:
        return json.dump(data, f, ensure_ascii=False)


def load_json(file_path, encoding='utf-8'):
    """
    Read JSON data from file.
    """
    with open(file_path, 'r', encoding=encoding) as f:
        return json.load(f)


def set_logger(logger: Logger, abs_job_file: Path, level: int = logging.INFO) -> Optional[logging.Logger]:
    """
    设置 logging 模块的基础配置，并返回一个 logger 对象。

    :param logger: 要配置的logger对象
    :param abs_job_file: Job配置文件的绝对路径
    :param level: 输出日志的最低级别，默认是 DEBUG 级别
    """
    # 创建 logger 对象

    # 设置日志级别
    logger.setLevel(level)

    # 创建处理器
    log_file = abs_job_file.with_suffix('.log')
    log_file_handler = logging.FileHandler(log_file, mode='w')
    log_file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    log_file_handler.setFormatter(formatter)
    logger.addHandler(log_file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    formatter = colorlog.ColoredFormatter('%(log_color)s%(message)s',
                                          log_colors={
                                              'DEBUG': 'white',
                                              'INFO': 'green',
                                              'WARNING': 'yellow',
                                              'ERROR': 'red',
                                              'CRITICAL': 'red,bg_white',
                                          })

    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


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
                 mode: str = "default",
                 strain_shift: float = 0.0,
                 strain_start: float = 0.0,
                 strain_end: float = 0.1,
                 threshold: float = 0.1,
                 stress_limit: float = None,
                 target_rows: int = None,
                 fracture_slope_criteria: float = -50.0) -> dict:
    """
    对数据进行统一预处理

    参数:
        data: 原始数据字典
        mode: 预处理模式，可选值:
            - "default": 基础预处理（去重 + 应变平移）
            - "elastic_limit": 截取弹性极限之前的部分
            - "fracture_strain": 截取断裂应变之前的部分
            - "ultimate_stress": 截取极限应力之前的部分
            - "strain_range": 截取指定应变范围
        strain_shift: 应变平移量
        strain_start: 应变范围起始值（用于strain_range模式）
        strain_end: 应变范围结束值（用于strain_range模式）
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
            if mode == "elastic_limit":
                try:
                    elastic_limit, E, shift = get_elastic_limit(strain, stress, strain_start, strain_end, threshold)
                    elastic_indices = strain < elastic_limit[0]
                    time = time[elastic_indices]
                    strain = strain[elastic_indices]
                    stress = stress[elastic_indices]
                except Exception as e:
                    print(f"Warning: Elastic limit calculation failed for {key}: {e}")
                    # 如果计算失败，保持原数据

            elif mode == "fracture_strain":
                try:
                    fracture_strain, fracture_stress = get_fracture_strain(strain, stress, fracture_slope_criteria)
                    elastic_indices = strain < (fracture_strain - 0.05)
                    time = time[elastic_indices]
                    strain = strain[elastic_indices]
                    stress = stress[elastic_indices]
                except Exception as e:
                    print(f"Warning: Fracture strain calculation failed for {key}: {e}")

            elif mode == "ultimate_stress":
                try:
                    ultimate_stress_index = np.argmax(stress)
                    time = time[:ultimate_stress_index]
                    strain = strain[:ultimate_stress_index]
                    stress = stress[:ultimate_stress_index]
                except Exception as e:
                    print(f"Warning: Ultimate stress calculation failed for {key}: {e}")

            elif mode == "strain_range":
                is_in_strain_range = (strain > strain_start) & (strain < strain_end)
                if np.any(is_in_strain_range):
                    time = time[is_in_strain_range]
                    strain = strain[is_in_strain_range]
                    stress = stress[is_in_strain_range]

        # 步骤4: 应力限制（如果指定了应力限制）
        if stress_limit is not None and len(stress) > 0:
            stress_indices = stress > stress_limit
            if np.any(stress_indices):
                time = time[stress_indices]
                strain = strain[stress_indices]
                stress = stress[stress_indices]

        # 步骤5: 数据缩减（如果指定了目标行数）
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


def analytical_solution(parameters: dict, strain: ndarray, time: ndarray) -> tuple[ndarray, ndarray, ndarray]:
    """
    计算单调拉伸实验广义Maxwell模型的解析解
    """
    t = time
    dt = np.diff(t)
    strain_rate = np.diff(strain) / np.diff(t)
    dt = np.concatenate((dt, dt[-1:]))
    strain_rate = np.concatenate((strain_rate, strain_rate[-1:]))

    h = []
    for i in range(3):
        h.append([0.0])
        E_i = parameters[f'E{i + 1}']['value']
        TAU_i = parameters[f'TAU{i + 1}']['value']
        for j in range(1, len(dt)):
            h[i].append(np.exp(-dt[j] / TAU_i) * h[i][j - 1] + TAU_i * E_i * (1.0 - np.exp(-dt[j] / TAU_i)) * strain_rate[j])

    ha = np.array(h).transpose()
    E_INF = parameters['EINF']['value']
    stress = E_INF * strain + ha.sum(axis=1)
    return strain, stress, time


def pyfem_solution(parameters: dict, strain: ndarray, time: ndarray) -> tuple[ndarray, ndarray, ndarray]:
    """
    计算耦合相场断裂的广义Maxwell模型的有限元解
    """

    path = r'F:\Github\pyfem\examples\mechanical_phase\1element\hex8_visco'
    job = Job(os.path.join(path, 'Job-1.toml'))

    total_time = time[-1]
    amplitude = [[time[i], strain[i]] for i in range(len(time))]

    BaseIO.is_read_only = False

    EINF = parameters['EINF']['value']
    E1 = parameters['E1']['value']
    E2 = parameters['E2']['value']
    E3 = parameters['E3']['value']
    TAU1 = parameters['TAU1']['value']
    TAU2 = parameters['TAU2']['value']
    TAU3 = parameters['TAU3']['value']
    LC = parameters['LC']['value']
    GC = parameters['GC']['value']
    NU = 0.499

    job.props.materials[0].data = [EINF, NU, E1, TAU1, E2, TAU2, E3, TAU3]
    job.props.materials[1].data = [GC, LC]
    job.props.solver.total_time = total_time
    job.props.solver.max_dtime = total_time / 50.0
    job.props.solver.initial_dtime = total_time / 50.0
    job.props.amplitudes[0].data = amplitude
    job.assembly.__init__(job.props)
    job.run()

    odb = ODB()
    odb.load_hdf5(os.path.join(path, 'Job-1.hdf5'))

    t = []
    e11 = []
    s11 = []
    for frame in odb.steps['Step-1']['frames']:
        t.append(frame['frameValue'])
        e11.append(frame['fieldOutputs']['E11']['bulkDataBlocks'][0])
        s11.append(frame['fieldOutputs']['S11']['bulkDataBlocks'][0])

    return np.array(e11), np.array(s11), np.array(t)


def pyfem_czm_solution(parameters: dict, strain: ndarray, time: ndarray) -> tuple[ndarray, ndarray, ndarray]:
    """
    计算耦合相场断裂的广义Maxwell模型的有限元解
    """

    path = r'F:\Github\pyfem\examples\mechanical_phase\1element\hex8_visco_czm'
    job = Job(os.path.join(path, 'Job-1.toml'))

    total_time = time[-1]
    amplitude = [[time[i], strain[i]] for i in range(len(time))]

    BaseIO.is_read_only = False

    EINF = parameters['EINF']['value']
    E1 = parameters['E1']['value']
    E2 = parameters['E2']['value']
    E3 = parameters['E3']['value']
    TAU1 = parameters['TAU1']['value']
    TAU2 = parameters['TAU2']['value']
    TAU3 = parameters['TAU3']['value']
    LC = parameters['LC']['value']
    GC = parameters['GC']['value']
    A1 = parameters['A1']['value']
    A2 = parameters['A2']['value']
    A3 = parameters['A3']['value']
    P = parameters['P']['value']
    XI = parameters['XI']['value']
    C0 = parameters['C0']['value']
    GTH = parameters['GTH']['value']
    NU = 0.499

    job.props.materials[0].data = [EINF, NU, E1, TAU1, E2, TAU2, E3, TAU3]
    job.props.materials[1].data = [GC, LC, A1, A2, A3, P, XI, C0, GTH]
    job.props.solver.total_time = total_time
    job.props.solver.max_dtime = total_time / 50.0
    job.props.solver.initial_dtime = total_time / 50.0
    job.props.amplitudes[0].data = amplitude
    job.assembly.__init__(job.props)
    job.run()

    odb = ODB()
    odb.load_hdf5(os.path.join(path, 'Job-1.hdf5'))

    t = []
    e11 = []
    s11 = []
    for frame in odb.steps['Step-1']['frames']:
        t.append(frame['frameValue'])
        e11.append(frame['fieldOutputs']['E11']['bulkDataBlocks'][0])
        s11.append(frame['fieldOutputs']['S11']['bulkDataBlocks'][0])

    return np.array(e11), np.array(s11), np.array(t)


class Optimize:
    """
    Optimize类。
    """

    def __init__(self, path, job='Job-1', is_clear=True):
        self.path = path
        self.job = job
        self.is_clear = is_clear
        self.counter = 0
        self.last_plot_time = time.time()
        self.max_iter = 100

        self.msg_file = os.path.join(path, '.optimize_msg')
        self.parameters_json_file = os.path.join(path, 'parameters.json')
        self.experiments_json_file = os.path.join(path, 'experiments.json')
        self.abs_job_file = Path(os.path.join(path, f'{self.job}.py'))

        self.parameters = {}
        self.experiment_data = {}
        self.simulation_data = {}
        self.data = {}
        self.paras_0 = []
        self.load_settings()
        self.preproc()

        if not logger.hasHandlers():
            set_logger(logger, self.abs_job_file)

    def load_settings(self):
        if os.path.exists(self.msg_file) and os.path.exists(self.parameters_json_file):
            message = load_json(self.msg_file)
            parameters_json = load_json(self.parameters_json_file)
            for p in [item.strip() for item in message['para'].split(',')]:
                self.parameters[p] = {}
                if f'check_{p}' in parameters_json:
                    self.parameters[p]['type'] = 'variable'
                else:
                    self.parameters[p]['type'] = 'constant'
                self.parameters[p]['value'] = float(parameters_json[f'value_{p}'])

        if os.path.exists(self.msg_file) and os.path.exists(self.experiments_json_file):
            experiments_json = load_json(self.experiments_json_file)
            experiment_id = int(experiments_json['experiment_id'].split('_')[0])
            experiments_path = experiments_json['EXPERIMENT_PATH']
            for key in experiments_json.keys():
                if 'check' in key:
                    specimen_id = int(key.split('_')[1])
                    csv_file = os.path.join(experiments_path, str(experiment_id), str(specimen_id), 'timed.csv')
                    self.experiment_data[specimen_id] = pd.read_csv(csv_file)

        self.paras_0 = []
        for key in self.parameters.keys():
            if self.parameters[key]['type'] == 'variable':
                self.paras_0.append(self.parameters[key]['value'])

    def write_parameters_json_file(self):
        parameters_dict = {}
        for p in self.parameters.keys():
            if self.parameters[p]['type'] == 'variable':
                parameters_dict[f'check_{p}'] = 'on'
            parameters_dict[f'value_{p}'] = self.parameters[p]['value']
        dump_json(self.parameters_json_file, parameters_dict)

    def preproc(self):
        # self.data = preproc_data(self.experiment_data, mode='strain_range', strain_start=0.000, strain_end=0.12, target_rows=100)
        self.data = preproc_data(self.experiment_data, mode='ultimate_stress', target_rows=50)

    def run(self):
        lock_file = Path(os.path.join(self.path, f'{self.job}.lck'))
        # if lock_file.exists():
        #     exit(f'Error: The job is locked.\nIt may be running or terminated with exception.')
        lock_file.touch()
        logger.info('OPTIMIZE INITIATED')
        self.counter = 0
        paras = fmin(self.func, self.paras_0, args=(self.data, self.parameters), maxiter=self.max_iter, ftol=1e-4, xtol=1e-4, disp=True)
        self.update_variable_parameters(paras, self.parameters)
        self.plot_with_paras(self.data, self.parameters)
        logger.info('OPTIMIZE COMPLETED')
        lock_file.unlink()

    def func(self, x: list, data: dict, paras: dict):
        self.counter += 1

        cost = 0.0
        self.update_variable_parameters(x, paras)
        cost += self.get_cost(data, paras)

        punish = 0.0
        y = cost
        for i in range(len(x)):
            punish += (max(0, -x[i])) ** 2
        y += 1e16 * punish

        logger.info(f'迭代 {self.counter}: 总成本 = {y:.6f}, 真实成本 = {cost:.6f}, 惩罚项 = {punish:.2e}')
        self.write_parameters_json_file()

        if time.time() - self.last_plot_time > 2.0:
            self.plot_with_data()
            self.last_plot_time = time.time()

        return y

    def get_cost(self, data: dict, paras: dict):
        """
        计算实验值与预测值的误差
        """
        cost = 0.0
        for key in data.keys():
            time_exp = data[key]['Time_s']
            strain_exp = data[key]['Strain']
            stress_exp = data[key]['Stress_MPa']
            # strain_sim, stress_sim, time_sim = analytical_solution(paras, strain_exp, time_exp)
            # strain_sim, stress_sim, time_sim = pyfem_solution(paras, strain_exp, time_exp)
            strain_sim, stress_sim, time_sim = pyfem_czm_solution(paras, strain_exp, time_exp)
            self.simulation_data[key] = {}
            self.simulation_data[key]['Time_s'] = time_sim
            self.simulation_data[key]['Strain'] = strain_sim
            self.simulation_data[key]['Stress_MPa'] = stress_sim
            f_time_stress = data[key]['f_time_stress']
            stress_exp = f_time_stress(time_sim)
            cost += np.sum(((stress_exp - stress_sim) / max(stress_exp)) ** 2, axis=0) / len(time_sim)
        return cost

    def plot_with_data(self) -> None:
        fig, ax = plt.subplots(figsize=(8, 6))
        for i, key in enumerate(self.experiment_data.keys()):
            color = colors[i]
            stress_exp = self.data[key]['Stress_MPa']
            strain_exp = self.data[key]['Strain']
            stress_sim = self.simulation_data[key]['Stress_MPa']
            strain_sim = self.simulation_data[key]['Strain']
            ax.plot(strain_exp, stress_exp, marker='o', markerfacecolor='none', color=color, label=f'Exp. {key}', ls='')
            ax.plot(strain_sim, stress_sim, color=color)

        ax.legend(loc=0)
        ax.grid(True, which='major', alpha=0.3)
        plt.savefig('fig.png', dpi=150, transparent=True)
        plt.close()

    @staticmethod
    def update_variable_parameters(x: list | tuple, parameters: dict) -> dict:
        """
        更新参数字典中的变量参数值

        Args:
            parameters: 参数字典
            x: 变量值数组
        """
        x_iter = iter(x)
        for name in parameters.keys():
            if parameters[name]['type'] == 'variable':
                parameters[name]['value'] = next(x_iter)

        return parameters

    @staticmethod
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

    @staticmethod
    def plot_with_paras(data: dict, paras: dict) -> None:
        fig, ax = plt.subplots(figsize=(8, 6))
        for i, key in enumerate(data.keys()):
            color = colors[i]
            time_exp = data[key]['Time_s']
            stress_exp = data[key]['Stress_MPa']
            strain_exp = data[key]['Strain']
            strain_sim, stress_sim, time_sim = analytical_tensile_solution(paras, strain_exp, time_exp)
            ax.plot(strain_exp, stress_exp, marker='o', markerfacecolor='none', color=color, label=f'Exp. {key}', ls='')
            ax.plot(strain_sim, stress_sim, color=color)

        ax.legend(loc=0)
        ax.grid(True, which='major', alpha=0.3)
        plt.savefig('fig.png', dpi=150, transparent=True)
        plt.close()


if __name__ == '__main__':
    o = Optimize(Path(__file__).resolve().parent)
    o.run()
