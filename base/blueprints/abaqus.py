# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil
import subprocess
import time

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

from base.forms.abaqus import JobForm, ParameterForm, ProjectForm, UploadForm
from tools.abaqus.Solver import Solver
from tools.abaqus.Postproc import Postproc
from tools.dir_status import (create_id, files_in_dir, get_job_status,
                              get_project_status, project_jobs_detail,
                              projects_detail, sub_dirs_int)

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
        project_id = create_id(current_app.config['ABAQUS_PATH'])
        project_path = os.path.join(
            current_app.config['ABAQUS_PATH'], str(project_id))
        if not os.path.isdir(project_path):
            os.makedirs(project_path)
        message = {}
        message['name'] = form.name.data
        message['descript'] = form.descript.data
        message['job'] = form.job.data
        message['user'] = form.user.data
        message['cpus'] = form.cpus.data
        msg_file = os.path.join(project_path, 'project.msg')
        with open(msg_file, 'w', encoding='utf-8') as f:
            json.dump(message, f, ensure_ascii=False)
        return redirect(url_for('.view_project', project_id=project_id))
    return render_template('abaqus/create_project.html', form=form)


@abaqus_bp.route('/create_job/<int:project_id>', methods=['GET', 'POST'])
@login_required
def create_job(project_id):
    form = JobForm()
    path = current_app.config['ABAQUS_PATH']
    project_path = os.path.join(path, str(project_id))
    if form.validate_on_submit():
        job_id = create_id(project_path)
        job_path = os.path.join(project_path, str(job_id))
        if not os.path.isdir(job_path):
            os.makedirs(job_path)
        message = {}
        message['job'] = form.job.data
        message['user'] = form.user.data
        message['cpus'] = form.cpus.data
        msg_file = os.path.join(job_path, '.msg')
        with open(msg_file, 'w', encoding='utf-8') as f:
            json.dump(message, f, ensure_ascii=False)
        files = files_in_dir(project_path)
        for file in files:
            shutil.copy(os.path.join(project_path, file['name']), os.path.join(
                job_path, file['name']))
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    msg_file = os.path.join(project_path, 'project.msg')
    with open(msg_file, 'r', encoding='utf-8') as f:
        message = json.load(f)
    form.job.data = message['job']
    form.user.data = message['user']
    form.cpus.data = message['cpus']
    return render_template('abaqus/create_job.html', form=form)


@abaqus_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    form = ProjectForm()
    project = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id))
    msg_file = os.path.join(project, 'project.msg')

    if form.validate_on_submit():
        message = {}
        message['name'] = form.name.data
        message['descript'] = form.descript.data
        message['job'] = form.job.data
        message['user'] = form.user.data
        message['cpus'] = form.cpus.data
        with open(msg_file, 'w', encoding='utf-8') as f:
            json.dump(message, f, ensure_ascii=False)
        return redirect(url_for('.view_project', project_id=project_id))

    with open(msg_file, 'r', encoding='utf-8') as f:
        message = json.load(f)
    form.name.data = message['name']
    form.descript.data = message['descript']
    form.job.data = message['job']
    form.user.data = message['user']
    form.cpus.data = message['cpus']
    return render_template('abaqus/create_job.html', form=form)


@abaqus_bp.route('/edit_job/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(project_id, job_id):
    form = JobForm()
    job_path = os.path.join(
        current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
    msg_file = os.path.join(job_path, '.msg')

    if form.validate_on_submit():
        message = {}
        message['job'] = form.job.data
        message['user'] = form.user.data
        message['cpus'] = form.cpus.data
        with open(msg_file, 'w', encoding='utf-8') as f:
            json.dump(message, f, ensure_ascii=False)
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))

    with open(msg_file, 'r', encoding='utf-8') as f:
        message = json.load(f)
    form.job.data = message['job']
    form.user.data = message['user']
    form.cpus.data = message['cpus']
    return render_template('abaqus/create_job.html', form=form)


@abaqus_bp.route('/projects_status')
@login_required
def projects_status():
    data = projects_detail(current_app.config['ABAQUS_PATH'])
    return jsonify(data)


@abaqus_bp.route('/project_jobs_status/<int:project_id>')
@login_required
def project_jobs_status(project_id):
    path = current_app.config['ABAQUS_PATH']
    job_id_list = sub_dirs_int(os.path.join(path, str(project_id)))
    for job_id in job_id_list:
        job_path = os.path.join(path, str(project_id), str(job_id))
        s = Solver(job_path)
        s.solver_status()
    data = project_jobs_detail(current_app.config['ABAQUS_PATH'], project_id)
    return jsonify(data)


@abaqus_bp.route('/view_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def view_project(project_id):
    path = current_app.config['ABAQUS_PATH']
    project_path = os.path.join(path, str(project_id))
    s = Solver(project_path)
    parameters = s.parameter_keys()
    form = UploadForm()
    if form.validate_on_submit():
        f = form.filename.data
        f.save(os.path.join(project_path, f.filename))

    if os.path.exists(project_path):
        status = get_project_status(path, project_id)
        files = files_in_dir(project_path)
        return render_template('abaqus/view_project.html', project_id=project_id, status=status, files=files, parameters=parameters, form=form)
    else:
        abort(404)


@abaqus_bp.route('/delete_project/<int:project_id>')
@login_required
def delete_project(project_id):
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'danger')
        return redirect(url_for('.manage_projects'))
    project_path = os.path.join(
        current_app.config['ABAQUS_PATH'], str(project_id))
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
        flash('ABAQUS项目%s删除成功。' % project_id, 'success')
    else:
        flash('ABAQUS项目%s不存在。' % project_id, 'warning')
    return redirect(url_for('.manage_projects'))


@abaqus_bp.route('/delete_job/<int:project_id>/<int:job_id>')
@login_required
def delete_job(project_id, job_id):
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'danger')
        return redirect(url_for('.manage_projects'))
    job_path = os.path.join(
        current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
    if os.path.exists(job_path):
        shutil.rmtree(job_path)
        flash('ABAQUS项目%s算例%s删除成功。' % (project_id, job_id), 'success')
    else:
        flash('ABAQUS项目%s算例%s不存在。' % (project_id, job_id), 'warning')
    return redirect(url_for('.view_project', project_id=project_id))


@abaqus_bp.route('/delete_project_file/<int:project_id>/<path:filename>')
@login_required
def delete_project_file(project_id, filename):
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'danger')
        return redirect(url_for('.view_project', project_id=project_id))
    file = os.path.join(current_app.config['ABAQUS_PATH'], str(
        project_id), str(filename))
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
    file = os.path.join(current_app.config['ABAQUS_PATH'], str(
        project_id), str(job_id), str(filename))
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


@abaqus_bp.route('/view_job/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def view_job(project_id, job_id):
    path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        sta = s.get_sta()
        logs = s.get_log()
        para = s.get_parameters()
        form = ParameterForm()
        if form.validate_on_submit():
            para = form.para.data
            s.save_parameters(para)
            flash('parameters.inp保存成功。', 'success')
            return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
        form.para.data = para
        s.parameters_to_json()
        files = files_in_dir(job_path)
        solver_status = s.solver_status()
        status = get_job_status(path, project_id, job_id)
        return render_template('abaqus/view_job.html', project_id=project_id, job_id=job_id, status=status, logs=logs[-5000:], sta=sta[-100:], form=form, solver_status=solver_status, files=files)
    else:
        abort(404)


@abaqus_bp.route('/run_job/<int:project_id>/<int:job_id>')
@login_required
def run_job(project_id, job_id):
    job_path = os.path.join(
        current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
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
        return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@abaqus_bp.route('/terminate_job/<int:project_id>/<int:job_id>')
@login_required
def terminate_job(project_id, job_id):
    job_path = os.path.join(
        current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        s.read_msg()
        proc = s.terminate()
        with open(os.path.join(job_path, '.status'), 'w', encoding='utf-8') as f:
            f.write('Stopping')
        return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
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


@abaqus_bp.route('/prescan_odb/<int:project_id>/<int:job_id>')
@login_required
def prescan_odb(project_id, job_id):
    job_path = os.path.join(
        current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
    if os.path.exists(job_path):
        p = Postproc(job_path)
        if p.check_files():
            proc = p.prescan_odb()
        else:
            flash('缺少odb文件。', 'warning')
        return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


def dict_to_tree(obj, start_id, parent_id, depth=0, maxdepth=10):
    if depth >= maxdepth:
        return start_id
    if isinstance(obj, dict):
        for key, val in obj.items():
            if depth < 1:
                tree.append({"id": start_id, "pId": parent_id,
                             "name": key, "open": True})
            else:
                tree.append({"id": start_id, "pId": parent_id, "name": key})
            start_id += 1
            start_id = dict_to_tree(
                val, start_id, start_id-1, depth=depth+1, maxdepth=maxdepth)
    elif isinstance(obj, list):
        i = 0
        for elem in obj:
            tree.append({"id": start_id, "pId": parent_id, "name": i})
            i += 1
            start_id += 1
            start_id = dict_to_tree(
                elem, start_id, start_id-1, depth=depth, maxdepth=maxdepth)
    else:
        tree.append({"id": start_id, "pId": parent_id, "name": obj})
        start_id += 1
    return start_id


@abaqus_bp.route('/prescan_odb_data/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def prescan_odb_data(project_id, job_id):
    job_path = os.path.join(
        current_app.config['ABAQUS_PATH'], str(project_id), str(job_id))
    prescan_odb_json_file = os.path.join(job_path, 'prescan_odb.json')
    global tree
    tree = []
    if os.path.exists(prescan_odb_json_file):
        with open(prescan_odb_json_file, 'r', encoding='utf-8') as f:
            prescan_odb_dict = json.load(f)
            dict_to_tree(prescan_odb_dict, 1, 0)
    else:
        tree.append({"id": 1, "pId": 0, "name": "空"})
    return tree


@abaqus_bp.route('/scan_odb')
@login_required
def scan_odb():
    return render_template('abaqus/scan_odb.html')


@abaqus_bp.route('/scan_odb_data', methods=['GET', 'POST'])
@login_required
def scan_odb_data():
    odb_json_file = 'F:\\Github\\base\\tools\\abaqus\\prescan_odb.json'
    with open(odb_json_file, 'r', encoding='utf-8') as f:
        odb_dict = json.load(f)

    tree = []

    parent_id = {}
    for i in range(10):
        parent_id[i] = []

    tree.append({"id": len(tree)+1, "pId": 0, "name": "Datasets", "open": True, "icon": url_for(
        'static', filename='zTree/icons/icoR_adaptiveRemeshRulesSmall.png')})

    parent_id[0].append(len(tree))

    tree.append({"id": len(tree)+1, "pId": parent_id[0][-1], "name": "File: " +
                 odb_dict['name'], "icon": url_for('static', filename='zTree/icons/icoR_mdbSmall.png')})

    parent_id[1].append(len(tree))
    for step_key, step in odb_dict['steps'].items():
        tree.append({"id": len(tree)+1, "pId": parent_id[1][-1], "name": step_key, "icon": url_for(
            'static', filename='zTree/icons/icoR_stepSmall.png')})

        parent_id[2].append(len(tree))
        for frame in step['frames']:
            tree.append({"id": len(tree)+1, "pId": parent_id[2][-1], "name": frame['description'], "icon": url_for(
                'static', filename='zTree/icons/icoR_framesSmall.png')})

            parent_id[3].append(len(tree))
            for field_name in ['S', 'LE', 'E']:
                if field_name in frame['fieldOutputs'].keys():
                    tree.append({"id": len(tree)+1, "pId": parent_id[3][-1],
                                 "name": field_name})

                    parent_id[4].append(len(tree))

                    tree.append({"id": len(tree)+1, "pId": parent_id[4][-1],
                                 "name": "Element types: %s" % str(frame['fieldOutputs']['S']['baseElementTypes'])})

                    tree.append({"id": len(tree)+1, "pId": parent_id[4][-1],
                                 "name": "Component labels: %s" % str(frame['fieldOutputs']['S']['componentLabels'])})

    return tree
