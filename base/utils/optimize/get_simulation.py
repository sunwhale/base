# -*- coding: utf-8 -*-
"""

"""
import os

import numpy as np
from numpy import ndarray
from pyfem.Job import Job
from pyfem.database.ODB import ODB
from pyfem.io.BaseIO import BaseIO
from Solver import Solver
from Postproc import Postproc
import time


def get_simulation(parameters: dict, strain: ndarray, time: ndarray) -> tuple[ndarray, ndarray, ndarray]:
    if int(parameters['MODE']['value']) == 0:
        strain_sim, stress_sim, time_sim = simulation_0(parameters, strain, time)
    elif int(parameters['MODE']['value']) == 1:
        strain_sim, stress_sim, time_sim = simulation_1(parameters, strain, time)
    elif int(parameters['MODE']['value']) == 2:
        strain_sim, stress_sim, time_sim = simulation_2(parameters, strain, time)
    elif int(parameters['MODE']['value']) == 3:
        strain_sim, stress_sim, time_sim = simulation_3(parameters, strain, time)
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


def simulation_3(parameters: dict, strain: ndarray, t: ndarray) -> tuple[ndarray, ndarray, ndarray]:
    """
    计算耦合相场断裂的广义Maxwell模型的有限元解
    """
    job_path = '/home/dell/www/base/files/abaqus/25/13'

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
    para_dict['INTERVAL'] = total_time / 60.0
    para_dict['TIME'] = total_time
    para_dict['STRAIN'] = total_strain * gauge_length
    s.save_parameters((s.dict_to_parameters(para_dict)))
    s.run()
    with open(os.path.join(job_path, '.solver_status'), 'w', encoding='utf-8') as f:
        f.write('Submitting')
    is_run_completed = False
    while not is_run_completed:
        status = s.solver_status()
        if status == 'Completed':
            is_run_completed = True
        elif status == 'Stopped':
            break
        else:
            time.sleep(1)
        print(status)

    if is_run_completed:
        p = Postproc(job_path)
        p.read_msg()
        p.odb_to_npz()
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
                time.sleep(1)
            print(status)

    npz_file = os.path.join(job_path, f'{s.job}.npz')
    sim_data = load_region_data(npz_file, ['PART-1-1.SET-Y1'])
    strain_fem = sim_data['PART-1-1.SET-Y1']['disp'] / gauge_length
    stress_fem = sim_data['PART-1-1.SET-Y1']['force'] / area
    time_sim = sim_data['PART-1-1.SET-Y1']['time']

    return np.array(strain_fem), np.array(stress_fem), np.array(time_sim)


def load_region_data(npz_file, regions):
    npz = np.load(npz_file, allow_pickle=True, encoding='latin1')
    data = npz['data'][()]
    time = npz['time']

    all_regions = data.keys()
    odb_data = {}
    out_data = {}

    for r in regions:

        odb_data[r] = {}
        region_elementLabels = []
        region_nodeLabels = []
        for e in data[r]['elements']:
            region_elementLabels.append(e['label'])
        for n in data[r]['nodes']:
            region_nodeLabels.append(n['label'])

        odb_data[r]['region_elementLabels'] = region_elementLabels
        odb_data[r]['region_nodeLabels'] = region_nodeLabels
        odb_data[r]['position'] = data[r]['fieldOutputs']['S']['position']
        odb_data[r]['regionType'] = data[r]['regionType']
        odb_data[r]['fieldOutputs'] = {}

        stress = np.array(data[r]['fieldOutputs']['S']['values'])
        try:
            strain = np.array(data[r]['fieldOutputs']['E']['values'])
        except:
            strain = np.array(data[r]['fieldOutputs']['LE']['values'])

        u = np.array(data[r]['fieldOutputs']['U']['values'])
        rf = np.array(data[r]['fieldOutputs']['RF']['values'])

        out_data[r] = {}
        out_data[r]['time'] = time
        out_data[r]['disp'] = np.mean(u[:, :, 1], axis=1)
        out_data[r]['force'] = np.sum(rf[:, :, 1], axis=1)

    return out_data


if __name__ == '__main__':
    print(simulation_3({}, [0, 1], [0, 100]))
