# -*- coding: utf-8 -*-
"""

"""

import psutil
from Solver import Solver

if __name__ == '__main__':
    for proc in psutil.process_iter():
        if  'standard.exe' in str(proc.name):
            print(proc)