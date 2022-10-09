# -*- coding: utf-8 -*-
"""

"""

from Solver import Solver
import psutil


if __name__ == '__main__':
    for proc in psutil.process_iter():
        if  'standard.exe' in str(proc.name):
            print(proc)