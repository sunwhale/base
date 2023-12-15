# -*- coding: utf-8 -*-
"""

"""
import requests
import json
import os
import threading
import time

from flask import (Blueprint, jsonify, redirect, render_template, url_for, current_app, send_from_directory, send_file)
from flask_login import login_required

from base.utils.dir_status import (create_id, get_path_uuid, files_in_dir, get_job_status, get_project_status, project_jobs_detail, projects_detail, templates_detail,
                                   sub_dirs)
from base.global_var import create_thread_id, sync_threads

sync_bp = Blueprint('sync', __name__)

server_url = 'https://sunjingyu.com'
server_url = 'http://127.0.0.1:5000'


def get_files(module, index, path, status):
    status['status'] = 'loading'
    for sub_dir in sub_dirs(path):
        for file_dict in files_in_dir(os.path.join(path, sub_dir)):
            url = server_url + f"/sync/get_file_level4/{module}/{index}/{sub_dir}/{file_dict['name']}"
            response = requests.get(url)
            status[url] = response
            print(response)
    status['status'] = 'done'


@sync_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('sync/index.html')


@sync_bp.route('/download/<module>/<index>', methods=['GET', 'POST'])
def download(module, index):
    path = os.path.join(current_app.config['FILE_PATH'], module, index)
    thread_name = f'{module}{index}'
    if thread_name not in sync_threads:
        sync_threads[thread_name] = {}
        status = sync_threads[thread_name]
        status['status'] = 'submitted'
        args = (module, index, path, status)
        thread = threading.Thread(target=get_files, args=args)
        thread.start()
    else:
        status = sync_threads[thread_name]
        if sync_threads[thread_name]['status'] != 'loading':
            status = {'status': 'submitted'}
            args = (module, index, path, status)
            thread = threading.Thread(target=get_files, args=args)
            thread.start()
    print(sync_threads)
    # for sub_dir in sub_dirs(path):
    #     for file_dict in files_in_dir(os.path.join(path, sub_dir)):
    #         response = requests.get(server_url + f"/sync/get_file_level4/{module}/{index}/{sub_dir}/{file_dict['name']}")
    #         print(response)
    return str(sync_threads)


@sync_bp.route('/get_file/<module>/<index>/<filename>', methods=['GET', 'POST'])
def get_file(module, index, filename):
    file_path = os.path.join(current_app.config['FILE_PATH'], module, index, filename)
    return send_file(file_path)


@sync_bp.route('/get_file_level4/<module>/<index>/<sub_dir>/<filename>', methods=['GET', 'POST'])
def get_file_level4(module, index, sub_dir, filename):
    file_path = os.path.join(current_app.config['FILE_PATH'], module, index, sub_dir, filename)
    time.sleep(5)
    return send_file(file_path)


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
