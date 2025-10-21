# -*- coding: utf-8 -*-
"""

"""
from pathlib import Path

import numpy as np
from numpy import ndarray
from pyfem.Job import Job
from pyfem.database.ODB import ODB
from pyfem.io.BaseIO import BaseIO


def get_simulation(parameters: dict, strain: ndarray, time: ndarray, job_path: Path) -> tuple[ndarray, ndarray, ndarray]:
    """
    计算耦合相场断裂的广义Maxwell模型的有限元解
    """
    job = Job(job_path)

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
    odb.load_hdf5(str(job_path.with_suffix('.hdf5')))

    t = []
    e11 = []
    s11 = []
    for frame in odb.steps['Step-1']['frames']:
        t.append(frame['frameValue'])
        e11.append(frame['fieldOutputs']['E11']['bulkDataBlocks'][0])
        s11.append(frame['fieldOutputs']['S11']['bulkDataBlocks'][0])

    return np.array(e11), np.array(s11), np.array(t)
