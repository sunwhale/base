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
from pyfem.Job import Job
from pyfem.database.ODB import ODB
from pyfem.io.BaseIO import BaseIO
from scipy.interpolate import interp1d
from scipy.optimize import fmin


def get_simulation(parameters: dict, strain: ndarray, time: ndarray) -> tuple[ndarray, ndarray, ndarray]:
    if int(parameters['MODE']['value']) == 0:
        strain_sim, stress_sim, time_sim = simulation_0(parameters, strain, time)
    elif int(parameters['MODE']['value']) == 1:
        strain_sim, stress_sim, time_sim = simulation_1(parameters, strain, time)
    elif int(parameters['MODE']['value']) == 2:
        strain_sim, stress_sim, time_sim = simulation_2(parameters, strain, time)
    else:
        raise KeyError
    return strain_sim, stress_sim, time_sim


def simulation_0(parameters: dict, strain: ndarray, time: ndarray) -> tuple[ndarray, ndarray, ndarray]:
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


def simulation_1(parameters: dict, strain: ndarray, time: ndarray) -> tuple[ndarray, ndarray, ndarray]:
    """
    计算耦合相场断裂的广义Maxwell模型的有限元解
    """

    path = '/home/dell/pyfem/examples/mechanical_phase/1element/hex8_visco'
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


def simulation_2(parameters: dict, strain: ndarray, time: ndarray) -> tuple[ndarray, ndarray, ndarray]:
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
