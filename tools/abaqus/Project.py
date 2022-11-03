# -*- coding: utf-8 -*-
"""

"""

import os
import shutil
import subprocess

from Solver import Solver


class Template:
    """
    Template类，用于相同input模板的计算。
    """

    def __init__(self, name, path, inpfile, userfile, otherfiles=[]):
        self.name = name
        self.path = path
        self.inpfile = inpfile
        self.userfile = userfile
        self.otherfiles = otherfiles
        self.jobs = []

    def create_directory(self, path):
        if not os.path.isdir(path):
            os.makedirs(path)
            print('Create new directory:', path)

    def copy_files(self, path):
        file = os.path.join(self.path, self.inpfile)
        shutil.copy(file, path)
        print('Copy:', file)
        file = os.path.join(self.path, self.userfile)
        shutil.copy(file, path)
        print('Copy:', file)
        for file in self.otherfiles:
            shutil.copy(file, path)
            print('Copy:', file)

    def create_parameters_input(self, name='parameters.inp', columns=[], parameters=[]):
        output_filename = self.path + name
        outfile = open(output_filename, 'w')

        outfile.write('*Parameter\n')
        for i in range(len(columns)):
            outfile.write('%s = %s\n' % (columns[i], parameters[i]))
        outfile.close()
        print('Create ', output_filename)

    def sub_dirs_int(self):
        try:
            sub_dirs = [int(sub_dir) for sub_dir in next(os.walk(self.path))[1]]
        except StopIteration:
            sub_dirs = []
        return sorted(sub_dirs)
    
    def create_job_id(self):
        old_id_list = self.sub_dirs_int()
        if len(old_id_list) == 0:
            return 1
        else:
            return max(old_id_list)+1
        
    def create_job(self):
        job_id = self.create_job_id()
        job_path = os.path.join(self.path, str(job_id))
        self.create_directory(job_path)
        self.copy_files(job_path)
        return job_path
        
    
if __name__ == '__main__':
    t = Template(name='test', path='F:\\Github\\base\\tools\\abaqus\\run\\',
               inpfile='Job-1.inp', userfile='umat_visco_maxwell_phasefield.for')
    print(t.sub_dirs_int())
    print(t.create_job())
