# -*- coding: utf-8 -*-
"""

"""

import os
import subprocess
import threading
import json

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

    def __init__(self, path, job='Job-1', user='', cpus='1', is_clear=True):
        self.path = path
        self.job = job
        self.user = user
        self.cpus = cpus
        self.is_clear = is_clear

    def write_msg(self):
        message = {}
        message['job'] = self.job
        message['user'] = self.user
        message['cpus'] = self.cpus
        msg_file = os.path.join(self.path, '.msg')
        with open(msg_file, 'w', encoding='utf-8') as f:
            json.dump(message, f, ensure_ascii=False)

    def read_msg(self):
        msg_file = os.path.join(self.path, '.msg')
        try:
            with open(msg_file, 'r', encoding='utf-8') as f:
                message = json.load(f)
            self.job = message['job']
            self.user = message['user']
            self.cpus = message['cpus']
        except FileNotFoundError:
            message = {}
        return message

    def check_files(self):
        inp_file = os.path.join(self.path, '{}.inp'.format(self.job))
        user_file = os.path.join(self.path, self.user)
        if not os.path.exists(inp_file):
            return False
        if not os.path.exists(user_file):
            return False
        return True

    def run(self):
        os.chdir(self.path)
        if self.user == '':
            cmd = 'abaqus job=%s cpus=%s ask=off' % (self.job, self.cpus)
        else:
            cmd = 'abaqus job=%s user=%s cpus=%s ask=off' % (self.job, self.user, self.cpus)
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
            'del *.odb',
            'del *.odb_f',
            'del *.com',
            'del *.dat',
            'del *.prt',
            'del *.sim',
            'del *.sta',
            'del *.log'
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
        if os.path.exists(sta_file):
            with open(sta_file, 'r') as f:
                lines = f.readlines()
            status = []
            for line in lines:
                ls = line.split()
                if ls:
                    if is_number(ls[0]):
                        status.append(ls)
        else:
            status = []
        return status

    def get_log(self):
        log_file = os.path.join(self.path, '{}.log'.format(self.job))
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.read()
        else:
            logs = ''
        return logs

    def get_inp(self):
        inp_file = os.path.join(self.path, '{}.inp'.format(self.job))
        with open(inp_file, 'r') as f:
            inp = f.read()
        return inp

    def get_parameters(self):
        para_file = os.path.join(self.path, 'parameters.inp')
        with open(para_file, 'r') as f:
            para = f.read()
        return para

    def solver_status(self):
        """
        求解器的可能状态如下：
        ['Setting', 'Submitting', 'Running', 'Stopping', 'Stopped', 'Completed']

        Returns
        -------
        None.

        """
        status_file = os.path.join(self.path, '.status')
        # Obtain the initial solver_status
        if not os.path.exists(status_file):
            solver_status = 'Setting'
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write(solver_status)
        else:
            with open(status_file, 'r', encoding='utf-8') as f:
                solver_status = f.read()

        # Update solver_status based on the logs
        logs = self.get_log()
        if 'COMPLETED' in logs:
            solver_status = 'Completed'
        elif 'exited' in logs:
            solver_status = 'Stopped'
        elif 'Run standard.exe' in logs and solver_status != 'Stopping':
            solver_status = 'Running'

        with open(status_file, 'w', encoding='utf-8') as f:
            f.write(solver_status)

        return solver_status


if __name__ == '__main__':
    s = Solver(path='F:\\Github\\base\\files\\abaqus\\1\\1',
               job='Job-1', user='umat_visco_maxwell_phasefield.for')
    s.write_msg()
