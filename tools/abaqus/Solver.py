# -*- coding: utf-8 -*-
"""

"""

import os
import threading
import psutil


class Solver:
    """
    Solver类，定义ABAQUS求解器执行参数。
    """

    def __init__(self, path, job='Job-1', user='user.for', cpus='1', clear=True):
        self.path = path
        self.job = job
        self.user = user
        self.cpus = cpus
        self.clear = clear

    def run(self):
        os.chdir(self.path)
        cmd = 'abaqus job=%s user=%s cpus=%s ask=off' % (self.job, self.user, self.cpus)
        result = os.popen(cmd)
        return result


    def clear(self):
        os.chdir(self.path)
        os.popen('del *.rpy.*')
        os.popen('del *.rpy')
        os.popen('del *.dmp')
        os.popen('del *.lck')
        os.popen('del fort.*')
        os.popen('del abaqus.*')
        os.popen('del *.exception')
        os.popen('del *.jnl')
        os.popen('del *.SMABulk')
        
        
    def terminate(self):
        os.chdir(self.path)
        cmd = 'abaqus terminate job=%s' % (self.job)
        result = os.popen(cmd)
        return result


    def get_sta(self):
        sta_file = os.path.join(self.path, '{}.sta'.format(self.job))
        with open(sta_file, 'r') as f:
            status = f.read()
        print(status)


if __name__ == '__main__':
    s = Solver(path=r'F:\Github\base\tools\abaqus\run', job='Job-1', user='umat_visco_maxwell_phasefield.for')
    result = s.run()
    for proc in psutil.process_iter():
        if  'standard.exe' in str(proc.name):
            print(proc)