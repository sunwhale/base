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
        f.save(os.path.join(project_path, f.filename))

    if os.path.exists(project_path):
        status = get_project_status(path, project_id)
        files = files_in_dir(project_path)
        return render_template('abaqus/view_project.html', project_id=project_id, status=status, files=files, form=form)
    else:
        abort(404)


@abaqus_bp.route('/delete_project_file/<int:project_id>/<path:filename>')
@login_required
def delete_project_file(project_id, filename):
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'danger')
        return redirect(url_for('.view_project', project_id=project_id))
    file = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id), str(filename))
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(url_for('.view_project', project_id=project_id))


@abaqus_bp.route('/get_project_file/<int:project_id>/<path:filename>')
@login_required
def get_project_file(project_id, filename):
    return send_from_directory(os.path.join(current_app.config['ABAQUS_PATH'], str(project_id)), filename)


@abaqus_bp.route('/view_job/<int:project_id>/<int:job_id>')
def view_job(project_id, job_id):
    job_path = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        status = s.get_sta()
        logs = s.get_log()
        files = files_in_dir(job_path)

        status_file = os.path.join(job_path, '.status')
        if not os.path.exists(status_file):
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write('None')

        with open(status_file, 'r', encoding='utf-8') as f:
            solver_status = f.read()

        if 'COMPLETED' in logs:
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write('Completed')
        elif 'exited' in logs:
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write('Stopped')
        elif 'Run standard.exe' in logs and solver_status != 'Stopping':
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write('Running')

        with open(status_file, 'r', encoding='utf-8') as f:
            solver_status = f.read()
        
        return render_template('abaqus/view_job.html', project_id=project_id, job_id=job_id, logs=logs, status=status, solver_status=solver_status, files=files)
    else:
        abort(404)


@abaqus_bp.route('/run_job/<int:project_id>/<int:job_id>')
def run_job(project_id, job_id):
    job_path = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path, job='Job-1', user='umat_visco_maxwell_phasefield.for')
        s.clear()
        proc = s.run()
        with open(os.path.join(job_path, '.status'), 'w', encoding='utf-8') as f:
            f.write('Submitting')
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@abaqus_bp.route('/terminate_job/<int:project_id>/<int:job_id>')
def terminate_job(project_id, job_id):
    job_path = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path, job='Job-1', user='umat_visco_maxwell_phasefield.for')
        proc = s.terminate()
        with open(os.path.join(job_path, '.status'), 'w', encoding='utf-8') as f:
            f.write('Stopping')
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@abaqus_bp.route('/open_path/<path>')
def open_path(path):
    cmd = 'explorer %s' % path
    proc = subprocess.run(cmd)
    return str(proc)
