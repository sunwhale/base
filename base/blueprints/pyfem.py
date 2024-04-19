# -*- coding: utf-8 -*-
"""

"""
import os
import shutil
import subprocess
import time
import uuid

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

from base.forms.pyfem import (JobForm, ParameterForm, ProjectForm, ImportTemplateForm, UploadForm)
from base.global_var import event_source
from base.utils.common import make_dir, dump_json, load_json
from base.utils.dir_status import (create_id, files_in_dir, get_job_status, get_project_status, project_jobs_detail, projects_detail, templates_detail,
                                   sub_dirs_int, sub_dirs)
from base.utils.events_new import update_events_new
from base.utils.pyfem.Solver import Solver

pyfem_bp = Blueprint('pyfem', __name__)


@pyfem_bp.route('/manage_projects', methods=['GET', 'POST'])
@login_required
def manage_projects():
    return render_template('pyfem/manage_projects.html')


@pyfem_bp.route('/create_project', methods=['GET', 'POST'])
@login_required
def create_project():
    form = ProjectForm()

    if form.validate_on_submit():
        pyfem_path = current_app.config['PYFEM_PATH']
        project_id = create_id(pyfem_path)
        project_path = os.path.join(pyfem_path, str(project_id))
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

    return render_template('pyfem/create_project.html', form=form)


@pyfem_bp.route('/projects_status')
@login_required
def projects_status():
    data = projects_detail(current_app.config['PYFEM_PATH'])
    return jsonify(data)


@pyfem_bp.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    form = ProjectForm()
    pyfem_path = current_app.config['PYFEM_PATH']
    project_path = os.path.join(pyfem_path, str(project_id))
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
    return render_template('pyfem/create_project.html', form=form)


@pyfem_bp.route('/delete_project/<int:project_id>')
@login_required
def delete_project(project_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    project_path = os.path.join(pyfem_path, str(project_id))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'warning')
        return redirect(url_for('.manage_projects'))
    if os.path.exists(project_path):
        shutil.rmtree(project_path)
        flash('PYFEM项目%s删除成功。' % project_id, 'success')
    else:
        flash('PYFEM项目%s不存在。' % project_id, 'warning')
    return redirect(url_for('.manage_projects'))


@pyfem_bp.route('/view_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def view_project(project_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    project_path = os.path.join(pyfem_path, str(project_id))
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
        return redirect(url_for('pyfem.view_project', project_id=project_id))

    if form_template.validate_on_submit():
        template_id = int(form_template.name.data.split('_')[0])
        template_path = os.path.join(templates_path, str(template_id))
        files = files_in_dir(template_path)
        for file in files:
            shutil.copy(os.path.join(template_path, file['name']),
                        os.path.join(project_path, file['name']))
            flash('从模板导入文件%s成功。' % file['name'], 'success')
        return redirect(url_for('pyfem.view_project', project_id=project_id))

    if request.method == 'POST':
        data = request.form.to_dict()
        if 'queue_value' in data.keys():
            queue_list = [int(job_id)
                          for job_id in data['queue_value'].split(',') if job_id != '']
            queue_type = data['queue_type']
            new_jobs = []
            if queue_type == 'Solver':
                for job_id in queue_list:
                    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
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
                    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
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
                    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
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
        status = get_project_status(pyfem_path, project_id)
        files = files_in_dir(project_path)
        return render_template('pyfem/view_project.html', project_id=project_id, status=status, files=files,
                               parameters=parameters, form_upload=form_upload, form_template=form_template)
    else:
        abort(404)


@pyfem_bp.route('/open_project/<int:project_id>')
@login_required
def open_project(project_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    project_path = os.path.join(pyfem_path, str(project_id))
    if os.path.exists(project_path):
        cmd = 'explorer %s' % project_path
        proc = subprocess.run(cmd)
        return redirect(url_for('.view_project', project_id=project_id))
    else:
        abort(404)


@pyfem_bp.route('/get_project_file/<int:project_id>/<path:filename>')
@login_required
def get_project_file(project_id, filename):
    return send_from_directory(os.path.join(current_app.config['PYFEM_PATH'], str(project_id)), filename)


@pyfem_bp.route('/delete_project_file/<int:project_id>/<path:filename>')
@login_required
def delete_project_file(project_id, filename):
    pyfem_path = current_app.config['PYFEM_PATH']
    file = os.path.join(pyfem_path, str(project_id), str(filename))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'warning')
        return redirect(url_for('.view_project', project_id=project_id))
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(url_for('.view_project', project_id=project_id))


@pyfem_bp.route('/synchronize_project_file/<int:project_id>/<path:filename>')
@login_required
def synchronize_project_file(project_id, filename):
    pyfem_path = current_app.config['PYFEM_PATH']
    project_path = os.path.join(pyfem_path, str(project_id))
    file = os.path.join(pyfem_path, str(project_id), str(filename))
    if os.path.exists(file):
        for job_path in sub_dirs(project_path):
            shutil.copy(os.path.join(project_path, filename), os.path.join(project_path, job_path, filename))
        flash('文件%s已经同步至所有算例。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(request.referrer or url_for('.view_project', project_id=project_id))


@pyfem_bp.route('/create_job/<int:project_id>', methods=['GET', 'POST'])
@login_required
def create_job(project_id):
    form = JobForm()
    pyfem_path = current_app.config['PYFEM_PATH']
    project_path = os.path.join(pyfem_path, str(project_id))

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
    return render_template('pyfem/create_job.html', form=form)


@pyfem_bp.route('/view_job/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def view_job(project_id, job_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
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
        status = get_job_status(pyfem_path, project_id, job_id)
        return render_template('pyfem/view_job.html', project_id=project_id, job_id=job_id, status=status,
                               logs=logs[-5000:], sta=sta[-100:], run_logs=run_logs, form=form,
                               solver_status=solver_status, files=files)
    else:
        abort(404)


@pyfem_bp.route('/job_status/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def job_status(project_id, job_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
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


@pyfem_bp.route('/project_jobs_status/<int:project_id>')
def project_jobs_status(project_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    job_id_list = sub_dirs_int(os.path.join(pyfem_path, str(project_id)))
    for job_id in job_id_list:
        job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
        s = Solver(job_path)
        s.solver_status()
    data = project_jobs_detail(pyfem_path, project_id)
    return jsonify(data)


@pyfem_bp.route('/edit_job/<int:project_id>/<int:job_id>', methods=['GET', 'POST'])
@login_required
def edit_job(project_id, job_id):
    form = JobForm()
    pyfem_path = current_app.config['PYFEM_PATH']
    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
    msg_file = os.path.join(job_path, '.job_msg')

    if form.validate_on_submit():
        message = {
            'job': form.job.data,
            'user': form.user.data,
            'cpus': form.cpus.data
        }
        dump_json(msg_file, message)
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))

    message = load_json(msg_file)
    form.job.data = message['job']
    form.user.data = message['user']
    form.cpus.data = message['cpus']
    return render_template('pyfem/create_job.html', form=form)


@pyfem_bp.route('/delete_job/<int:project_id>/<int:job_id>')
@login_required
def delete_job(project_id, job_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'warning')
        return redirect(url_for('.manage_projects'))
    if os.path.exists(job_path):
        shutil.rmtree(job_path)
        flash('ABAQUS项目%s算例%s删除成功。' % (project_id, job_id), 'success')
    else:
        flash('ABAQUS项目%s算例%s不存在。' % (project_id, job_id), 'warning')
    return redirect(url_for('.view_project', project_id=project_id))


@pyfem_bp.route('/open_job/<int:project_id>/<int:job_id>')
@login_required
def open_job(project_id, job_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        cmd = 'explorer %s' % job_path
        proc = subprocess.run(cmd)
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@pyfem_bp.route('/run_job/<int:project_id>/<int:job_id>')
@login_required
def run_job(project_id, job_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        s.read_msg()
        s.clear()
        if s.check_files():
            proc = s.run()
            with open(os.path.join(job_path, '.solver_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
            with open(os.path.join(job_path, '.pid'), 'w', encoding='utf-8') as f:
                f.write(f'{proc.pid}')
            print(proc)
            current_app.config['PYFEM_PROC_DICT'][f'{project_id}{job_id}'] = proc
            print(current_app.config['PYFEM_PROC_DICT'])
        else:
            flash('缺少必要的计算文件。', 'warning')
        return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@pyfem_bp.route('/terminate_job/<int:project_id>/<int:job_id>')
@login_required
def terminate_job(project_id, job_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        s.read_msg()
        with open(os.path.join(job_path, '.pid'), 'r', encoding='utf-8') as f:
            pid = int(f.read())

        proc = current_app.config['PYFEM_PROC_DICT'][f'{project_id}{job_id}']

        if current_app.config['IS_WIN']:
            cmd = 'taskkill /t /f /pid {}'.format(pid)
            print(cmd)
            os.system(cmd)
            with open(os.path.join(job_path, '.solver_status'), 'w', encoding='utf-8') as f:
                f.write('Stopped')
            with open(os.path.join(job_path, '{}.log'.format(s.job)), 'a', encoding='utf-8') as f:
                f.write('EXITED')
        else:
            import signal
            os.killpg(pid, signal.SIGTERM)
            with open(os.path.join(job_path, '.solver_status'), 'w', encoding='utf-8') as f:
                f.write('Stopped')
            with open(os.path.join(job_path, '{}.log'.format(s.job)), 'a', encoding='utf-8') as f:
                f.write('EXITED')

        return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@pyfem_bp.route('/reset_job/<int:project_id>/<int:job_id>')
@login_required
def reset_job(project_id, job_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
    if os.path.exists(job_path):
        s = Solver(job_path)
        s.read_msg()
        s.clear()
        flash('项目文件重置成功。', 'success')
        return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
    else:
        abort(404)


@pyfem_bp.route('/join_job/<int:project_id>/<int:job_id>')
@login_required
def join_job(project_id, job_id):
    pyfem_path = current_app.config['PYFEM_PATH']
    job_path = os.path.join(pyfem_path, str(project_id), str(job_id))
    new_jobs = []
    if os.path.exists(job_path):
        s = Solver(job_path)
        s.read_msg()
        job = {'type': 'PyfemSolver',
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
        make_dir(current_app.config['QUEUE_PATH'])
        update_events_new(new_jobs, current_app.config['EVENTS_NEW'])
        flash('选中的算例已经提交到计算队列。', 'success')
        return redirect(url_for('queue.view_queue'))
    else:
        abort(404)


@pyfem_bp.route('/get_job_file/<int:project_id>/<int:job_id>/<path:filename>')
@login_required
def get_job_file(project_id, job_id, filename):
    return send_from_directory(os.path.join(current_app.config['PYFEM_PATH'], str(project_id), str(job_id)), filename)


@pyfem_bp.route('/delete_job_file/<int:project_id>/<int:job_id>/<path:filename>')
@login_required
def delete_job_file(project_id, job_id, filename):
    pyfem_path = current_app.config['PYFEM_PATH']
    file = os.path.join(pyfem_path, str(project_id), str(job_id), str(filename))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'warning')
        return redirect(url_for('.view_job', project_id=project_id, job_id=job_id))
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(request.referrer or url_for('.view_job', project_id=project_id, job_id=job_id))
