# -*- coding: utf-8 -*-
"""

"""

import pandas as pd
import os
import time
import json


def getFiles(path):
    fns = []
    for root, dirs, files in os.walk(path):
        for fn in files:
            fns.append([root, fn])
    return fns


def hasFile(filename, files):
    b = False
    if filename in files:
        b = True
    return b


def formatSize(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        print("传入的字节格式不对")
        return "Error"

    if kb >= 1024:
        M = kb / 1024
        if M >= 1024:
            G = M / 1024
            return "%.2fGB" % (G)
        else:
            return "%.2fMB" % (M)
    else:
        return "%.2fKB" % (kb)


def sub_dirs(path):
    sub_dirs = []
    for root, dirs, files in os.walk(path):
        if root != path:
            sub_dirs.append(int(root.replace(path, '').replace('\\', '')))
    return sub_dirs


def create_id(path):
    old_id_list = sub_dirs(path)
    if len(old_id_list) == 0:
        return 1
    else:
        return max(old_id_list)+1


def packing_models_detail(path):
    data_list = []
    model_id_list = sub_dirs(path)
    model_id_list.sort()
    for model_id in model_id_list[::-1]:
        status = {}
        status['model_id'] = model_id
        npy_file = os.path.join(path, str(model_id)+'\\'+'model.npy')
        args_file = os.path.join(path, str(model_id)+'\\'+'args.json')
        log_file = os.path.join(path, str(model_id)+'\\'+'model.log')
        msg_file = os.path.join(path, str(model_id)+'\\'+'model.msg')
        try:
            npy_modified_time = os.path.getmtime(npy_file)
            with open(args_file, 'r', encoding='utf-8') as f:
                args = json.load(f)
            with open(msg_file, 'r', encoding='utf-8') as f:
                message = json.load(f)
            status['args'] = str(args[:-1])
            status['size'] = str(message['size'])
            status['num_ball'] = message['num_ball']
            status['fraction'] = '%.4f' % message['fraction']
            status['npy_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(npy_modified_time))
            status['npy_size'] = formatSize(os.path.getsize(npy_file))
            status['download'] = "<a href='%s'>查看</a> | <a onclick=\"return confirm('确定删除模型?')\" href='%s'>删除</a>" % ('../view_packing_models/'+str(model_id), '../delete_packing_models/'+str(model_id))
        except:
            status['npy_time'] = 'None'
            status['npy_size'] = 'None'    
            status['download'] = 'None'
            status['args'] = 'None'
            status['size'] = 'None'
            status['num_ball'] = 'None'
            status['fraction'] = 'None'
            
        data_list.append(status)
    
    data = {
        "data": data_list
    }
    
    return data


if __name__ == '__main__':
    path = '..\\files\\propellant\\packing\\models\\'
    
    dir_status_detail(path,'#')