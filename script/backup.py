# -*- coding: utf-8 -*-
"""

"""
import hashlib
import os
import shutil
import time
import zipfile
from datetime import datetime


def calculate_checksum(file_path):
    # 创建一个hash对象
    hash_object = hashlib.md5()

    # 打开文件并逐块读取内容进行更新
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_object.update(chunk)

    # 计算并返回文件的校验和值
    return hash_object.hexdigest()


def check_project_job_files(project_path, job_path, ignore_files):
    for f in files_in_dir(project_path):
        for ignore_file in ignore_files:
            if ignore_file in f['name']:
                break
            else:
                project_file_path = os.path.join(project_path, f['name'])
                job_file_path = os.path.join(job_path, f['name'])
                if not (os.path.exists(job_file_path) and calculate_checksum(project_file_path) == calculate_checksum(job_file_path)):
                    return False
    return True


def get_path_uuid(path):
    server_uuid = []
    for d0 in sub_dirs(path):
        for d1 in sub_dirs(os.path.join(path, d0)):
            for file in files_in_dir(os.path.join(path, d0, d1)):
                if file['name'] == '.uuid':
                    uuid_file = os.path.join(path, d0, d1, '.uuid')
                    with open(uuid_file, "r") as f:
                        uuid_str = f.read()
                        server_uuid.append([d0, int(d1), uuid_str])
    return server_uuid


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
        return max(old_id_list) + 1


def files_in_dir(path):
    file_list = []
    for filename in sorted(next(os.walk(path))[2]):
        file = {}
        file['name'] = filename
        file['size'] = file_size(os.path.join(path, filename))
        file['time'] = file_time(os.path.join(path, filename))
        file_list.append(file)
    return file_list


def subpaths_in_dir(path):
    subpath_list = []
    for subpath_name in sorted(next(os.walk(path))[1]):
        subpath = {}
        subpath['name'] = subpath_name
        subpath['time'] = file_time(os.path.join(path, subpath_name))
        subpath_list.append(subpath)
    return subpath_list


def file_time(file):
    if os.path.exists(file):
        modified_time = os.path.getmtime(file)
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(modified_time))
    else:
        return 'None'


def file_size(file):
    if os.path.exists(file):
        return format_size(os.path.getsize(file))
    else:
        return 'None'


allowed_suffix_dict = {
    'abaqus': ['.project_msg', '.cae', '.inp', '.for', '.FOR', '.json', '.abaqus_msg', '.job_msg', '.uuid'],
    'abaqus_template': ['.inp', '.for', '.FOR', '.json', '.template_msg', '.job_msg', '.uuid'],
    'abaqus_pre': ['.inp', '.for', '.FOR', '.py', '.json', '.preproc_msg', '.uuid'],
    'virtual': ['.inp', '.for', '.json', '.abaqus_msg', '.job_msg', '.uuid'],
    'experiment': ['.*'],
    'doc': ['.*'],
    'sheet': ['.*'],
    'packing': ['.*'],
    'pyfem': ['.toml', '.inp', '.msh', '.json', '.project_msg', '.job_msg', '.uuid']
}


def zip_folder(folder_path, zip_path):
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                print(arcname)
                zipf.write(file_path, arcname)


if __name__ == '__main__':
    path = '/home/dell/www/base/files'
    backup_root_path = '/home/dell/www/base/backup'
    backup_path = os.path.join(backup_root_path, str(datetime.now().date()))
    os.makedirs(backup_path, exist_ok=True)

    for d0 in sub_dirs(path):
        if d0 in allowed_suffix_dict:
            for d1 in sub_dirs(os.path.join(path, d0)):
                sub_module_path = os.path.join(path, d0, d1)
                for file in files_in_dir(sub_module_path):
                    suffix = os.path.splitext(file['name'])[1]
                    if suffix == '':  # 如果文件名为空，例如 .uuid 的情况
                        suffix = os.path.splitext(file['name'])[0]
                    if suffix in allowed_suffix_dict[d0] or '.*' in allowed_suffix_dict[d0]:
                        file_path = os.path.join(sub_module_path, file['name'])
                        backup_sub_module_path = os.path.join(backup_path, d0, d1)
                        backup_file_path = os.path.join(backup_sub_module_path, file['name'])
                        os.makedirs(backup_sub_module_path, exist_ok=True)
                        shutil.copy(file_path, backup_file_path)

                for d2 in sub_dirs(sub_module_path):
                    sub_sub_module_path = os.path.join(sub_module_path, d2)
                    for file in files_in_dir(sub_sub_module_path):
                        suffix = os.path.splitext(file['name'])[1]
                        if suffix == '':  # 如果文件名为空，例如 .uuid 的情况
                            suffix = os.path.splitext(file['name'])[0]
                        if suffix in allowed_suffix_dict[d0] or '.*' in allowed_suffix_dict[d0]:
                            file_path = os.path.join(sub_sub_module_path, file['name'])
                            backup_sub_sub_module_path = os.path.join(backup_path, d0, d1, d2)
                            backup_file_path = os.path.join(backup_sub_sub_module_path, file['name'])
                            os.makedirs(backup_sub_sub_module_path, exist_ok=True)
                            shutil.copy(file_path, backup_file_path)

    zip_folder(backup_path, f'{backup_root_path}/{datetime.now().date()}.zip')
