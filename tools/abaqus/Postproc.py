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

    def has_odb(self):
        odb_file = os.path.join(self.path, '{}.odb'.format(self.job))
        if not os.path.exists(odb_file):
            return False
        else:
            return True

    def check_setting_files(self):
        setting_file = os.path.join(self.path, 'odb_to_npz.json')
        if not os.path.exists(setting_file):
            return False
        else:
            return True

    def prescan_odb(self):
        os.chdir(self.path)
        py_file = os.path.join(os.path.dirname(__file__), 'prescan_odb.py')
        json_file = os.path.join(self.path, 'prescan_odb.json')
        if os.path.exists(json_file):
            os.remove(json_file)
        cmd = 'abaqus viewer noGui=%s -- %s.odb %s' % (
            py_file, self.job, 'prescan_odb.json')
        proc = subprocess.Popen(cmd, shell=True)
        return proc

    def odb_to_npz(self):
        os.chdir(self.path)
        py_file = os.path.join(os.path.dirname(__file__), 'odb_to_npz.py')
        npz_file = os.path.join(self.path, '{}.npz'.format(self.job))
        if os.path.exists(npz_file):
            os.remove(npz_file)
        cmd = 'abaqus viewer noGui=%s -- %s' % (py_file, 'odb_to_npz.json')
        proc = subprocess.Popen(cmd, shell=True)
        return proc

    def print_figure(self):
        os.chdir(self.path)
        py_file = os.path.join(os.path.dirname(__file__), 'print_figure.py')
        odb_file = os.path.join(self.path, '{}.odb'.format(self.job))
        cmd = 'abaqus viewer noGui=%s -- %s' % (py_file, 'print_figure.json')
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

    def odb_to_npz_status(self):
        odb_to_npz_status_file = os.path.join(self.path, '.odb_to_npz_status')
        if os.path.exists(odb_to_npz_status_file):
            with open(odb_to_npz_status_file, 'r', encoding='utf-8') as f:
                odb_to_npz_status = f.read()
        else:
            odb_to_npz_status = 'None'
        return odb_to_npz_status

    def is_odb_to_npz_done(self):
        odb_to_npz_status = self.odb_to_npz_status()
        if odb_to_npz_status == 'Done' or odb_to_npz_status == 'Error':
            return True
        else:
            return False

    def prescan_status(self):
        """
        后处理的可能状态如下：
        ['None', 'Submitting', 'Scanning', 'Error', 'Done']

        Returns
        -------
        prescan_status

        """
        status_file = os.path.join(self.path, '.prescan_status')

        if not os.path.exists(status_file):
            prescan_status = 'None'
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write(prescan_status)
        else:
            with open(status_file, 'r', encoding='utf-8') as f:
                prescan_status = f.read()

        return prescan_status


if __name__ == '__main__':
    p = Postproc(path='F:\\Github\\base\\files\\abaqus\\1\\1',
                 job='Job-1')
    p.prescan_odb()
