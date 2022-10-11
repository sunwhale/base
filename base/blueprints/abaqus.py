# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil
import time
import subprocess

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

from tools.dir_status import create_id, files_in_dir
from tools.abaqus.Solver import Solver

abaqus_bp = Blueprint('abaqus', __name__)


@abaqus_bp.route('/manage_projects', methods=['GET', 'POST'])
@login_required
def manage_projects():
    return render_template('abaqus/manage_projects.html')


@abaqus_bp.route('/view_job')
def view_job():
    abaqus_path = os.path.join(current_app.config['ABAQUS_PATH'], 'run', str(1))
    s = Solver(abaqus_path)
    status = s.get_sta()
    logs = s.get_log()
    inp = s.get_inp()
    files = files_in_dir(abaqus_path)
    return render_template('abaqus/view_job.html', logs=logs, status=status, inp=inp, files=files)


@abaqus_bp.route('/open_path/<path>')
def open_path(path):
    cmd = 'explorer %s' % path
    proc = subprocess.run(cmd)
    return str(proc)