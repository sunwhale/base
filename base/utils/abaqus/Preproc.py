# -*- coding: utf-8 -*-
"""

"""
import glob
import json
import os
import subprocess
import threading

from base.settings import ABAQUS


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


def write_log(proc, logfile):
    f = open(logfile, 'w', encoding='utf-8')
    for line in iter(proc.stdout.readline, b''):
        log = line.decode('UTF-8').replace('\n', '')
        f.write(log)
        f.flush()
        if not subprocess.Popen.poll(proc) is None:
            if line == "":
                break
    proc.stdout.close()
    f.close()


def files(curr_dir='.', ext='*.txt'):
    for i in glob.glob(os.path.join(curr_dir, ext)):
        yield i


def remove_files(rootdir, ext):
    for i in files(rootdir, ext):
        os.remove(i)


class Preproc:
    """
    Postproc类，定义ABAQUS后处理执行参数。
    """

    def __init__(self, path, script='script.py'):
        self.path = path
        self.script = script

    def read_msg(self):
        msg_file = os.path.join(self.path, '.preproc_msg')
        try:
            message = load_json(msg_file)
            self.script = message['script']
        except FileNotFoundError:
            message = {}
        return message

    def check_setting_files(self):
        setting_file = os.path.join(self.path, self.script)
        if not os.path.exists(setting_file):
            return False
        else:
            return True

    def clear(self):
        os.chdir(self.path)
        exts = [
            '*.rpy',
            '*.rpy.*',
        ]
        for ext in exts:
            remove_files(self.path, ext)

    def run(self):
        os.chdir(self.path)
        py_file = os.path.join(self.path, self.script)
        cmd = '%s cae noGui=\"%s\"' % (ABAQUS, py_file)
        print(cmd)
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=self.path)
        logfile = 'run.log'
        thread = threading.Thread(target=write_log, args=(proc, logfile))
        thread.start()
        return proc

    def get_run_log(self):
        log_file = os.path.join(self.path, 'run.log')
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                logs = f.read()
        else:
            logs = ''
        return logs

    def get_rpy(self):
        rpy_file = os.path.join(self.path, 'abaqus.rpy')
        if os.path.exists(rpy_file):
            with open(rpy_file, 'r') as f:
                rpy = f.read()
        else:
            rpy = ''
        return rpy

    def is_preproc_done(self):
        preproc_status = self.preproc_status()
        if preproc_status == 'Done' or preproc_status == 'Error':
            return True
        else:
            return False

    def preproc_status(self):
        """
        前处理的可能状态如下：
        ['None', 'Submitting', 'Running', 'Stopped', 'Completed']

        Returns
        -------
        preproc_status

        """
        preproc_status_file = os.path.join(self.path, '.preproc_status')

        if not os.path.exists(preproc_status_file):
            preproc_status = 'None'
            with open(preproc_status_file, 'w', encoding='utf-8') as f:
                f.write(preproc_status)
        else:
            with open(preproc_status_file, 'r', encoding='utf-8') as f:
                preproc_status = f.read()

        # Update solver_status based on the logs
        logs = self.get_rpy()
        if 'done' in logs:
            preproc_status = 'Completed'
        elif 'Error' in logs:
            preproc_status = 'Stopped'

        run_logs = self.get_run_log()
        if '不是' in run_logs:
            preproc_status = 'Stopped'

        return preproc_status


if __name__ == '__main__':
    p = Preproc(path='/files/abaqus/1/1', script='script.py')
    p.run()
