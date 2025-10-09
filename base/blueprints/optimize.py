# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil
import subprocess
import time
import uuid
from markupsafe import Markup

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

from base.forms.optimize import UploadForm, OptimizeForm, ParameterForm, ExperimentForm
from base.global_var import event_source
from base.utils.optimize.Solver import Solver
from base.utils.common import make_dir, dump_json, load_json
from base.utils.dir_status import (create_id, files_in_dir, subpaths_in_dir, get_job_status, get_project_status, get_optimize_status, project_jobs_detail,
                                   optimizes_detail, experiments_detail, projects_detail, preprocs_detail, sub_dirs_int, sub_dirs, file_time)
from base.utils.events_new import update_events_new
from base.utils.make_gif import make_gif
from base.utils.read_prescan import read_prescan
from base.utils.tree import json_to_ztree, odb_json_to_ztree

optimize_bp = Blueprint('optimize', __name__)


def simple_parse(input_str):
    """
    简化的解析函数
    """
    if not isinstance(input_str, str) or not input_str.strip():
        return []

    # 分割并去除每个部分的首尾空格
    parts = [part.strip() for part in input_str.split(',')]

    # 检查所有部分是否都非空
    if all(parts):  # all() 会检查列表中所有元素是否为真（非空）
        return parts
    else:
        return []


@optimize_bp.route('/optimizes_status/')
@login_required
def optimizes_status():
    data = optimizes_detail(current_app.config['OPTIMIZE_PATH'])
    return jsonify(data)


@optimize_bp.route('/manage_optimizes/')
@login_required
def manage_optimizes():
    return render_template('optimize/manage_optimizes.html')


@optimize_bp.route('/create_optimize', methods=['GET', 'POST'])
@login_required
def create_optimize():
    form = OptimizeForm()

    if form.validate_on_submit():
        optimizes_path = current_app.config['OPTIMIZE_PATH']
        optimize_id = create_id(optimizes_path)
        optimize_path = os.path.join(optimizes_path, str(optimize_id))
        make_dir(optimize_path)
        uuid_file = os.path.join(optimize_path, '.uuid')
        with open(uuid_file, 'w', encoding='utf-8') as f:
            f.write(str(uuid.uuid4()))
        message = {
            'name': form.name.data,
            'type': form.type.data,
            'para': form.para.data,
            'job': form.job.data,
            'descript': form.descript.data
        }
        msg_file = os.path.join(optimize_path, '.optimize_msg')
        dump_json(msg_file, message)
        optimize_file = os.path.join(optimize_path, 'optimize.json')
        dump_json(optimize_file, {})
        parameters_json_file = os.path.join(optimize_path, 'parameters.json')
        dump_json(parameters_json_file, {})
        experiments_json_file = os.path.join(optimize_path, 'experiments.json')
        dump_json(experiments_json_file, {})
        flash('项目创建成功。', 'success')
        return redirect(url_for('.view_optimize', optimize_id=optimize_id))

    return render_template('optimize/create_optimize.html', form=form)


@optimize_bp.route('/edit_optimize/<int:optimize_id>', methods=['GET', 'POST'])
@login_required
def edit_optimize(optimize_id):
    form = OptimizeForm()
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    optimize_path = os.path.join(optimizes_path, str(optimize_id))
    msg_file = os.path.join(optimize_path, '.optimize_msg')

    if form.validate_on_submit():
        message = {
            'name': form.name.data,
            'type': form.type.data,
            'para': form.para.data,
            'job': form.job.data,
            'descript': form.descript.data
        }
        dump_json(msg_file, message)
        return redirect(url_for('.view_optimize', optimize_id=optimize_id))

    message = load_json(msg_file)
    form.name.data = message['name']
    form.type.data = message['type']
    form.para.data = message['para']
    form.job.data = message['job']
    form.descript.data = message['descript']
    return render_template('optimize/create_optimize.html', form=form)


@optimize_bp.route('/delete_optimize/<int:optimize_id>')
@login_required
def delete_optimize(optimize_id):
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    optimize_path = os.path.join(optimizes_path, str(optimize_id))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'warning')
        return redirect(url_for('.manage_optimizes'))
    if os.path.exists(optimize_path):
        shutil.rmtree(optimize_path)
        flash('实验项目%s删除成功。' % optimize_id, 'success')
    else:
        flash('实验项目%s不存在。' % optimize_id, 'warning')
    return redirect(url_for('.manage_optimizes'))


@optimize_bp.route('/view_optimize/<int:optimize_id>', methods=['GET', 'POST'])
@login_required
def view_optimize(optimize_id):
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    optimize_path = os.path.join(optimizes_path, str(optimize_id))
    parameters_json_file = os.path.join(optimize_path, 'parameters.json')
    experiments_json_file = os.path.join(optimize_path, 'experiments.json')

    upload_form = UploadForm()
    parameter_form = ParameterForm()
    experiment_form = ExperimentForm()

    experiments_path = current_app.config['EXPERIMENT_PATH']
    experiment_dict = experiments_detail(experiments_path)
    experiment_list = []
    for experiment in experiment_dict['data']:
        experiment_list.append('%s_%s' % (experiment['experiment_id'], experiment['name']))

    experiment_form.experiment_id.choices = experiment_list

    if upload_form.submit.data and upload_form.validate():
        f = upload_form.filename.data
        f.save(os.path.join(optimize_path, f.filename))
        flash('上传文件%s成功。' % f.filename, 'success')
        return redirect(url_for('optimize.view_optimize', optimize_id=optimize_id))

    if experiment_form.submit.data and experiment_form.validate():
        data = request.form.to_dict()
        data['EXPERIMENT_PATH'] = current_app.config['EXPERIMENT_PATH']
        if os.path.exists(experiments_json_file):
            dump_json(experiments_json_file, data)
        return redirect(url_for('optimize.view_optimize', optimize_id=optimize_id))

    if parameter_form.submit.data and parameter_form.validate():
        data = request.form.to_dict()
        if os.path.exists(parameters_json_file):
            dump_json(parameters_json_file, data)
        return redirect(url_for('optimize.view_optimize', optimize_id=optimize_id))

    if os.path.exists(optimize_path):
        status = get_optimize_status(optimizes_path, optimize_id)
        files = files_in_dir(optimize_path)
        if os.path.exists(experiments_json_file):
            if 'experiment_id' in load_json(experiments_json_file).keys():
                experiment_form.experiment_id.data = load_json(experiments_json_file)['experiment_id']
        return render_template('optimize/view_optimize.html', optimize_id=optimize_id, status=status, files=files, upload_form=upload_form,
                               experiment_form=experiment_form, parameter_form=parameter_form)
    else:
        abort(404)


@optimize_bp.route('/run_optimize/<int:optimize_id>')
@login_required
def run_optimize(optimize_id):
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    optimize_path = os.path.join(optimizes_path, str(optimize_id))
    if os.path.exists(optimize_path):
        s = Solver(optimize_path)
        s.read_msg()
        s.clear()
        if s.check_files():
            proc = s.run()
            with open(os.path.join(optimize_path, '.solver_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
            with open(os.path.join(optimize_path, '.pid'), 'w', encoding='utf-8') as f:
                f.write(f'{proc.pid}')
            print(proc)
            current_app.config['OPTIMIZE_PROC_DICT'][f'{optimize_id}'] = proc
            print(current_app.config['OPTIMIZE_PROC_DICT'])
        else:
            flash('缺少必要的计算文件。', 'warning')
        return redirect(request.referrer or url_for('.view_optimize', optimize_id=optimize_id))
    else:
        abort(404)


@optimize_bp.route('/terminate_optimize/<int:optimize_id>')
@login_required
def terminate_optimize(optimize_id):
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    optimize_path = os.path.join(optimizes_path, str(optimize_id))
    if os.path.exists(optimize_path):
        s = Solver(optimize_path)
        s.read_msg()
        with open(os.path.join(optimize_path, '.pid'), 'r', encoding='utf-8') as f:
            pid = int(f.read())

        if f'{optimize_id}' in current_app.config['OPTIMIZE_PROC_DICT']:
            proc = current_app.config['OPTIMIZE_PROC_DICT'][f'{optimize_id}']
        else:
            pass

        if current_app.config['IS_WIN']:
            cmd = 'taskkill /t /f /pid {}'.format(pid)
            print(cmd)
            os.system(cmd)
            with open(os.path.join(optimize_path, '.solver_status'), 'w', encoding='utf-8') as f:
                f.write('Stopped')
            with open(os.path.join(optimize_path, '{}.log'.format(s.job)), 'a', encoding='utf-8') as f:
                f.write('EXITED')
        else:
            import signal
            os.killpg(pid, signal.SIGTERM)
            with open(os.path.join(optimize_path, '.solver_status'), 'w', encoding='utf-8') as f:
                f.write('Stopped')
            with open(os.path.join(optimize_path, '{}.log'.format(s.job)), 'a', encoding='utf-8') as f:
                f.write('EXITED')

        return redirect(request.referrer or url_for('.view_optimize', optimize_id=optimize_id))
    else:
        abort(404)


@optimize_bp.route('/reset_optimize/<int:optimize_id>')
@login_required
def reset_optimize(optimize_id):
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    optimize_path = os.path.join(optimizes_path, str(optimize_id))
    if os.path.exists(optimize_path):
        s = Solver(optimize_path)
        s.read_msg()
        s.clear()
        with open(os.path.join(optimize_path, '.solver_status'), 'w', encoding='utf-8') as f:
            f.write('Setting')
        flash('项目文件重置成功。', 'success')
        return redirect(request.referrer or url_for('.view_optimize', optimize_id=optimize_id))
    else:
        abort(404)


@optimize_bp.route('/optimize_job_status/<int:optimize_id>', methods=['GET', 'POST'])
@login_required
def optimize_job_status(optimize_id):
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    optimize_path = os.path.join(optimizes_path, str(optimize_id))
    parameters_json_file = os.path.join(optimize_path, 'parameters.json')
    experiments_json_file = os.path.join(optimize_path, 'experiments.json')
    if os.path.exists(optimize_path):
        s = Solver(optimize_path)
        s.read_msg()
        run_logs = s.get_run_log()
        logs = s.get_log()
        files = files_in_dir(optimize_path)
        solver_status = s.solver_status()
        parameters = load_json(parameters_json_file)
        experiments = load_json(experiments_json_file)
        optimize_status = get_optimize_status(optimizes_path, optimize_id)
        status = {
            'run_logs': run_logs,
            'logs': logs[-50000:],
            'files': files,
            'solver_status': solver_status,
            'parameters': parameters,
            'experiments': experiments,
            'optimize_status': optimize_status
        }
        return jsonify(status)
    else:
        abort(404)


@optimize_bp.route('/open_optimize/<int:optimize_id>')
@login_required
def open_optimize(optimize_id):
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    optimize_path = os.path.join(optimizes_path, str(optimize_id))
    if os.path.exists(optimize_path):
        cmd = 'explorer %s' % optimize_path
        proc = subprocess.run(cmd)
        return redirect(url_for('.view_optimize', optimize_id=optimize_id))
    else:
        abort(404)


@optimize_bp.route('/get_optimize_file/<int:optimize_id>/<path:filename>')
@login_required
def get_optimize_file(optimize_id, filename):
    return send_from_directory(os.path.join(current_app.config['OPTIMIZE_PATH'], str(optimize_id)), filename)


@optimize_bp.route('/delete_optimize_file/<int:optimize_id>/<path:filename>')
@login_required
def delete_optimize_file(optimize_id, filename):
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    file = os.path.join(optimizes_path, str(optimize_id), str(filename))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'warning')
        return redirect(url_for('.view_optimize', optimize_id=optimize_id))
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(url_for('.view_optimize', optimize_id=optimize_id))


@optimize_bp.route('/optimize_status/<int:optimize_id>', methods=['GET', 'POST'])
@login_required
def optimize_status(optimize_id):
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    if os.path.exists(optimizes_path):
        return get_optimize_status(optimizes_path, optimize_id)
    else:
        abort(404)
