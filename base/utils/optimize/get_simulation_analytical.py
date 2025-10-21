# -*- coding: utf-8 -*-
"""

"""

import numpy as np
from numpy import ndarray


def get_simulation(parameters: dict, strain: ndarray, time: ndarray) -> tuple[ndarray, ndarray, ndarray]:
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
