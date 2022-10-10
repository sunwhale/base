# -*- coding: utf-8 -*-
"""

"""

import psutil
from Solver import Solver

if __name__ == '__main__':
    s1 = Solver(path='F:\\Github\\base\\tools\\abaqus\\run\\1', job='Job-1', user='umat_visco_maxwell_phasefield.for')
    s2 = Solver(path='F:\\Github\\base\\tools\\abaqus\\run\\2', job='Job-1', user='umat_visco_maxwell_phasefield.for')
    
    # s1.resume()
    # s2.suspend()
    
    print(s1.get_sta())