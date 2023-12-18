# -*- coding: utf-8 -*-
"""

"""
import requests
import json
import os
import threading
import time

from flask import (Blueprint, jsonify, abort, redirect, render_template, url_for, current_app, send_from_directory, send_file, request)
from flask_login import login_required

from base.utils.dir_status import (create_id, get_path_uuid, files_in_dir, get_job_status, get_project_status, project_jobs_detail, projects_detail,
                                   templates_detail, calculate_checksum,
                                   sub_dirs)
from base.global_var import create_thread_id, sync_threads

sync_bp = Blueprint('sync', __name__)

server_url = 'https://sunjingyu.com'
server_url = 'http://127.0.0.1:5000'


def get_files(module, module_id, module_path, status):
    status['status'] = 'loading'
    for sub_dir in sub_dirs(os.path.join(module_path, module_id)):
        for file_dict in files_in_dir(os.path.join(module_path, sub_dir)):
            url = server_url + f"/sync/get_file?module={module}&module_id={module_id}&sub_module_id={sub_dir}&filename={file_dict['name']}"
            response = requests.get(url)
            status[url] = response.status_code
    status['status'] = 'done'


def save_files(module, module_id, resource_dict, status):
    status['status'] = 'loading'
    for directory in resource_dict['data']:
        for url in resource_dict['data'][directory]:
            response = requests.get(url)
            status[url] = response.status_code
            print(response)
    status['status'] = 'done'


@sync_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('sync/index.html')


@sync_bp.route('/resource/<module>/<module_id>', methods=['GET', 'POST'])
def resource(module, module_id):
    module_path_dict = {
        'abaqus': current_app.config['ABAQUS_PATH'],
        'abaqus_template': current_app.config['ABAQUS_TEMPLATE_PATH'],
        'virtual': current_app.config['VIRTUAL_PATH'],
        'experiment': current_app.config['EXPERIMENT_PATH'],
        'doc': current_app.config['DOC_PATH'],
        'sheet': current_app.config['SHEET_PATH'],
        'packing_models': current_app.config['PACKING_MODELS_PATH'],
        'pyfem': current_app.config['PYFEM_PATH']
    }
    module_resource = {'module': module, 'module_id': module_id, 'data': {}}

    if module in module_path_dict:
        module_path = module_path_dict[module]
    else:
        return jsonify({})

    if os.path.exists(os.path.join(module_path, module_id)):
        module_resource['data']['.'] = {}
        for file_dict in files_in_dir(os.path.join(module_path, module_id)):
            url = server_url + f"/sync/get_file?module={module}&module_id={module_id}&filename={file_dict['name']}"
            module_resource['data']['.'][url] = calculate_checksum(os.path.join(module_path, module_id, file_dict['name']))

        for sub_dir in sub_dirs(os.path.join(module_path, module_id)):
            module_resource['data'][sub_dir] = {}
            for file_dict in files_in_dir(os.path.join(module_path, module_id, sub_dir)):
                url = server_url + f"/sync/get_file?module={module}&module_id={module_id}&sub_module_id={sub_dir}&filename={file_dict['name']}"
                module_resource['data'][sub_dir][url] = calculate_checksum(os.path.join(module_path, module_id, sub_dir, file_dict['name']))
        return jsonify(module_resource)
    else:
        return jsonify({})


@sync_bp.route('/download/<module>/<module_id>', methods=['GET', 'POST'])
def download(module, module_id):
    module_path_dict = {
        'abaqus': current_app.config['ABAQUS_PATH'],
        'abaqus_template': current_app.config['ABAQUS_TEMPLATE_PATH'],
        'virtual': current_app.config['VIRTUAL_PATH'],
        'experiment': current_app.config['EXPERIMENT_PATH'],
        'doc': current_app.config['DOC_PATH'],
        'sheet': current_app.config['SHEET_PATH'],
        'packing_models': current_app.config['PACKING_MODELS_PATH'],
        'pyfem': current_app.config['PYFEM_PATH']
    }
    if module in module_path_dict:
        module_path = module_path_dict[module]
    else:
        abort(404)

    url = server_url + f'/sync/resource/{module}/{module_id}'
    response = requests.get(url)
    resource_dict = json.loads(response.text)

    thread_name = f'{module}/{module_id}'

    if thread_name not in sync_threads:
        sync_threads[thread_name] = {}
        status = sync_threads[thread_name]
        status['status'] = 'submitted'
        args = (module, module_id, resource_dict, status)
        thread = threading.Thread(target=save_files, args=args)
        thread.start()
    else:
        if sync_threads[thread_name]['status'] == 'done':
            sync_threads.pop(thread_name)
            sync_threads[thread_name] = {}
            status = sync_threads[thread_name]
            status['status'] = 'submitted'
            args = (module, module_id, resource_dict, status)
            thread = threading.Thread(target=save_files, args=args)
            thread.start()

    return response.text


@sync_bp.route('/download_status/<module>/<module_id>/', methods=['GET', 'POST'])
def download_status(module, module_id):
    thread_name = f'{module}/{module_id}'
    if thread_name in sync_threads:
        return jsonify(sync_threads[thread_name])
    else:
        return jsonify(None)


@sync_bp.route('/get_file', methods=['GET', 'POST'])
def get_file():
    module_path_dict = {
        'abaqus': current_app.config['ABAQUS_PATH'],
        'abaqus_template': current_app.config['ABAQUS_TEMPLATE_PATH'],
        'virtual': current_app.config['VIRTUAL_PATH'],
        'experiment': current_app.config['EXPERIMENT_PATH'],
        'doc': current_app.config['DOC_PATH'],
        'sheet': current_app.config['SHEET_PATH'],
        'packing_models': current_app.config['PACKING_MODELS_PATH'],
        'pyfem': current_app.config['PYFEM_PATH']
    }

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
    return jsonify(local_uuid)


@sync_bp.route('/get_server_uuid', methods=['GET', 'POST'])
def get_server_uuid():
    server_uuid_url = server_url + '/sync/uuid'
    response = requests.get(server_uuid_url)
    server_uuid = json.loads(response.text)
    return jsonify(server_uuid)
