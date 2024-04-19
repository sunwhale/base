# -*- coding: utf-8 -*-
"""

"""
import glob
import json
import os
import signal
import subprocess
import sys
import threading

import chardet

from base.settings import ABAQUS

WIN = sys.platform.startswith('win')


def files(curr_dir='.', ext='*.txt'):
    for i in glob.glob(os.path.join(curr_dir, ext)):
        yield i


def remove_files(rootdir, ext):
    for i in files(rootdir, ext):
        os.remove(i)


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


def write_log(proc, logfile):
    f = open(logfile, 'w', encoding='utf-8')
    for line in iter(proc.stdout.readline, b''):
        result = chardet.detect(line)
        encoding = result['encoding']
        if result['encoding'] is not None:
            log = line.decode(encoding).replace('\n', '')
            f.write(log)
            f.flush()
            if not subprocess.Popen.poll(proc) is None:
                if line == "":
                    break
    proc.stdout.close()
    f.close()


class Solver:
    """
    Solver类，定义PYFEM求解器执行参数。
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
        msg_file = os.path.join(self.path, '.job_msg')
        with open(msg_file, 'w', encoding='utf-8') as f:
            json.dump(message, f, ensure_ascii=False)

    def read_msg(self):
        msg_file = os.path.join(self.path, '.job_msg')
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
        inp_file = os.path.join(self.path, f'{self.job}.toml')
        print(inp_file)
        user_file = os.path.join(self.path, self.user)
        if not os.path.exists(inp_file):
            return False
        if self.user == '':
            return True
        elif not os.path.exists(user_file):
            return False
        return True

    def preproc(self):
        os.chdir(self.path)
        cmd = 'python edit_amplitude.py'
        proc = subprocess.Popen(cmd, shell=True)
        return proc

    def run(self):
        """

        """
        os.chdir(self.path)
        self.preproc()
        if self.user == '':
            cmd = f'pyfem -i {self.job}.toml'
        else:
            cmd = f'C:\\Users\\SunJingyu\\.conda\\envs\\pyfem311\\python.exe F:\\GitHub\\pyfem\\app.py -i {self.job}.toml'
        print(cmd)
        if WIN:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=self.path)
        else:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, cwd=self.path, preexec_fn=os.setsid)
        logfile = 'run.log'
        thread = threading.Thread(target=write_log, args=(proc, logfile))
        thread.start()
        return proc

    def clear(self):
        os.chdir(self.path)
        exts = [
            '*.pvd',
            '*.log',
            '*.vtu',
            '*.sta',
            '*.lck',
        ]
        for ext in exts:
            remove_files(self.path, ext)
        remove_files(self.path, '{}.msg'.format(self.job))
        remove_files(self.path, '{}.odb'.format(self.job))
        remove_files(self.path, '{}.npz'.format(self.job))

    def terminate(self, pid):
        os.chdir(self.path)
        os.killpg(pid, signal.SIGTERM)

    def suspend(self):
        os.chdir(self.path)
        cmd = '%s suspend job=%s' % (ABAQUS, self.job)
        proc = subprocess.Popen(cmd, shell=True)
        return proc

    def resume(self):
        os.chdir(self.path)
        cmd = '%s resume job=%s' % (ABAQUS, self.job)
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
        if os.path.exists(inp_file):
            with open(inp_file, 'r') as f:
                inp = f.read()
        else:
            inp = ''
        return inp

    def get_parameters(self):
        para_file = os.path.join(self.path, 'parameters.toml')
        if os.path.exists(para_file):
            with open(para_file, 'r', encoding='utf-8') as f:
                para = f.read()
        else:
            para = ''
        return para

    def get_run_log(self):
        log_file = os.path.join(self.path, 'run.log')
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                logs = f.read()
        else:
            logs = ''
        return logs

    def save_parameters(self, para):
        para_file = os.path.join(self.path, 'parameters.toml')
        para = para.replace('\r', '')
        with open(para_file, 'w', encoding='utf-8') as f:
            f.write(para)

    def parameters_to_json(self):
        para_file = os.path.join(self.path, 'parameters.toml')
        if os.path.exists(para_file):
            with open(para_file, 'r', encoding='utf-8') as f:
                para = f.readlines()
        else:
            para = ''
        para_dict = {}
        for p in para:
            if '=' in p:
                l = p.strip().replace(' ', '').split('=')
                para_dict[l[0]] = l[1]
        para_json_file = os.path.join(self.path, 'parameters.json')
        with open(para_json_file, 'w', encoding='utf-8') as f:
            json.dump(para_dict, f, ensure_ascii=False)

    def parameter_keys(self):
        para_file = os.path.join(self.path, 'parameters.toml')
        if os.path.exists(para_file):
            with open(para_file, 'r', encoding='utf-8') as f:
                para = f.readlines()
        else:
            para = ''
        para_dict = {}
        for p in para:
            if '=' in p:
                l = p.strip().replace(' ', '').split('=')
                para_dict[l[0]] = l[1]
        return para_dict.keys()

    def is_done(self):
        solver_status = self.solver_status()
        if solver_status == 'Stopped' or solver_status == 'Completed':
            return True
        else:
            return False

    def solver_status(self):
        """
        求解器的可能状态如下：
        ['Setting', 'Submitting', 'Running', 'Stopping', 'Stopped', 'Completed']

        Returns
        -------
        None.

        """
        status_file = os.path.join(self.path, '.solver_status')
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
        elif 'EXITED' in logs:
            solver_status = 'Stopped'
        elif 'RUNNING' in logs and solver_status != 'Stopping':
            solver_status = 'Running'

        run_logs = self.get_run_log()
        if 'Error' in run_logs or '找不到' in run_logs:
            solver_status = 'Stopped'

        # 如果发生异常，则赋予默认值'Setting'
        if solver_status not in ['Setting', 'Submitting', 'Running', 'Stopping', 'Stopped', 'Completed']:
            solver_status = 'Setting'

        with open(status_file, 'w', encoding='utf-8') as f:
            f.write(solver_status)

        return solver_status

    def button(self, project_id, job_id):
        solver_status = self.solver_status()
        button = ""
        button += "<a class='btn btn-primary btn-sm' href='%s'>查看</a> " % (
                '../view_job/' + str(project_id) + '/' + str(job_id))
        button += "<a class='btn btn-primary btn-sm' onclick=\"return confirm('确定删除模型?')\" href='%s'>删除</a> " % (
                '../delete_job/' + str(project_id) + '/' + str(job_id))
        if solver_status == 'Submitting' or solver_status == 'Running' or solver_status == 'Pause' or solver_status == 'Stopping':
            button += "<button class='btn btn-secondary btn-sm' disabled='disabled'>计算</button> "
        else:
            button += "<a href='%s' class='btn btn-success btn-sm'>计算</a> " % (
                    '../run_job/' + str(project_id) + '/' + str(job_id))
        if solver_status == 'Running':
            button += "<a href='#' class='btn btn-warning btn-sm'>暂停</a> "
        else:
            button += "<button class='btn btn-secondary btn-sm' disabled='disabled'>暂停</button> "
        if solver_status == 'Pause':
            button += "<a href='#'' class='btn btn-info btn-sm'>继续</a> "
        else:
            button += "<button class='btn btn-secondary btn-sm' disabled='disabled'>继续</button> "
        if solver_status == 'Running':
            button += "<a href='%s' class='btn btn-danger btn-sm'>终止</a>" % (
                    '../terminate_job/' + str(project_id) + '/' + str(job_id))
        else:
            button += "<button class='btn btn-secondary btn-sm' disabled='disabled'>终止</button>"
        return button


if __name__ == '__main__':
    s = Solver(path='F:/Github/base/files/pyfem/1/2', job='Job-1', user='')
    s.clear()
    proc = s.run()
