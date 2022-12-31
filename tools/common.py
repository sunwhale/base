# -*- coding: utf-8 -*-
"""

"""

import json
import os
import numpy as np


invariant_dict = {
    'MAGNITUDE': 'Magnitude',
    'MAX_INPLANE_PRINCIPAL': 'Max. In-Plane Principal',
    'MIN_INPLANE_PRINCIPAL': 'Min. In-Plane Principal',
    'OUTOFPLANE_PRINCIPAL': 'Out-of-Plane Principal',
    'MAX_PRINCIPAL': 'Max. Principal',
    'MID_PRINCIPAL': 'Mid. Principal',
    'MIN_PRINCIPAL': 'Min. Principal',
    'MISES': 'Mises',
    'TRESCA': 'Tresca',
    'PRESS': 'Pressure',
    'INV3': 'Third Invariant',
    }
    

def make_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def dump_json(file_name, data, encoding='utf-8'):
    """
    Write JSON data to file.
    """
    with open(file_name, 'w', encoding=encoding) as f:
        return json.dump(data, f, ensure_ascii=False)


def load_json(file_name, encoding='utf-8'):
    """
    Read JSON data from file.
    """
    with open(file_name, 'r', encoding=encoding) as f:
        return json.load(f)
