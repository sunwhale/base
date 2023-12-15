# -*- coding: utf-8 -*-
"""

"""
import requests
import json

from flask import (Blueprint, jsonify, redirect, render_template, url_for, current_app)
from flask_login import login_required

from base.utils.dir_status import get_path_uuid

sync_bp = Blueprint('sync', __name__)


@sync_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('sync/index.html')


@sync_bp.route('/uuid', methods=['GET', 'POST'])
def uuid():
    local_uuid = get_path_uuid(current_app.config['FILE_PATH'])
    return jsonify(local_uuid)


@sync_bp.route('/get_server_uuid', methods=['GET', 'POST'])
def get_server_uuid():
    server_url = 'https://sunjingyu.com/sync/uuid'
    response = requests.get(server_url)
    server_uuid = json.loads(response.text)
    return jsonify(server_uuid)
