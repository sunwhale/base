# -*- coding: utf-8 -*-
"""

"""
from flask import (Blueprint, jsonify, redirect, render_template, url_for, current_app)
from flask_login import login_required

from base.utils.dir_status import get_server_uuid

sync_bp = Blueprint('sync', __name__)


@sync_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    server_uuid = get_server_uuid(current_app.config['FILE_PATH'])
    return render_template('sync/index.html', server_uuid=server_uuid)


@sync_bp.route('/uuid', methods=['GET', 'POST'])
@login_required
def uuid():
    server_uuid = get_server_uuid(current_app.config['FILE_PATH'])
    return jsonify(server_uuid)
