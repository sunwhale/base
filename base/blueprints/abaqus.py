# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil
import subprocess
import time
import uuid

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

from base.forms.abaqus import (JobForm, ParameterForm, ProjectForm, TemplateForm, ImportTemplateForm, UploadForm, FigureSettingFrom, OdbForm)
from base.global_var import event_source
from base.utils.abaqus.Postproc import Postproc
from base.utils.abaqus.Solver import Solver
from base.utils.common import make_dir, dump_json, load_json
from base.utils.dir_status import (create_id, files_in_dir, subpaths_in_dir, get_job_status, get_project_status, get_template_status, project_jobs_detail,
                                   projects_detail, templates_detail, sub_dirs_int, sub_dirs)
from base.utils.events_new import update_events_new
from base.utils.make_gif import make_gif
from base.utils.read_prescan import read_prescan
from base.utils.tree import json_to_ztree, odb_json_to_ztree

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
        abaqus_path = current_app.config['ABAQUS_PATH']
        project_id = create_id(abaqus_path)
        project_path = os.path.join(abaqus_path, str(project_id))
        make_dir(project_path)
        uuid_file = os.path.join(project_path, '.uuid')
        with open(uuid_file, 'w', encoding='utf-8') as f:
            f.write(str(uuid.uuid4()))
        message = {
            'name': form.name.data,
            'descript': form.descript.data,
            'job': form.job.data,
            'user': form.user.data,
            'cpus': form.cpus.data
        }
        msg_file = os.path.join(project_path, '.project_msg')
        dump_json(msg_file, message)
        flash('项目创建成功。', 'success')
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
            shutil.copy(os.path.join(project_path, file['name']), os.path.join(job_path, file['name']))
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
    return render_template('abaqus/create_project.html', form=form)


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
    templates_path = current_app.config['ABAQUS_TEMPLATE_PATH']
    s = Solver(project_path)
    parameters = s.parameter_keys()
    form_upload = UploadForm()
    form_template = ImportTemplateForm()
    template_dict = templates_detail(templates_path)
    template_list = []
    for template in template_dict['data']:
        template_list.append('%s_%s' % (template['template_id'], template['name']))
    form_template.name.choices = template_list
    if form_upload.validate_on_submit():
        f = form_upload.filename.data
        f.save(os.path.join(project_path, f.filename))
        flash('上传文件%s成功。' % f.filename, 'success')
        return redirect(url_for('abaqus.view_project', project_id=project_id))

    if form_template.validate_on_submit():
        template_id = int(form_template.name.data.split('_')[0])
        template_path = os.path.join(templates_path, str(template_id))
        files = files_in_dir(template_path)
        for file in files:
            shutil.copy(os.path.join(template_path, file['name']),
                        os.path.join(project_path, file['name']))
            flash('从模板导入文件%s成功。' % file['name'], 'success')
        return redirect(url_for('abaqus.view_project', project_id=project_id))

    if request.method == 'POST':
        data = request.form.to_dict()
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
        return render_template('abaqus/view_project.html', project_id=project_id, status=status, files=files,
                               parameters=parameters, form_upload=form_upload, form_template=form_template)
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


@abaqus_bp.route('/synchronize_project_file/<int:project_id>/<path:filename>')
@login_required
def synchronize_project_file(project_id, filename):
    abaqus_path = current_app.config['ABAQUS_PATH']
    project_path = os.path.join(abaqus_path, str(project_id))
    file = os.path.join(abaqus_path, str(project_id), str(filename))
    if os.path.exists(file):
        for job_path in sub_dirs(project_path):
            shutil.copy(os.path.join(project_path, filename), os.path.join(project_path, job_path, filename))
        flash('文件%s已经同步至所有算例。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(request.referrer or url_for('.view_project', project_id=project_id))


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
    return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))


@abaqus_bp.route('/delete_job_subpath/<int:project_id>/<int:job_id>/<path:pathname>')
@login_required
def delete_job_subpath(project_id, job_id, pathname):
    abaqus_path = current_app.config['ABAQUS_PATH']
    subpath = os.path.join(abaqus_path, str(project_id),
                           str(job_id), str(pathname))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件夹！', 'warning')
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    if os.path.exists(subpath):
        shutil.rmtree(subpath)
        flash('文件夹%s删除成功。' % pathname, 'success')
    else:
        flash('文件夹%s不存在。' % pathname, 'warning')
    return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))


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
        run_logs = s.get_run_log()
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
        return render_template('abaqus/view_job.html', project_id=project_id, job_id=job_id, status=status,
                               logs=logs[-5000:], sta=sta[-100:], run_logs=run_logs, form=form,
                               solver_status=solver_status, files=files)
    else:
        abort(404)


@abaqus_bp.route('/job_status/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def job_status(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        s.read_msg()
        sta = s.get_sta()
        logs = s.get_log()
        run_logs = s.get_run_log()
        para = s.get_parameters()
        files = files_in_dir(job_path)
        solver_status = s.solver_status()
        status = {
            'sta': sta[-100:],
            'logs': logs[-5000:],
            'run_logs': run_logs,
            'para': para,
            'files': files,
            'solver_status': solver_status
        }
        return jsonify(status)
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
        p.read_msg()
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
        p.read_msg()
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


@abaqus_bp.route('/prescan_odb_data_origin/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def prescan_odb_data_origin(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    prescan_odb_json_file = os.path.join(job_path, 'prescan_odb.json')
    if os.path.exists(prescan_odb_json_file):
        prescan_odb_dict = load_json(prescan_odb_json_file)
        ztree = json_to_ztree(prescan_odb_dict)
    else:
        ztree = [{"id": 1, "pId": 0, "name": "无"}]
    return ztree


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
        ztree = [{"id": 1, "pId": 0, "name": "未进行预扫描"}]
    return ztree


@abaqus_bp.route('/odb_to_npz_data/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def odb_to_npz_data(project_id, job_id):
    import numpy as np
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    p = Postproc(job_path)
    p.read_msg()
    npz_file = os.path.join(job_path, str(p.job) + '.npz')
    if os.path.exists(npz_file):
        npz = np.load(npz_file, allow_pickle=True, encoding='latin1')
        data = npz['data'][()]
        ztree = json_to_ztree(data)
    else:
        ztree = [{"id": 1, "pId": 0, "name": "未生成npz文件"}]
    return ztree


@abaqus_bp.route('/print_figure/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def print_figure(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    setting_file = os.path.join(job_path, 'print_figure.json')
    if os.path.exists(job_path):
        form = FigureSettingFrom()
        files = files_in_dir(job_path)
        subpaths = subpaths_in_dir(job_path)
        png_files = [f for f in files if (f['name'].split('.')[-1] == 'png' or f['name'].split('.')[-1] == 'gif')]
        p = Postproc(job_path)
        p.read_msg()
        prescan_odb_json_file = os.path.join(job_path, 'prescan_odb.json')
        if p.has_odb():
            if os.path.exists(prescan_odb_json_file):
                prescan_odb_dict = load_json(prescan_odb_json_file)
                from base.utils.common import invariant_dict
                refinement_list = []
                variableLabel_list = []
                for step in prescan_odb_dict['steps'].keys():
                    variableLabel_list += list(prescan_odb_dict['steps'][step]['frames'][0]['fieldOutputs'].keys())
                    fieldOutputs = prescan_odb_dict['steps'][step]['frames'][0]['fieldOutputs']
                    for key in fieldOutputs.keys():
                        for i in fieldOutputs[key]['validInvariants']:
                            refinement_list.append("(INVARIANT, '%s')" % invariant_dict[i])
                        for i in fieldOutputs[key]['componentLabels']:
                            refinement_list.append("(COMPONENT, '%s')" % i)
                refinement_list.append("()")

                form.step.choices = list(prescan_odb_dict['steps'].keys())
                form.variableLabel.choices = sorted(list(set(variableLabel_list)))
                form.refinement.choices = sorted(list(set(refinement_list)))
                form.statusLabel.choices = sorted(list(set(variableLabel_list)))
                form.statusRefinement.choices = sorted(list(set(refinement_list)))
            else:
                flash('请先对odb文件进行预扫描。', 'warning')

            if form.validate_on_submit():
                message = {
                    'width': form.width.data,
                    'height': form.height.data,
                    'imageSize': form.imageSize.data,
                    'legend': form.legend.data,
                    'triad': form.triad.data,
                    'legendPosition': form.legendPosition.data,
                    'mirrorAboutXyPlane': form.mirrorAboutXyPlane.data,
                    'mirrorAboutXzPlane': form.mirrorAboutXzPlane.data,
                    'mirrorAboutYzPlane': form.mirrorAboutYzPlane.data,
                    'plotState': form.plotState.data,
                    'uniformScaleFactor': form.uniformScaleFactor.data,
                    'step': form.step.data,
                    'frame': form.frame.data,
                    'variableLabel': form.variableLabel.data,
                    'refinement': form.refinement.data,
                    'outputPosition': form.outputPosition.data,
                    'visibleEdges': form.visibleEdges.data,
                    'maxAutoCompute': form.maxAutoCompute.data,
                    'maxValue': form.maxValue.data,
                    'minAutoCompute': form.minAutoCompute.data,
                    'minValue': form.minValue.data,
                    'colorMappings': form.colorMappings.data,
                    'projection': form.projection.data,
                    'views': form.views.data,
                    'useStatus': form.useStatus.data,
                    'statusLabel': form.statusLabel.data,
                    'statusPosition': form.statusPosition.data,
                    'statusRefinement': form.statusRefinement.data,
                    'statusMinimum': form.statusMinimum.data,
                    'statusMaximum': form.statusMaximum.data,
                    'animate': form.animate.data,
                    'frameInterval': form.frameInterval.data,
                    'startFrame': form.startFrame.data,
                    'endFrame': form.endFrame.data,
                    'fps': form.fps.data,
                }
                dump_json(setting_file, message)
                proc = p.print_figure()
                with open(os.path.join(job_path, '.print_figure_status'), 'w', encoding='utf-8') as f:
                    f.write('Submitting')
                return redirect(
                    url_for('.print_figure', project_id=project_id, job_id=job_id, form=form, files=png_files,
                            subpaths=subpaths))
        else:
            flash('缺少odb文件。', 'warning')

        if os.path.exists(setting_file):
            try:
                message = load_json(setting_file)
                form.width.data = message['width']
                form.height.data = message['height']
                form.imageSize.data = message['imageSize']
                form.legend.data = message['legend']
                form.triad.data = message['triad']
                form.legendPosition.data = message['legendPosition']
                form.mirrorAboutXyPlane.data = message['mirrorAboutXyPlane']
                form.mirrorAboutXzPlane.data = message['mirrorAboutXzPlane']
                form.mirrorAboutYzPlane.data = message['mirrorAboutYzPlane']
                form.plotState.data = message['plotState']
                form.uniformScaleFactor.data = message['uniformScaleFactor']
                form.step.data = message['step']
                form.frame.data = message['frame']
                form.variableLabel.data = message['variableLabel']
                form.refinement.data = message['refinement']
                form.outputPosition.data = message['outputPosition']
                form.visibleEdges.data = message['visibleEdges']
                form.maxAutoCompute.data = message['maxAutoCompute']
                form.maxValue.data = message['maxValue']
                form.minAutoCompute.data = message['minAutoCompute']
                form.minValue.data = message['minValue']
                form.colorMappings.data = message['colorMappings']
                form.projection.data = message['projection']
                form.views.data = message['views']
                form.useStatus.data = message['useStatus']
                form.statusLabel.data = message['statusLabel']
                form.statusPosition.data = message['statusPosition']
                form.statusRefinement.data = message['statusRefinement']
                form.statusMinimum.data = message['statusMinimum']
                form.statusMaximum.data = message['statusMaximum']
                form.animate.data = message['animate']
                form.frameInterval.data = message['frameInterval']
                form.startFrame.data = message['startFrame']
                form.endFrame.data = message['endFrame']
                form.fps.data = message['fps']
            except KeyError:
                pass

        status = get_job_status(abaqus_path, project_id, job_id)
        logs = p.get_print_figure_log()
        return render_template('abaqus/print_figure.html', project_id=project_id, job_id=job_id, form=form, logs=logs,
                               status=status, files=png_files, subpaths=subpaths)
    else:
        abort(404)


@abaqus_bp.route('/print_figure_dict/<int:project_id>/<int:job_id>')
def print_figure_dict(project_id, job_id):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    prescan_odb_json_file = os.path.join(job_path, 'prescan_odb.json')
    print_figure_dict = {}
    if os.path.exists(prescan_odb_json_file):
        prescan_odb_dict = load_json(prescan_odb_json_file)
        for step in prescan_odb_dict['steps'].keys():
            print_figure_dict[step] = {}
            fieldOutputs = prescan_odb_dict['steps'][step]['frames'][0]['fieldOutputs']
            from base.utils.common import invariant_dict
            print_figure_dict[step]['refinement'] = {}
            print_figure_dict[step]['outputPosition'] = {}
            for key in fieldOutputs.keys():
                print_figure_dict[step]['refinement'][key] = []
                print_figure_dict[step]['outputPosition'][key] = fieldOutputs[key]['locations'][0]['position']
                for i in fieldOutputs[key]['validInvariants']:
                    print_figure_dict[step]['refinement'][key].append("(INVARIANT, '%s')" % invariant_dict[i])
                for i in fieldOutputs[key]['componentLabels']:
                    print_figure_dict[step]['refinement'][key].append("(COMPONENT, '%s')" % i)
                if len(print_figure_dict[step]['refinement'][key]) == 0:
                    print_figure_dict[step]['refinement'][key].append("()")
    return jsonify(print_figure_dict)


@abaqus_bp.route('/print_figure_gif/<int:project_id>/<int:job_id>/<path:pathname>')
def print_figure_gif(project_id, job_id, pathname):
    abaqus_path = current_app.config['ABAQUS_PATH']
    job_path = os.path.join(abaqus_path, str(project_id), str(job_id))
    gif_path = os.path.join(job_path, str(pathname))
    make_gif(job_path, gif_path, 8)
    return redirect(url_for('.print_figure', project_id=project_id, job_id=job_id))


@abaqus_bp.route('/manage_templates', methods=['GET', 'POST'])
@login_required
def manage_templates():
    return render_template('abaqus/manage_templates.html')


@abaqus_bp.route('/templates_status')
@login_required
def templates_status():
    data = templates_detail(current_app.config['ABAQUS_TEMPLATE_PATH'])
    return jsonify(data)


@abaqus_bp.route('/create_template', methods=['GET', 'POST'])
@login_required
def create_template():
    form = TemplateForm()

    if form.validate_on_submit():
        templates_path = current_app.config['ABAQUS_TEMPLATE_PATH']
        template_id = create_id(templates_path)
        template_path = os.path.join(templates_path, str(template_id))
        make_dir(template_path)
        message = {
            'name': form.name.data,
            'descript': form.descript.data,
            'job': form.job.data,
            'user': form.user.data,
            'cpus': form.cpus.data
        }
        msg_file = os.path.join(template_path, '.template_msg')
        dump_json(msg_file, message)
        return redirect(url_for('.view_template', template_id=template_id))

    return render_template('abaqus/create_template.html', form=form)


@abaqus_bp.route('/view_template/<int:template_id>', methods=['GET', 'POST'])
@login_required
def view_template(template_id):
    templates_path = current_app.config['ABAQUS_TEMPLATE_PATH']
    template_path = os.path.join(templates_path, str(template_id))
    form = UploadForm()
    if form.validate_on_submit():
        f = form.filename.data
        f.save(os.path.join(template_path, f.filename))
        flash('上传文件%s成功。' % f.filename, 'success')
        return redirect(url_for('abaqus.view_template', template_id=template_id))
    if os.path.exists(template_path):
        status = get_template_status(templates_path, template_id)
        files = files_in_dir(template_path)
        return render_template('abaqus/view_template.html', template_id=template_id, status=status, files=files,
                               form=form)
    else:
        abort(404)


@abaqus_bp.route('/edit_template/<int:template_id>', methods=['GET', 'POST'])
@login_required
def edit_template(template_id):
    form = TemplateForm()
    templates_path = current_app.config['ABAQUS_TEMPLATE_PATH']
    template_path = os.path.join(templates_path, str(template_id))
    msg_file = os.path.join(template_path, '.template_msg')

    if form.validate_on_submit():
        message = {
            'name': form.name.data,
            'descript': form.descript.data,
            'job': form.job.data,
            'user': form.user.data,
            'cpus': form.cpus.data
        }
        dump_json(msg_file, message)
        return redirect(url_for('.view_template', template_id=template_id))

    message = load_json(msg_file)
    form.name.data = message['name']
    form.descript.data = message['descript']
    form.job.data = message['job']
    form.user.data = message['user']
    form.cpus.data = message['cpus']
    return render_template('abaqus/create_template.html', form=form)


@abaqus_bp.route('/open_template/<int:template_id>')
@login_required
def open_template(template_id):
    templates_path = current_app.config['ABAQUS_TEMPLATE_PATH']
    template_path = os.path.join(templates_path, str(template_id))
    if os.path.exists(template_path):
        cmd = 'explorer %s' % template_path
        proc = subprocess.run(cmd)
        return redirect(url_for('.view_template', template_id=template_id))
    else:
        abort(404)


@abaqus_bp.route('/get_template_file/<int:template_id>/<path:filename>')
@login_required
def get_template_file(template_id, filename):
    return send_from_directory(os.path.join(current_app.config['ABAQUS_TEMPLATE_PATH'], str(template_id)), filename)


@abaqus_bp.route('/delete_template_file/<int:template_id>/<path:filename>')
@login_required
def delete_template_file(template_id, filename):
    templates_path = current_app.config['ABAQUS_TEMPLATE_PATH']
    file = os.path.join(templates_path, str(template_id), str(filename))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'warning')
        return redirect(url_for('.view_template', template_id=template_id))
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(url_for('.view_template', template_id=template_id))


@abaqus_bp.route('/postproc', methods=['GET', 'POST'])
@login_required
def postproc():
    abaqus_post_path = current_app.config['ABAQUS_POST_PATH']
    setting_file = os.path.join(abaqus_post_path, 'postproc.json')
    prescan_status_file = os.path.join(abaqus_post_path, '.prescan_status')
    odb_json_file = os.path.join(abaqus_post_path, 'prescan_odb.json')
    odb_to_npz_file = os.path.join(abaqus_post_path, 'odb_to_npz.json')

    if os.path.exists(setting_file):
        message = load_json(setting_file)
    else:
        message = {}

    if os.path.exists(prescan_status_file):
        with open(prescan_status_file, 'r', encoding='utf-8') as f:
            prescan_status = f.read()
    else:
        prescan_status = 'None'

    form_odb = OdbForm()
    if form_odb.validate_on_submit():
        odb_name = form_odb.odb.data
        message['odb_name'] = form_odb.odb.data
        job_name = odb_name.split('.')[0]
        if os.path.exists(odb_name):
            p = Postproc(abaqus_post_path, job=job_name)
            proc = p.prescan_odb()
            with open(os.path.join(abaqus_post_path, '.prescan_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
            flash('预扫描开始', 'success')
            dump_json(setting_file, message)
        else:
            if os.path.exists(odb_json_file):
                os.remove(odb_json_file)
            flash('%s不存在。' % odb_name, 'warning')
        return redirect(request.referrer)

    if request.method == 'POST':
        data = request.form.to_dict()
        print(data)
        variables = eval('[' + data['variable_id'] + ']')
        frames = eval('[' + data['frame_id'] + ']')
        regions = eval('[' + data['region_id'] + ']')

        steps = []
        for frame in frames:
            if frame[0] not in steps:
                steps.append(frame[0])

        new_frames = []
        for step in steps:
            step_frames = [step, []]
            for frame in frames:
                if frame[0] == step:
                    step_frames[1].append(frame[1])
            new_frames.append(step_frames)

        message = load_json(setting_file)
        odb_path = os.path.abspath(message['odb_name'])

        odb_to_npz_dict = {
            "Frames": new_frames,
            "Regions": regions,
            "Variables": variables,
            "ODB": [odb_path]
        }

        dump_json(odb_to_npz_file, odb_to_npz_dict)

    if os.path.exists(odb_json_file):
        variables, regions, frames = read_prescan(odb_json_file)
    else:
        variables = {}
        regions = []
        frames = []

    if os.path.exists(odb_to_npz_file):
        odb_to_npz_json = load_json(odb_to_npz_file)
    else:
        odb_to_npz_json = ''

    return render_template('abaqus/postproc.html', form_odb=form_odb, filename=odb_json_file, variables=variables,
                           regions=regions, frames=frames, odb_to_npz_json=odb_to_npz_json)


@abaqus_bp.route('/postproc_prescan_odb_data/<path:filename>', methods=['GET', 'POST'])
@login_required
def postproc_prescan_odb_data(filename):
    if os.path.exists(filename):
        prescan_odb_dict = load_json(filename)
        ztree = odb_json_to_ztree(prescan_odb_dict, url_for(
            'static', filename='zTree/icons/'))
    else:
        ztree = [{"id": 1, "pId": 0, "name": "未进行预扫描"}]
    return ztree


# @abaqus_bp.route('/postproc_prescan_odb/<path:odbname>')
# @login_required
# def postproc_prescan_odb(odbname):
#     dirname = os.path.dirname(odbname)
#     basename = os.path.basename(odbname)
#     jobname = basename.split('.')[0]
#     if os.path.exists(odbname):
#         p = Postproc(dirname, job=jobname)
#         proc = p.prescan_odb()
#         with open(os.path.join(job_path, '.prescan_status'), 'w', encoding='utf-8') as f:
#             f.write('Submitting')
#             flash('预扫描开始', 'success')
#         return redirect(request.referrer)
#     else:
#         abort(404)


@abaqus_bp.route('/prescan')
@login_required
def prescan():
    return render_template('abaqus/prescan.html')


@abaqus_bp.route('/prescan_data', methods=['GET', 'POST'])
@login_required
def prescan_data():
    odb_json_file = 'H:\\files\\abaqus\\1\\1\\prescan_odb.json'
    with open(odb_json_file, 'r', encoding='utf-8') as f:
        odb_dict = json.load(f)
    ztree = json_to_ztree(odb_dict)
    return ztree
