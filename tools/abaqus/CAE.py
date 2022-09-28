# -*- coding: utf-8 -*-
"""

"""

import os
import threading
import psutil


class CAE:
    """
    CAE类，定义ABAQUS前处理脚本
    """

    def __init__(self, path, noGUI_file):
        self.path = path
        self.noGUI_file = noGUI_file


    def run(self):
        os.chdir(self.path)
        cmd = 'abaqus cae noGUI=%s' % (self.noGUI_file)
        result = os.system(cmd)
        return result


if __name__ == '__main__':
    c = CAE(path=r'F:\Github\base\tools\abaqus\cae', noGUI_file='create_abaqus_cae_2D_phasefield')
    result = c.run()
