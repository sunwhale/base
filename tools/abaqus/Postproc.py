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
            with open(msg_file, 'r', encoding='utf-8') as f:
                message = json.load(f)
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
        cmd = 'abaqus viewer noGui=%s -- %s.odb %s' % ('F:\\Github\\base\\tools\\abaqus\\prescan_odb.py', self.job, 'prescan_odb.json')
        proc = subprocess.Popen(cmd, shell=True)
        return proc


if __name__ == '__main__':
    s = Solver(path='F:\\Github\\base\\files\\abaqus\\1\\1',
               job='Job-1', user='umat_visco_maxwell_phasefield.for')
    s.parameters_to_json()
