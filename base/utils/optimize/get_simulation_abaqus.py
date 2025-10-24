# -*- coding: utf-8 -*-
"""

"""
import os
import sys
import time

BASE_PATH = '/home/dell/base'
sys.path.insert(0, BASE_PATH)

import numpy as np
from numpy import ndarray

try:
    from Postproc import Postproc
    from Solver import Solver
except ModuleNotFoundError:
    from base.utils.abaqus.Postproc import Postproc
    from base.utils.abaqus.Solver import Solver


def get_simulation(parameters: dict, strain: ndarray, t: ndarray, job_path: str) -> tuple[ndarray, ndarray, ndarray]:
    """
    计算耦合相场断裂的广义Maxwell模型的有限元解
    """
    total_time = t[-1]
    total_strain = strain[-1]
    amplitude = [[t[i], strain[i]] for i in range(len(t))]

    gauge_length = 35.0
    area = 25.0

    s = Solver(job_path)
    s.read_msg()
    s.clear()
    s.write_amplitude({'Amp-1': amplitude})
    para_dict = s.parameters_to_dict()
    for para in para_dict.keys():
        if para in parameters:
            para_dict[para] = parameters[para]['value']
    para_dict['INTERVAL'] = total_time / 50.0
    para_dict['TIME'] = total_time
    s.save_parameters((s.dict_to_parameters(para_dict)))
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
        print(status)

    if is_run_finished:
        p = Postproc(job_path)
        p.read_msg()
        p.odb_to_npz()
        time.sleep(0.5)
        with open(os.path.join(job_path, '.odb_to_npz_status'), 'w', encoding='utf-8') as f:
            f.write('Submitting')
        is_odb_to_npz_done = False
        while not is_odb_to_npz_done:
            status = p.odb_to_npz_status()
            if status == 'Done':
                is_odb_to_npz_done = True
            elif status == 'Error':
                break
            else:
                time.sleep(0.5)
            print(status)

    npz_file = os.path.join(job_path, f'{s.job}.npz')
    npz = np.load(npz_file, allow_pickle=True, encoding='latin1')
    sim_data = npz['data'][()]
    u = np.array(sim_data['PART-1-1.SET-Y1']['fieldOutputs']['U']['values'])
    rf = np.array(sim_data['PART-1-1.SET-Y1']['fieldOutputs']['RF']['values'])

    disp = np.mean(u[:, :, 1], axis=1)
    force = np.sum(rf[:, :, 1], axis=1)

    strain_fem = disp / gauge_length
    stress_fem = force / area
    time_sim = npz['time']

    return np.array(strain_fem), np.array(stress_fem), np.array(time_sim)
