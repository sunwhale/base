# -*- coding: utf-8 -*-
"""

"""

import json
import os
import subprocess

import psutil


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


class Postproc:
    """
    Postproc类，定义ABAQUS后处理执行参数。
    """

    def __init__(self, path, job='Job-1'):
        self.path = path
        self.job = job

    def read_msg(self):
        msg_file = os.path.join(self.path, '.msg')
        try:
            message = load_json(msg_file)
            self.job = message['job']
        except FileNotFoundError:
            message = {}
        return message

    def check_files(self):
        odb_file = os.path.join(self.path, '{}.odb'.format(self.job))
        if not os.path.exists(odb_file):
            return False
        else:
            return True

    def prescan_odb(self):
        os.chdir(self.path)
        cmd = 'abaqus viewer noGui=%s -- %s.odb %s' % (
            'F:\\Github\\base\\tools\\abaqus\\prescan_odb.py', self.job, 'prescan_odb.json')
        proc = subprocess.Popen(cmd, shell=True)
        return proc

    def get_rpy(self):
        rpy_file = os.path.join(self.path, 'abaqus.rpy')
        if os.path.exists(rpy_file):
            with open(rpy_file, 'r') as f:
                rpy = f.read()
        else:
            rpy = ''
        return rpy

    def prescan_status(self):
        """
        求解器的可能状态如下：
        ['No odb file', 'Ready to prescan', 'Submitting', 'Scanning', 'Stopped', 'Completed']

        Returns
        -------
        prescan_status

        """
        status_file = os.path.join(self.path, '.prescan_status')
        
        odb_file = os.path.join(self.path, '{}.odb'.format(self.job))
        if not os.path.exists(odb_file):
            prescan_status = 'No odb file'
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write(prescan_status)
            return prescan_status

        if not os.path.exists(status_file):
            prescan_status = 'Ready to prescan'
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write(prescan_status)
        else:
            with open(status_file, 'r', encoding='utf-8') as f:
                prescan_status = f.read()

        rpy = self.get_rpy()
        if 'done' in rpy:
            prescan_status = 'Completed'
        elif 'exited' in rpy:
            prescan_status = 'Stopped'
        elif 'Run standard' in rpy and prescan_status != 'Stopping':
            prescan_status = 'Scanning'

        if prescan_status not in ['No odb file', 'Ready to prescan', 'Submitting', 'Scanning', 'Stopped', 'Completed']:
            prescan_status = 'Ready to prescan'

        with open(status_file, 'w', encoding='utf-8') as f:
            f.write(prescan_status)

        return prescan_status


if __name__ == '__main__':
    s = Solver(path='F:\\Github\\base\\files\\abaqus\\1\\1',
               job='Job-1', user='umat_visco_maxwell_phasefield.for')
    s.parameters_to_json()
