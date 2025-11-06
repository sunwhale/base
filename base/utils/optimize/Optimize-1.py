# -*- coding: utf-8 -*-
"""

"""
import json
import logging
import os
import shutil
import sys
import threading
import time
from logging import Logger
from pathlib import Path
from typing import Optional

import colorlog
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.optimize import fmin

UTILS_PATH = '/home/dell/base'
sys.path.insert(0, UTILS_PATH)

try:
    from preproc_data import preproc_data
except ModuleNotFoundError:
    from base.utils.optimize.preproc_data import preproc_data

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


def make_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def files_in_dir(path):
    file_list = []
    for filename in sorted(next(os.walk(path))[2]):
        file = {}
        file['name'] = filename
        file_list.append(file)
    return file_list


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


def create_job(project_path, job_path, job, user, cpus):
    make_dir(job_path)
    message = {
        'job': job,
        'user': user,
        'cpus': cpus,
        'descript': ''
    }
    msg_file = os.path.join(job_path, '.job_msg')
    dump_json(msg_file, message)
    files = files_in_dir(project_path)
    for file in files:
        shutil.copy(os.path.join(project_path, file['name']), os.path.join(job_path, file['name']))


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


class ReturnThread(threading.Thread):
    def __init__(self, target, args=(), kwargs=None):
        super().__init__()
        if kwargs is None:
            kwargs = {}
        self.target = target
        self.args = args
        self.kwargs = kwargs
        self.result = None

    def run(self):
        self.result = self.target(*self.args, **self.kwargs)


class Optimize:
    """
    Optimize类。
    """

    def __init__(self, path, is_clear=True):
        self.path = path
        self.is_clear = is_clear
        self.counter = 0
        self.last_plot_time = time.time()
        self.maxiter = 100

        self.msg_file = os.path.join(path, '.optimize_msg')
        self.parameters_json_file = os.path.join(path, 'parameters.json')
        self.experiments_json_file = os.path.join(path, 'experiments.json')
        self.preproc_json_file = os.path.join(path, 'preproc.json')
        self.optimize_type = ''
        self.project_path = ''
        self.project_job = ''
        self.project_user = ''
        self.project_cpus = ''

        self.parameters = {}
        self.experiment_data = {}
        self.simulation_data = {}
        self.preproc_json = {}
        self.data = {}
        self.paras_0 = []
        self.job = ''
        self.abs_job_file = Path()
        self.get_simulation = None
        self.load_settings()
        self.preproc()

        if not logger.hasHandlers():
            set_logger(logger, self.abs_job_file)

    def load_settings(self):
        if os.path.exists(self.msg_file) and os.path.exists(self.parameters_json_file):
            message = load_json(self.msg_file)
            self.job = message['job']
            self.abs_job_file = Path(os.path.join(self.path, f'{self.job}.py'))
            self.optimize_type = message['type']
            self.project_path = message['project_path']
            self.maxiter = int(message['maxiter'])
            if self.optimize_type == '解析解':
                pass
            elif (self.optimize_type == 'ABAQUS项目' or self.optimize_type == 'PYFEM项目') and os.path.exists(self.project_path):
                project_message = load_json(os.path.join(self.project_path, '.project_msg'))
                self.project_job = project_message['job']
                self.project_user = project_message['user']
                self.project_cpus = project_message['cpus']
            else:
                raise NotImplementedError(f'{self.project_path} not exist')

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

        if os.path.exists(self.msg_file) and os.path.exists(self.preproc_json_file):
            self.preproc_json = load_json(self.preproc_json_file)

        self.paras_0 = []
        for key in self.parameters.keys():
            if self.parameters[key]['type'] == 'variable':
                self.paras_0.append(self.parameters[key]['value'])

        type_mapping = {
            '解析解': 'get_simulation_analytical',
            'PYFEM项目': 'get_simulation_pyfem',
            'ABAQUS项目': 'get_simulation_abaqus'
        }

        if self.optimize_type in type_mapping:
            module_name = type_mapping[self.optimize_type]
            module = __import__(module_name)
            self.get_simulation = getattr(module, 'get_simulation')
        else:
            raise ValueError(f"Unsupported optimize type: {self.optimize_type}")

    def write_parameters_json_file(self):
        parameters_dict = {}
        for p in self.parameters.keys():
            if self.parameters[p]['type'] == 'variable':
                parameters_dict[f'check_{p}'] = 'on'
            parameters_dict[f'value_{p}'] = self.parameters[p]['value']
        dump_json(self.parameters_json_file, parameters_dict)

    def preproc(self):
        self.data = preproc_data(data=self.experiment_data,
                                 mode=self.preproc_json['preproc_mode'],
                                 strain_shift=self.preproc_json['strain_shift'],
                                 strain_start=self.preproc_json['strain_start'],
                                 strain_end=self.preproc_json['strain_end'],
                                 stress_start=self.preproc_json['stress_start'],
                                 stress_end=self.preproc_json['stress_end'],
                                 threshold=self.preproc_json['threshold'],
                                 target_rows=self.preproc_json['target_rows'],
                                 fracture_slope_criteria=self.preproc_json['fracture_slope_criteria'])

    def run(self):
        lock_file = Path(os.path.join(self.path, f'{self.job}.lck'))
        # if lock_file.exists():
        #     exit(f'Error: The job is locked.\nIt may be running or terminated with exception.')
        lock_file.touch()
        logger.info('OPTIMIZE INITIATED')
        self.counter = 0
        paras = fmin(self.func, self.paras_0, args=(self.data, self.parameters), maxiter=self.maxiter, ftol=1e-4, xtol=1e-4, disp=True)
        self.update_variable_parameters(paras, self.parameters)
        self.plot_with_data()
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

        logger.info(f'迭代 {self.counter}: 总成本 = {y:.6f}')
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
        threads = {}
        for i, key in enumerate(data.keys()):
            time_exp = data[key]['Time_s']
            strain_exp = data[key]['Strain']
            stress_exp = data[key]['Stress_MPa']
            if self.optimize_type == '解析解':
                threads[key] = ReturnThread(target=self.get_simulation, args=(paras, strain_exp, time_exp))
            elif self.optimize_type == 'PYFEM项目':
                job_path = os.path.join(self.project_path, str(i + 1))
                if not os.path.exists(job_path):
                    create_job(self.project_path, job_path, self.project_job, self.project_user, self.project_cpus)
                threads[key] = ReturnThread(target=self.get_simulation, args=(paras, strain_exp, time_exp, job_path))
            elif self.optimize_type == 'ABAQUS项目':
                job_path = os.path.join(self.project_path, str(i + 1))
                if not os.path.exists(job_path):
                    create_job(self.project_path, job_path, self.project_job, self.project_user, self.project_cpus)
                threads[key] = ReturnThread(target=self.get_simulation, args=(paras, strain_exp, time_exp, job_path))
                time.sleep(0.2)
            threads[key].start()

        for key in threads.keys():
            threads[key].join()
            strain_sim, stress_sim, time_sim = threads[key].result
            self.simulation_data[key] = {}
            self.simulation_data[key]['Time_s'] = time_sim
            self.simulation_data[key]['Strain'] = strain_sim
            self.simulation_data[key]['Stress_MPa'] = stress_sim
            f_time_stress = data[key]['f_time_stress']
            stress_exp = f_time_stress(time_sim)
            cost += np.sum(((stress_exp - stress_sim) / max(stress_exp)) ** 2, axis=0) / len(time_sim)
        return cost

    def plot_with_data(self) -> None:
        fig_path = os.path.join(self.path, 'fig.png')
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
        plt.savefig(fig_path, dpi=150, transparent=True)
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


if __name__ == '__main__':
    o = Optimize(Path(__file__).resolve().parent)
    t0 = time.time()
    o.run()
    t1 = time.time()
    print(t1 - t0)
