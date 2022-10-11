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

from base.forms.abaqus import UploadForm
from tools.dir_status import create_id, files_in_dir, projects_detail, get_project_status, project_jobs_detail
from tools.abaqus.Solver import Solver

abaqus_bp = Blueprint('abaqus', __name__)


@abaqus_bp.route('/manage_projects', methods=['GET', 'POST'])
@login_required
def manage_projects():
    return render_template('abaqus/manage_projects.html')


@abaqus_bp.route('/projects_status')
@login_required
def projects_status():
    data = projects_detail(current_app.config['ABAQUS_PATH'])
    return jsonify(data)


@abaqus_bp.route('/project_jobs_status/<int:project_id>')
@login_required
def project_jobs_status(project_id):
    data = project_jobs_detail(current_app.config['ABAQUS_PATH'], project_id)
    return jsonify(data)


@abaqus_bp.route('/view_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def view_project(project_id):
    path = os.path.join(current_app.config['ABAQUS_PATH'])
    project_path = os.path.join(path, str(project_id))
    form = UploadForm()
    if form.validate_on_submit():
        f = form.filename.data
        print(f)
    if os.path.exists(project_path):
        status = get_project_status(path, project_id)
        files = files_in_dir(project_path)
        return render_template('abaqus/view_project.html', project_id=project_id, status=status, files=files, form=form)
    else:
        abort(404)


# @abaqus_bp.route('/view_project/<int:project_id>')
# @login_required
# def view_project(project_id):
#     path = os.path.join(current_app.config['ABAQUS_PATH'])
#     project_path = os.path.join(path, str(project_id))
#     if os.path.exists(project_path):
#         status = get_project_status(path, project_id)
#         files = files_in_dir(project_path)
#         return render_template('abaqus/view_project.html', project_id=project_id, status=status, files=files)
#     else:
#         abort(404)


@abaqus_bp.route('/view_job/<int:project_id>/<int:job_id>')
def view_job(project_id, job_id):
    job_path = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        status = s.get_sta()
        logs = s.get_log()
        inp = s.get_inp()
        files = files_in_dir(job_path)
        return render_template('abaqus/view_job.html', project_id=project_id, job_id=job_id, logs=logs, status=status, inp=inp, files=files)
    else:
        abort(404)


@abaqus_bp.route('/open_path/<path>')
def open_path(path):
    cmd = 'explorer %s' % path
    proc = subprocess.run(cmd)
    return str(proc)
