# -*- coding: utf-8 -*-
"""

"""

import os
import shutil
import subprocess


class Template:
    """
    Template类，用于相同input模板的计算。
    """

    def __init__(self, name, path, inpfile, userfile, otherfiles):
        self.name = name
        self.path = path
        self.inpfile = inpfile
        self.userfile = userfile
        self.jobs = []

    def create_directory(self):
        if not os.path.isdir(self.path):
            os.makedirs(self.path)
            print('Create new directory:', self.path)

    def copy_files(self):
        for file in files:
            shutil.copy(file, self.path)
            print('Copy:', file)

    def create_parameters_input(self, name='parameters.inp', columns=[], parameters=[]):
        output_filename = self.abaqus_work_path + name
        outfile = open(output_filename, 'w')

        outfile.write('*Parameter\n')
        for i in range(len(columns)):
            outfile.write('%s = %s\n' % (columns[i], parameters[i]))
        outfile.close()
        print('Create ', output_filename)

    def create_job(self):



if __name__ == '__main__':
    s = Solver(path='F:\\Github\\base\\tools\\abaqus\\run\\1',
               job='Job-1', user='umat_visco_maxwell_phasefield.for')
    s.run()
