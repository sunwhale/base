# -*- coding: utf-8 -*-
"""

"""
import json
import os
import threading

import requests
from flask import (Blueprint, jsonify, abort, redirect, render_template, url_for, current_app, send_from_directory,
                   request)

from base.decorators import permission_required
from base.global_var import sync_threads
from base.utils.dir_status import (create_id, get_path_uuid, files_in_dir, calculate_checksum, sub_dirs)

sync_bp = Blueprint('sync', __name__)

server_url = 'https://sunjingyu.com:8010'

# server_url = 'http://127.0.0.1:5000'

allowed_suffix_dict = {
    'abaqus': ['.project_msg', '.inp', '.for', '.FOR', '.json', '.abaqus_msg', '.job_msg', '.uuid'],
    'abaqus_template': ['.inp', '.for', '.FOR', '.json', '.template_msg', '.job_msg', '.uuid'],
    'abaqus_pre': ['.inp', '.for', '.FOR', '.py', '.json', '.preproc_msg', '.uuid'],
    'virtual': ['.inp', '.for', '.json', '.abaqus_msg', '.job_msg', '.uuid'],
    'experiment': ['.*'],
    'doc': ['.*'],
    'sheet': ['.*'],
    'packing_models': ['.*'],
    'material': ['.*'],
    'pyfem': ['.toml', '.inp', '.msh', '.json', '.project_msg', '.job_msg', '.uuid']
}


def get_module_path_dict():
    module_path_dict = {
        'abaqus': current_app.config['ABAQUS_PATH'],
        'abaqus_template': current_app.config['ABAQUS_TEMPLATE_PATH'],
        'abaqus_pre': current_app.config['ABAQUS_PRE_PATH'],
        'virtual': current_app.config['VIRTUAL_PATH'],
        'experiment': current_app.config['EXPERIMENT_PATH'],
        'doc': current_app.config['DOC_PATH'],
        'material': current_app.config['MATERIAL_PATH'],
        'sheet': current_app.config['SHEET_PATH'],
        'packing_models': current_app.config['PACKING_MODELS_PATH'],
        'pyfem': current_app.config['PYFEM_PATH']
    }
    return module_path_dict


def save_files(module, module_id, module_path_dict, resource_dict, status):
    status['status'] = 'loading'
    module_path = module_path_dict[module]
    if not os.path.exists(module_path):
        os.mkdir(module_path)
    save_path = os.path.join(module_path, str(module_id))
    if not os.path.exists(save_path):
        os.mkdir(save_path)
    for directory in resource_dict['data']:
        if not os.path.exists(os.path.join(save_path, directory)):
            os.mkdir(os.path.join(save_path, directory))
        for url in resource_dict['data'][directory]:
            filename = resource_dict['data'][directory][url][0]
            file_md5 = resource_dict['data'][directory][url][1]
            file_local = os.path.join(save_path, directory, filename)
            if os.path.exists(file_local) and calculate_checksum(file_local) == file_md5:
                status[url] = 'existed'
            else:
                response = requests.get(url)
                with open(file_local, 'wb') as file:
                    file.write(response.content)
                status[url] = 'downloaded'
    status['status'] = 'done'


@sync_bp.route('/', methods=['GET', 'POST'])
@permission_required('RESOURCE')
def index():
    if request.method == 'POST':
        data = request.form.to_dict()
        if 'create_value' in data.keys():
            create_list = [sub_module for sub_module in data['create_value'].split(',') if sub_module != '']
            print(create_list)
        return redirect(url_for('sync.index'))
    return render_template('sync/index.html')


@sync_bp.route('/resource/<module>/<module_id>', methods=['GET', 'POST'])
def resource(module, module_id):
    module_path_dict = get_module_path_dict()
    module_resource = {'module': module, 'module_id': module_id, 'data': {}}

    if module in module_path_dict:
        module_path = module_path_dict[module]
    else:
        return jsonify(None)

    sub_module_path = os.path.join(module_path, module_id)

    if os.path.exists(sub_module_path):
        module_resource['data']['.'] = {}
        for file_dict in files_in_dir(sub_module_path):
            suffix = os.path.splitext(file_dict['name'])[1]
            if suffix == '':  # 如果文件名为空，例如 .uuid 的情况
                suffix = os.path.splitext(file_dict['name'])[0]
            if suffix in allowed_suffix_dict[module] or '.*' in allowed_suffix_dict[module]:
                url = server_url + f"/sync/get_file?module={module}&module_id={module_id}&filename={file_dict['name']}"
                file_path = os.path.join(sub_module_path, file_dict['name'])
                module_resource['data']['.'][url] = [file_dict['name'], calculate_checksum(file_path)]

        for sub_dir in sub_dirs(sub_module_path):
            module_resource['data'][sub_dir] = {}
            for file_dict in files_in_dir(os.path.join(sub_module_path, sub_dir)):
                suffix = os.path.splitext(file_dict['name'])[1]
                if suffix == '':  # 如果文件名为空，例如 .uuid 的情况
                    suffix = os.path.splitext(file_dict['name'])[0]
                if suffix in allowed_suffix_dict[module] or '.*' in allowed_suffix_dict[module]:
                    url = server_url + f"/sync/get_file?module={module}&module_id={module_id}&sub_module_id={sub_dir}&filename={file_dict['name']}"
                    file_path = os.path.join(sub_module_path, sub_dir, file_dict['name'])
                    module_resource['data'][sub_dir][url] = [file_dict['name'], calculate_checksum(file_path)]
        return jsonify(module_resource)
    else:
        return jsonify(None)


@sync_bp.route('/download/<module>/<server_module_id>/to/<local_module_id>', methods=['GET', 'POST'])
def download(module, server_module_id, local_module_id):
    module_path_dict = get_module_path_dict()
    if module in module_path_dict:
        module_path = module_path_dict[module]
    else:
        abort(404)

    url = server_url + f'/sync/resource/{module}/{server_module_id}'
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.Timeout:
        abort(408)
    except requests.exceptions.RequestException as e:
        abort(500)

    resource_dict = json.loads(response.text)

    if int(local_module_id) == 0:
        local_module_id = create_id(module_path)

    thread_name = f'{module}/{server_module_id}/{local_module_id}'

    if thread_name not in sync_threads:
        sync_threads[thread_name] = {}
        status = sync_threads[thread_name]
        status['status'] = 'submitted'
        args = (module, local_module_id, module_path_dict, resource_dict, status)
        thread = threading.Thread(target=save_files, args=args)
        thread.start()
    else:
        if sync_threads[thread_name]['status'] == 'done':
            sync_threads.pop(thread_name)
            sync_threads[thread_name] = {}
            status = sync_threads[thread_name]
            status['status'] = 'submitted'
            args = (module, local_module_id, module_path_dict, resource_dict, status)
            thread = threading.Thread(target=save_files, args=args)
            thread.start()

    return render_template('sync/download.html', module=module, server_module_id=server_module_id,
                           local_module_id=local_module_id)


@sync_bp.route('/create/<module>/<server_module_id>', methods=['GET', 'POST'])
def create(module, server_module_id):
    module_path_dict = get_module_path_dict()
    if module in module_path_dict:
        module_path = module_path_dict[module]
    else:
        abort(404)
    local_module_id = create_id(module_path)
    return redirect(
        url_for('.download', module=module, server_module_id=server_module_id, local_module_id=local_module_id))


@sync_bp.route('/download_status/<module>/<server_module_id>/to/<local_module_id>', methods=['GET', 'POST'])
def download_status(module, server_module_id, local_module_id):
    thread_name = f'{module}/{server_module_id}/{local_module_id}'
    if thread_name in sync_threads:
        return jsonify(sync_threads[thread_name])
    else:
        return jsonify(None)


@sync_bp.route('/get_file', methods=['GET', 'POST'])
def get_file():
    module_path_dict = get_module_path_dict()
    module = request.args.get('module')
    module_id = request.args.get('module_id')
    sub_module_id = request.args.get('sub_module_id')
    filename = request.args.get('filename')

    if module in module_path_dict:
        if sub_module_id:
            path = os.path.join(module_path_dict[module], module_id, sub_module_id)
        elif module_id:
            path = os.path.join(module_path_dict[module], module_id)
        else:
            path = ''
    else:
        path = ''

    return send_from_directory(path, filename)


@sync_bp.route('/uuid', methods=['GET', 'POST'])
def uuid():
    local_uuid = get_path_uuid(current_app.config['FILE_PATH'])
    return jsonify(sorted(local_uuid))


@sync_bp.route('/get_server_uuid', methods=['GET', 'POST'])
def get_server_uuid():
    server_uuid_url = server_url + '/sync/uuid'
    response = requests.get(server_uuid_url)
    server_uuid = json.loads(response.text)
    return jsonify(server_uuid)


@sync_bp.route('/get_server_resource/<module>/<module_id>', methods=['GET', 'POST'])
def get_server_resource(module, module_id):
    server_resource_url = server_url + f'/sync/resource/{module}/{module_id}'
    response = requests.get(server_resource_url)
    server_resource = json.loads(response.text)
    return jsonify(server_resource)


@sync_bp.route('/url', methods=['GET', 'POST'])
def url():
    return render_template('sync/url.html')
