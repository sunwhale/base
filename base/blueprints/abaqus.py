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

from base.forms.abaqus import UploadForm, ProjectForm, JobForm
from tools.dir_status import create_id, files_in_dir, projects_detail, get_project_status, project_jobs_detail, get_job_status
from tools.abaqus.Solver import Solver

abaqus_bp = Blueprint('abaqus', __name__)


@abaqus_bp.route('/manage_projects', methods=['GET', 'POST'])
@login_required
def manage_projects():
    return render_template('abaqus/manage_projects.html')


@abaqus_bp.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()
    if form.validate_on_submit():
        name = form.name.data
        descript = form.descript.data
        project_id = create_id(current_app.config['ABAQUS_PATH'])
        project_path = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id))
        if not os.path.isdir(project_path):
            os.makedirs(project_path)
        message = {}
        message['name'] = name
        message['descript'] = descript
        msg_file = os.path.join(project_path, 'project.msg')
        with open(msg_file, 'w', encoding='utf-8') as f:
            json.dump(message, f, ensure_ascii=False)
        return redirect(url_for('.view_project', project_id=project_id))
    return render_template('abaqus/create_project.html', form=form)


@abaqus_bp.route('/create_job/<int:project_id>', methods=['GET', 'POST'])
@login_required
def create_job(project_id):
    form = JobForm()
    if form.validate_on_submit():
        job = form.job.data
        user = form.user.data
        cpus = form.cpus.data
        path = current_app.config['ABAQUS_PATH']
        project_path = os.path.join(path, str(project_id))
        job_id = create_id(project_path)
        job_path = os.path.join(project_path, str(job_id))
        if not os.path.isdir(job_path):
            os.makedirs(job_path)
        message = {}
        message['job'] = job
        message['user'] = user
        message['cpus'] = cpus
        msg_file = os.path.join(job_path, '.msg')
        with open(msg_file, 'w', encoding='utf-8') as f:
            json.dump(message, f, ensure_ascii=False)
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    return render_template('abaqus/create_job.html', form=form)


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
    path = current_app.config['ABAQUS_PATH']
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


@abaqus_bp.route('/delete_project/<int:project_id>')
@login_required
def delete_project(project_id):
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'danger')
        return redirect(url_for('.manage_projects'))
    project_path = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id))
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
        flash('ABAQUS项目%s删除成功。' % project_id, 'success')
    else:
        flash('ABAQUS项目%s不存在。' % project_id, 'warning')
    return redirect(url_for('.manage_projects'))


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


@abaqus_bp.route('/delete_job_file/<int:project_id>/<int:job_id>/<path:filename>')
@login_required
def delete_job_file(project_id, job_id, filename):
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'danger')
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    file = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id), str(job_id), str(filename))
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))


@abaqus_bp.route('/get_project_file/<int:project_id>/<path:filename>')
@login_required
def get_project_file(project_id, filename):
    return send_from_directory(os.path.join(current_app.config['ABAQUS_PATH'], str(project_id)), filename)


@abaqus_bp.route('/get_job_file/<int:project_id>/<int:job_id>/<path:filename>')
@login_required
def get_job_file(project_id, job_id, filename):
    return send_from_directory(os.path.join(current_app.config['ABAQUS_PATH'], str(project_id), str(job_id)), filename)


@abaqus_bp.route('/view_job/<int:project_id>/<int:job_id>')
@login_required
def view_job(project_id, job_id):
    path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        sta = s.get_sta()
        logs = s.get_log()
        files = files_in_dir(job_path)
        solver_status = s.solver_status()
        status = get_job_status(path, project_id, job_id)
        return render_template('abaqus/view_job.html', project_id=project_id, job_id=job_id, status=status, logs=logs, sta=sta, solver_status=solver_status, files=files)
    else:
        abort(404)


@abaqus_bp.route('/run_job/<int:project_id>/<int:job_id>')
@login_required
def run_job(project_id, job_id):
    job_path = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        s.read_msg()
        s.clear()
        if s.check_files():
            proc = s.run()
            with open(os.path.join(job_path, '.status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
        else:
            flash('缺少必要的计算文件。', 'warning')
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@abaqus_bp.route('/terminate_job/<int:project_id>/<int:job_id>')
@login_required
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


@abaqus_bp.route('/open_job/<int:project_id>/<int:job_id>')
@login_required
def open_job(project_id, job_id):
    path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        cmd = 'explorer %s' % job_path
        proc = subprocess.run(cmd)
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)