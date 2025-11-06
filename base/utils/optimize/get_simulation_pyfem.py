# -*- coding: utf-8 -*-
"""

"""
import os
import time
import sys

BASE_PATH = '/home/dell/base'
sys.path.insert(0, BASE_PATH)

import numpy as np
from numpy import ndarray
from pyfem.database.ODB import ODB

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

try:
    from Solver import Solver
except ModuleNotFoundError:
    from base.utils.pyfem.Solver import Solver


def get_simulation(parameters: dict, strain: ndarray, t: ndarray, job_path: str) -> tuple[ndarray, ndarray, ndarray]:
    """
    计算耦合相场断裂的广义Maxwell模型的有限元解
    """
    total_time = t[-1]
    amplitude = [[t[i], strain[i]] for i in range(len(t))]

    s = Solver(job_path)
    s.read_msg()
    s.clear()

    para_dict = s.parameters_to_dict()
    for para in para_dict.keys():
        if para in parameters:
            para_dict[para] = parameters[para]['value']
    para_dict['INTERVAL'] = total_time / 50.0
    para_dict['TIME'] = total_time
    para_dict['AMP1'] = amplitude
    s.save_parameters(para_dict)
    s.parameters_to_json()
    s.run()
    with open(os.path.join(job_path, '.solver_status'), 'w', encoding='utf-8') as f:
        f.write('Submitting')
    is_run_finished = False
    while not is_run_finished:
        status = s.solver_status()
        if status == 'Completed':
            is_run_finished = True
        elif status == 'Stopped':
            is_run_finished = True
        else:
            time.sleep(0.5)

    t = []
    e11 = []
    s11 = []

    if is_run_finished:
        odb = ODB()
        odb.load_hdf5(os.path.join(job_path, f'{s.job}.hdf5'))
        for frame in odb.steps['Step-1']['frames']:
            t.append(frame['frameValue'])
            e11.append(frame['fieldOutputs']['E11']['bulkDataBlocks'][0])
            s11.append(frame['fieldOutputs']['S11']['bulkDataBlocks'][0])

    return np.array(e11), np.array(s11), np.array(t)
