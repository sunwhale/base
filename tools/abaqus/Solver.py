# -*- coding: utf-8 -*-
"""

"""

import os
import subprocess
import threading

import psutil
import pandas as pd


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
 
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
 
    return False


class Solver:
    """
    Solver类，定义ABAQUS求解器执行参数。
    """

    def __init__(self, path, job='Job-1', user='user.for', cpus='1', is_clear=True):
        self.path = path
        self.job = job
        self.user = user
        self.cpus = cpus
        self.is_clear = is_clear

    def run(self):
        os.chdir(self.path)
        cmd1 = '\"C:\\Program Files (x86)\\Microsoft Visual Studio\\2019\\Community\\VC\\Auxiliary\\Build\\vcvarsall.bat\" x86 amd64'
        cmd2 = '\"C:\\Program Files (x86)\\IntelSWTools\\compilers_and_libraries_2020.0.166\\windows\\bin\\ifortvars.bat\" intel64 vs2019'
        cmd3 = 'abaqus job=%s user=%s cpus=%s ask=off' % (
            self.job, self.user, self.cpus)
        cmd = '%s && %s && %s' % (cmd1, cmd2, cmd3)
        proc = subprocess.Popen(cmd, shell=True)
        return proc

    def clear(self):
        os.chdir(self.path)
        cmds = [
            'del *.rpy.*',
            'del *.dmp',
            'del *.lck',
            'del fort.*',
            'del abaqus.*',
            'del *.exception',
            'del *.jnl',
            'del *.SMABulk',
            'del *.odb'
        ]
        for cmd in cmds:
            try:
                proc = subprocess.Popen(cmd, shell=True)
                print('proc:', proc)
            except subprocess.CalledProcessError as exc:
                print('returncode:', exc.returncode)
                print('cmd:', exc.cmd)
                print('output:', exc.output)

    def terminate(self):
        os.chdir(self.path)
        cmd = 'abaqus terminate job=%s' % (self.job)
        proc = subprocess.Popen(cmd, shell=True)
        return proc

    def suspend(self):
        os.chdir(self.path)
        cmd = 'abaqus suspend job=%s' % (self.job)
        proc = subprocess.Popen(cmd, shell=True)
        return proc

    def resume(self):
        os.chdir(self.path)
        cmd = 'abaqus resume job=%s' % (self.job)
        proc = subprocess.Popen(cmd, shell=True)
        return proc

    def get_sta(self):
        sta_file = os.path.join(self.path, '{}.sta'.format(self.job))
        with open(sta_file, 'r') as f:
            lines = f.readlines()
        status = []
        for line in lines:
            ls = line.split()
            if ls:
                if is_number(ls[0]):
                    status.append(ls)
        return status

    def get_log(self):
        log_file = os.path.join(self.path, '{}.log'.format(self.job))
        with open(log_file, 'r') as f:
            logs = f.read()
        return logs

    def get_inp(self):
        inp_file = os.path.join(self.path, '{}.inp'.format(self.job))
        with open(inp_file, 'r') as f:
            inp = f.read()
        return inp

if __name__ == '__main__':
    s = Solver(path='F:\\Github\\base\\files\\abaqus\\run\\1',
               job='Job-1', user='umat_visco_maxwell_phasefield.for')
    s.get_log()
