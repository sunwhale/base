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
from tools.tree import json_to_ztree, odb_json_to_ztree
from tools.common import make_dir, dump_json, load_json
from base.global_var import event_source
from tools.events_new import update_events_new


abaqus_bp = Blueprint('abaqus', __name__)


@abaqus_bp.route('/observer', methods=['GET', 'POST'])
@login_required
def observer():
    print('event_message', event_message)
    return event_message


@abaqus_bp.route('/manage_projects', methods=['GET', 'POST'])
@login_required
def manage_projects():
    return render_template('abaqus/manage_projects.html')


@abaqus_bp.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()

    if form.validate_on_submit():
        abaqus_path = current_app.config['ABAQUS_PATH']
        project_id = create_id(abaqus_path)
        project_path = os.path.join(abaqus_path, str(project_id))
        make_dir(project_path)
        message = {
            'name': form.name.data,
            'descript': form.descript.data,
            'job': form.job.data,
            'user': form.user.data,
            'cpus': form.cpus.data
        }
        msg_file = os.path.join(project_path, '.project_msg')
        dump_json(msg_file, message)
        return redirect(url_for('.view_project', project_id=project_id))

    return render_template('abaqus/create_project.html', form=form)


@abaqus_bp.route('/create_job/<int:project_id>', methods=['GET', 'POST'])
@login_required
def create_job(project_id):
    form = JobForm()
    abaqus_path = current_app.config['ABAQUS_PATH']
    project_path = os.path.join(abaqus_path, str(project_id))

    if form.validate_on_submit():
        job_id = create_id(project_path)
        job_path = os.path.join(project_path, str(job_id))
        make_dir(job_path)
        message = {
            'job': form.job.data,
            'user': form.user.data,
            'cpus': form.cpus.data
        }
        msg_file = os.path.join(job_path, '.job_msg')
        dump_json(msg_file, message)
        files = files_in_dir(project_path)
        for file in files:
            shutil.copy(os.path.join(project_path, file['name']),
                        os.path.join(job_path, file['name']))
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))

    msg_file = os.path.join(project_path, '.project_msg')
    message = load_json(msg_file)
    form.job.data = message['job']
    form.user.data = message['user']
    form.cpus.data = message['cpus']
    return render_template('abaqus/create_job.html', form=form)


@abaqus_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    form = ProjectForm()
    abaqus_path = current_app.config['ABAQUS_PATH']
    project_path = os.path.join(abaqus_path, str(project_id))
    msg_file = os.path.join(project_path, '.project_msg')

    if form.validate_on_submit():
        message = {
            'name': form.name.data,
            'descript': form.descript.data,
            'job': form.job.data,
            'user': form.user.data,
            'cpus': form.cpus.data
        }
        dump_json(msg_file, message)
        return redirect(url_for('.view_project', project_id=project_id))

    message = load_json(msg_file)
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
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    msg_file = os.path.join(job_path, '.job_msg')

    if form.validate_on_submit():
        message = {}
        message['job'] = form.job.data
        message['user'] = form.user.data
        message['cpus'] = form.cpus.data
        dump_json(msg_file, message)
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))

    message = load_json(msg_file)
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
def project_jobs_status(project_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_id_list = sub_dirs_int(os.path.join(abaqus_path, str(project_id)))
    for job_id in job_id_list:
        job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
        s = Solver(job_path)
        s.solver_status()
    data = project_jobs_detail(abaqus_path, project_id)
    return jsonify(data)


@abaqus_bp.route('/view_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def view_project(project_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    project_path = os.path.join(abaqus_path, str(project_id))
    s = Solver(project_path)
    parameters = s.parameter_keys()
    form = UploadForm()
    if form.validate_on_submit():
        f = form.filename.data
        f.save(os.path.join(project_path, f.filename))
    if request.method == 'POST':
        data = request.form.to_dict()
        print(data)
        if 'queue_value' in data.keys():
            queue_list = [int(job_id)
                           for job_id in data['queue_value'].split(',') if job_id != '']
            queue_type = data['queue_type']
            new_jobs = []
            if queue_type == 'Solver':
                for job_id in queue_list:
                    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
                    if os.path.exists(job_path):
                        s = Solver(job_path)
                        s.read_msg()
                        job = {'type': 'Solver',
                               'project_id': project_id,
                               'job_id': job_id,
                               'job_path': job_path,
                               'cpus': s.cpus,
                               'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                               'status': 'Submitting'}
                        new_jobs.append(job)
                        event_type = job['type']
                        event_dict = job
                        event_source.set_event(event_type, event_dict)
                        event_source.send_event()
            elif queue_type == 'odb_to_npz':
                for job_id in queue_list:
                    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
                    if os.path.exists(job_path):
                        job = {'type': 'odb_to_npz',
                               'project_id': project_id,
                               'job_id': job_id,
                               'job_path': job_path,
                               'cpus': 1,
                               'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                               'status': 'Submitting'}
                        new_jobs.append(job)
                        event_type = job['type']
                        event_dict = job
                        event_source.set_event(event_type, event_dict)
                        event_source.send_event()
            elif queue_type == 'All':
                for job_id in queue_list:
                    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
                    if os.path.exists(job_path):
                        s = Solver(job_path)
                        s.read_msg()
                        job = {'type': 'Solver',
                               'project_id': project_id,
                               'job_id': job_id,
                               'job_path': job_path,
                               'cpus': s.cpus,
                               'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                               'status': 'Submitting'}
                        new_jobs.append(job)
                        event_type = job['type']
                        event_dict = job
                        event_source.set_event(event_type, event_dict)
                        event_source.send_event()
                        job = {'type': 'odb_to_npz',
                               'project_id': project_id,
                               'job_id': job_id,
                               'job_path': job_path,
                               'cpus': 1,
                               'time': time.strftime('%Y-%m-%d %H:%M:%S'),
                               'status': 'Submitting'}
                        new_jobs.append(job)
                        event_type = job['type']
                        event_dict = job
                        event_source.set_event(event_type, event_dict)
                        event_source.send_event()
            make_dir(current_app.config['QUEUE_PATH'])
            update_events_new(new_jobs, current_app.config['EVENTS_NEW'])
            flash('选中的算例已经提交到计算队列。', 'success')
            return redirect(url_for('queue.view_queue'))
    if os.path.exists(project_path):
        status = get_project_status(abaqus_path, project_id)
        files = files_in_dir(project_path)
        return render_template('abaqus/view_project.html', project_id=project_id, status=status, files=files, parameters=parameters, form=form)
    else:
        abort(404)


@abaqus_bp.route('/delete_project/<int:project_id>')
@login_required
def delete_project(project_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    project_path = os.path.join(abaqus_path, str(project_id))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'warning')
        return redirect(url_for('.manage_projects'))
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
        flash('ABAQUS项目%s删除成功。' % project_id, 'success')
    else:
        flash('ABAQUS项目%s不存在。' % project_id, 'warning')
    return redirect(url_for('.manage_projects'))


@abaqus_bp.route('/delete_job/<int:project_id>/<int:job_id>')
@login_required
def delete_job(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'warning')
        return redirect(url_for('.manage_projects'))
    if os.path.exists(job_path):
        shutil.rmtree(job_path)
        flash('ABAQUS项目%s算例%s删除成功。' % (project_id, job_id), 'success')
    else:
        flash('ABAQUS项目%s算例%s不存在。' % (project_id, job_id), 'warning')
    return redirect(url_for('.view_project', project_id=project_id))


@abaqus_bp.route('/delete_project_file/<int:project_id>/<path:filename>')
@login_required
def delete_project_file(project_id, filename):
    abaqus_path = current_app.config['ABAQUS_PATH']
    file = os.path.join(abaqus_path, str(project_id), str(filename))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'warning')
        return redirect(url_for('.view_project', project_id=project_id))
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(url_for('.view_project', project_id=project_id))


@abaqus_bp.route('/delete_job_file/<int:project_id>/<int:job_id>/<path:filename>')
@login_required
def delete_job_file(project_id, job_id, filename):
    abaqus_path = current_app.config['ABAQUS_PATH']
    file = os.path.join(abaqus_path, str(project_id),
                        str(job_id), str(filename))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'warning')
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
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
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        s.read_msg()
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
        status = get_job_status(abaqus_path, project_id, job_id)
        return render_template('abaqus/view_job.html', project_id=project_id, job_id=job_id, status=status, logs=logs[-5000:], sta=sta[-100:], form=form, solver_status=solver_status, files=files)
    else:
        abort(404)


@abaqus_bp.route('/run_job/<int:project_id>/<int:job_id>')
@login_required
def run_job(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        s.read_msg()
        s.clear()
        if s.check_files():
            proc = s.run()
            with open(os.path.join(job_path, '.solver_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
        else:
            flash('缺少必要的计算文件。', 'warning')
        return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@abaqus_bp.route('/terminate_job/<int:project_id>/<int:job_id>')
@login_required
def terminate_job(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        s.read_msg()
        proc = s.terminate()
        with open(os.path.join(job_path, '.solver_status'), 'w', encoding='utf-8') as f:
            f.write('Stopping')
        return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@abaqus_bp.route('/open_job/<int:project_id>/<int:job_id>')
@login_required
def open_job(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        cmd = 'explorer %s' % job_path
        proc = subprocess.run(cmd)
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@abaqus_bp.route('/open_project/<int:project_id>')
@login_required
def open_project(project_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    project_path = os.path.join(abaqus_path, str(project_id))
    if os.path.exists(project_path):
        cmd = 'explorer %s' % project_path
        proc = subprocess.run(cmd)
        return redirect(url_for('.view_project', project_id=project_id))
    else:
        abort(404)


@abaqus_bp.route('/prescan_odb/<int:project_id>/<int:job_id>')
@login_required
def prescan_odb(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        p = Postproc(job_path)
        if p.has_odb():
            proc = p.prescan_odb()
            with open(os.path.join(job_path, '.prescan_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
        else:
            flash('缺少odb文件。', 'warning')
        return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@abaqus_bp.route('/odb_to_npz/<int:project_id>/<int:job_id>')
@login_required
def odb_to_npz(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        p = Postproc(job_path)
        if p.has_odb() and p.check_setting_files():
            proc = p.odb_to_npz()
            with open(os.path.join(job_path, '.odb_to_npz_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
            with open(os.path.join(job_path, '.odb_to_npz_proc'), 'w', encoding='utf-8') as f:
                f.write('0.0\n')
        else:
            flash('缺少odb文件或odb_to_npz.json配置文件。', 'warning')
        return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@abaqus_bp.route('/prescan_odb_data/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def prescan_odb_data(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    prescan_odb_json_file = os.path.join(job_path, 'prescan_odb.json')
    if os.path.exists(prescan_odb_json_file):
        prescan_odb_dict = load_json(prescan_odb_json_file)
        ztree = odb_json_to_ztree(prescan_odb_dict, url_for(
            'static', filename='zTree/icons/'))
    else:
        ztree = [{"id": 1, "pId": 0, "name": "无"}]
    return ztree


@abaqus_bp.route('/odb_to_npz_data/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def odb_to_npz_data(project_id, job_id):
    import numpy as np
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    p = Postproc(job_path)
    npz_file = os.path.join(job_path, str(p.job) + '.npz')
    if os.path.exists(npz_file):
        npz = np.load(npz_file, allow_pickle=True, encoding='latin1')
        data = npz['data'][()]
        ztree = json_to_ztree(data)
    else:
        ztree = [{"id": 1, "pId": 0, "name": "无"}]
    return ztree


@abaqus_bp.route('/print_figure/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def print_figure(project_id, job_id):
    import numpy as np
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    p = Postproc(job_path)
    npz_file = os.path.join(job_path, str(p.job) + '.npz')
    if os.path.exists(npz_file):
        npz = np.load(npz_file, allow_pickle=True, encoding='latin1')
        data = npz['data'][()]
        ztree = json_to_ztree(data)
    else:
        ztree = [{"id": 1, "pId": 0, "name": "无"}]
    return ztree
