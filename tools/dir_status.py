# -*- coding: utf-8 -*-
"""

"""

import json
import os
import time


def get_files(path):
    fns = []
    for root, dirs, files in os.walk(path):
        for fn in files:
            fns.append([root, fn])
    return fns


def has_file(filename, files):
    b = False
    if filename in files:
        b = True
    return b


def format_size(size_in_bytes):
    try:
        size_in_bytes = float(size_in_bytes)
        kb = size_in_bytes / 1024
    except TypeError:
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


def sub_dirs_int(path):
    try:
        sub_dirs = [int(sub_dir) for sub_dir in next(os.walk(path))[1]]
    except StopIteration:
        sub_dirs = []
    return sorted(sub_dirs)


def get_current_dir_int(path):
    abs_dir = next(os.walk(path))[0].split(os.sep)
    if abs_dir[-1] == '':
        return abs_dir[-2]
    else:
        return abs_dir[-1]


def sub_dirs(path):
    sub_dirs = next(os.walk(path))[1]
    return sub_dirs


def create_id(path):
    old_id_list = sub_dirs_int(path)
    if len(old_id_list) == 0:
        return 1
    else:
        return max(old_id_list)+1
    
def files_in_dir(path):
    file_list = []
    for filename in next(os.walk(path))[2]:
        file = {}
        file['name'] = filename
        file['size'] = file_size(os.path.join(path, filename))
        file['time'] = file_time(os.path.join(path, filename))
        file_list.append(file)    
    return file_list
    

def file_time(file):
    modified_time = os.path.getmtime(file)
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(modified_time))


def file_size(file):
    return format_size(os.path.getsize(file))


def get_model_status(path, model_id):
    npy_file = os.path.join(path, str(model_id), 'model.npy')
    msg_file = os.path.join(path, str(model_id), 'model.msg')
    args_file = os.path.join(path, str(model_id), 'args.json')
    log_file = os.path.join(path, str(model_id), 'model.log')
    status = {}
    status['model_id'] = model_id
    try:
        with open(msg_file, 'r', encoding='utf-8') as f:
            message = json.load(f)
        with open(args_file, 'r', encoding='utf-8') as f:
            args = json.load(f)
            status['args'] = str(args)
        with open(log_file, 'r', encoding='utf-8') as f:
            status['log'] = f.read()        
        status['npy_time'] = file_time(npy_file)
        status['npy_size'] = file_size(npy_file)
        status['size'] = str(message['size'])
        status['gap'] = message['gap']
        status['num_ball'] = message['num_ball']
        status['fraction'] = '%.4f' % message['fraction']
        status['operation'] = "<a href='%s'>查看</a> | <a href='%s'>子模型</a> | <a onclick=\"return confirm('确定删除模型?')\" href='%s'>删除</a>" % ('../view_packing_model/'+str(model_id), '../manage_packing_submodels/'+str(model_id), '../delete_packing_models/'+str(model_id))
    except FileNotFoundError:
        for key in ['npy_time', 'npy_size', 'size', 'gap', 'num_ball', 'fraction']:
            status[key] = 'None'
        status['operation'] = "<a onclick=\"return confirm('确定删除模型?')\" href='%s'>删除</a>" % ('../delete_packing_models/'+str(model_id))
    return status


def get_submodel_status(path, model_id, submodel_id):
    npy_file = os.path.join(path, str(model_id), str(submodel_id), 'model.npy')
    msg_file = os.path.join(path, str(model_id), str(submodel_id), 'model.msg')
    args_file = os.path.join(path, str(model_id), str(submodel_id), 'args.json')
    status = {}
    status['model_id'] = model_id
    status['submodel_id'] = submodel_id
    try:
        with open(msg_file, 'r', encoding='utf-8') as f:
            message = json.load(f)
        with open(args_file, 'r', encoding='utf-8') as f:
            args = json.load(f)
            status['args'] = str(args)
        status['npy_time'] = file_time(npy_file)
        status['npy_size'] = file_size(npy_file)
        status['ndiv'] = message['ndiv']
        status['location'] = str(message['location'])
        status['subsize'] = str(message['subsize'])
        status['gap'] = message['gap']
        status['num_ball'] = message['num_ball']
        status['fraction'] = '%.4f' % message['fraction']
        status['operation'] = "<a href='%s'>查看</a>" % ('../view_packing_submodel/'+str(model_id)+'/'+str(submodel_id))
    except FileNotFoundError:
        for key in ['npy_time', 'npy_size', 'ndiv', 'location', 'subsize', 'gap', 'num_ball', 'fraction', 'operation']:
            status[key] = 'None'
    return status


def get_mesh_status(path, model_id, submodel_id):
    inp_file = os.path.join(path, str(model_id), str(submodel_id), 'Model-1.inp')
    args_file = os.path.join(path, str(model_id), str(submodel_id), 'args.json')
    msg_file = os.path.join(path, str(model_id), str(submodel_id), 'model.msg')
    status = {}
    status['model_id'] = model_id
    status['submodel_id'] = submodel_id
    if os.path.exists(inp_file):
        with open(args_file, 'r', encoding='utf-8') as f:
            args = json.load(f)
        with open(msg_file, 'r', encoding='utf-8') as f:
            message = json.load(f)
        status['args'] = str(args)
        status['gap'] = message['gap']
        status['nodes_number'] = message['nodes_number']
        status['elements_number'] = message['elements_number']
        status['node_shape'] = message['node_shape']
        status['dimension'] = message['dimension']
        status['size'] = message['size']
        status['element_type'] = message['element_type']        
        status['inp_time'] = file_time(inp_file)
        status['inp_size'] = file_size(inp_file)
    return status        
        

def get_doc_status(path, doc_id):
    md_file = os.path.join(path, str(doc_id), 'article.md')
    msg_file = os.path.join(path, str(doc_id), 'article.msg')
    status = {}
    if os.path.exists(md_file):
        status['doc_id'] = doc_id
        try:
            with open(msg_file, 'r', encoding='utf-8') as f:
                message = json.load(f)
            status['title'] = message['title']
            status['md_time'] = file_time(md_file)
            status['operation'] = "<a href='%s'>查看</a> | <a href='%s'>编辑</a> | <a onclick=\"return confirm('确定删除模型?')\" href='%s'>删除</a>" % ('../viewmd/'+str(doc_id), '../editmd/'+str(doc_id), '../deletemd/'+str(doc_id))
        except FileNotFoundError:
            for key in ['title', 'md_time']:
                status[key] = 'None'
            status['operation'] = "<a href='%s'>查看</a> | <a href='%s'>编辑</a> | <a onclick=\"return confirm('确定删除模型?')\" href='%s'>删除</a>" % ('../viewmd/'+str(doc_id), '../editmd/'+str(doc_id), '../deletemd/'+str(doc_id))
    return status 


def get_sheet_status(path, sheet_id):
    sheet_file = os.path.join(path, str(sheet_id), 'sheet.json')
    msg_file = os.path.join(path, str(sheet_id), 'sheet.msg')
    status = {}
    if os.path.exists(sheet_file):
        status['sheet_id'] = sheet_id
        try:
            with open(msg_file, 'r', encoding='utf-8') as f:
                message = json.load(f)
            status['title'] = message['title']
            status['sheet_time'] = file_time(sheet_file)
            status['operation'] = "<a href='%s'>查看</a> | <a href='%s'>编辑</a> | <a onclick=\"return confirm('确定删除模型?')\" href='%s'>删除</a>" % ('../view_sheet/'+str(sheet_id), '../edit_sheet/'+str(sheet_id), '../delete_sheet/'+str(sheet_id))
        except FileNotFoundError:
            for key in ['title', 'sheet_time']:
                status[key] = 'None'
            status['operation'] = "<a href='%s'>查看</a> | <a href='%s'>编辑</a> | <a onclick=\"return confirm('确定删除模型?')\" href='%s'>删除</a>" % ('../view_sheet/'+str(sheet_id), '../edit_sheet/'+str(sheet_id), '../delete_sheet/'+str(sheet_id))
    return status 


def get_project_status(path, project_id):
    msg_file = os.path.join(path, str(project_id), 'project.msg')
    status = {}
    if os.path.exists(msg_file):
        status['project_id'] = project_id
        try:
            with open(msg_file, 'r', encoding='utf-8') as f:
                message = json.load(f)
            status['name'] = message['name']
            status['project_time'] = file_time(msg_file)
            status['log'] = message['log']
            status['operation'] = "<a href='%s'>查看</a> | <a href='%s'>编辑</a> | <a onclick=\"return confirm('确定删除模型?')\" href='%s'>删除</a>" % ('view_project/'+str(project_id), 'edit_project/'+str(project_id), 'delete_project/'+str(project_id))
        except FileNotFoundError:
            for key in ['title', 'project_time', 'log']:
                status[key] = 'None'
            status['operation'] = "<a href='%s'>查看</a> | <a href='%s'>编辑</a> | <a onclick=\"return confirm('确定删除模型?')\" href='%s'>删除</a>" % ('view_project/'+str(project_id), 'edit_project/'+str(project_id), 'delete_project/'+str(project_id))
    return status 


def get_job_status(path, project_id, job_id):
    inp_file = os.path.join(path, str(project_id), str(job_id), 'Job-1.inp')
    status = {}
    status['project_id'] = project_id
    status['job_id'] = job_id
    try:
        status['inp_time'] = file_time(inp_file)
        status['inp_size'] = file_size(inp_file)
        status['operation'] = "<a href='%s'>查看</a>" % ('../view_job/'+str(project_id)+'/'+str(job_id))
    except FileNotFoundError:
        for key in ['npy_time', 'npy_size', 'ndiv', 'location', 'subsize', 'gap', 'num_ball', 'fraction', 'operation']:
            status[key] = 'None'
    return status


def packing_models_detail(path):
    data_list = []
    model_id_list = sub_dirs_int(path)
    for model_id in model_id_list:
        status = get_model_status(path, model_id)
        data_list.append(status)

    data = {
        "data": data_list
    }

    return data


def packing_submodels_detail(path, model_id):
    data_list = []
    submodel_id_list = sub_dirs_int(os.path.join(path, str(model_id)))
    for submodel_id in submodel_id_list:
        status = get_submodel_status(path, model_id, submodel_id)
        data_list.append(status)
        
    data = {
        "data": data_list
    }

    return data


def docs_detail(path):
    data_list = []
    doc_id_list = sub_dirs_int(path)
    for doc_id in doc_id_list:
        status = get_doc_status(path, doc_id)
        data_list.append(status)
        
    data = {
        "data": data_list
    }

    return data


def sheets_detail(path):
    data_list = []
    sheet_id_list = sub_dirs_int(path)
    for sheet_id in sheet_id_list:
        status = get_sheet_status(path, sheet_id)
        data_list.append(status)
        
    data = {
        "data": data_list
    }

    return data


def projects_detail(path):
    data_list = []
    project_id_list = sub_dirs_int(path)
    for project_id in project_id_list:
        status = get_project_status(path, project_id)
        data_list.append(status)
        
    data = {
        "data": data_list
    }

    return data


def project_jobs_detail(path, project_id):
    data_list = []
    job_id_list = sub_dirs_int(os.path.join(path, str(project_id)))
    for job_id in job_id_list:
        status = get_job_status(path, project_id, job_id)
        data_list.append(status)
        
    data = {
        "data": data_list
    }

    return data


if __name__ == '__main__':
    path = '..\\files\\abaqus\\run\\1\\'
    print(files_in_dir(path))
