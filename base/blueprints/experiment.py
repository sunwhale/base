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

from base.forms.experiment import ExperimentForm, UploadForm, SpecimenForm, ParameterForm
from tools.dir_status import (create_id, files_in_dir, subpaths_in_dir, get_job_status,
                              get_experiment_status, get_specimen_status,
                              experiments_detail, experiment_specimens_detail, sub_dirs_int)
from tools.common import make_dir, dump_json, load_json
from tools.abaqus.Solver import Solver

experiment_bp = Blueprint('experiment', __name__)


@experiment_bp.route('/manage_experiments', methods=['GET', 'POST'])
@login_required
def manage_experiments():
    return render_template('experiment/manage_experiments.html')


@experiment_bp.route('/experiments_status')
@login_required
def experiments_status():
    data = experiments_detail(current_app.config['EXPERIMENT_PATH'])
    return jsonify(data)


@experiment_bp.route('/create_experiment', methods=['GET', 'POST'])
@login_required
def create_experiment():
    form = ExperimentForm()

    if form.validate_on_submit():
        experiments_path = current_app.config['EXPERIMENT_PATH']
        experiment_id = create_id(experiments_path)
        experiment_path = os.path.join(experiments_path, str(experiment_id))
        make_dir(experiment_path)
        message = {
            'name': form.name.data,
            'type': form.type.data,
            'standard': form.standard.data,
            'parameters': form.parameters.data,
            'descript': form.descript.data
        }
        msg_file = os.path.join(experiment_path, '.experiment_msg')
        dump_json(msg_file, message)
        para_file = os.path.join(experiment_path, 'parameters.inp')
        with open(para_file, 'w', encoding='utf-8') as f:
            f.write(message['parameters'].replace('\r', ''))
        flash('项目创建成功。', 'success')
        return redirect(url_for('.view_experiment', experiment_id=experiment_id))

    return render_template('experiment/create_experiment.html', form=form)


@experiment_bp.route('/edit_experiment/<int:experiment_id>', methods=['GET', 'POST'])
@login_required
def edit_experiment(experiment_id):
    form = ExperimentForm()
    experiments_path = current_app.config['EXPERIMENT_PATH']
    experiment_path = os.path.join(experiments_path, str(experiment_id))
    msg_file = os.path.join(experiment_path, '.experiment_msg')

    if form.validate_on_submit():
        message = {
            'name': form.name.data,
            'type': form.type.data,
            'standard': form.standard.data,
            'parameters': form.parameters.data,
            'descript': form.descript.data
        }
        dump_json(msg_file, message)
        para_file = os.path.join(experiment_path, 'parameters.inp')
        with open(para_file, 'w', encoding='utf-8') as f:
            f.write(message['parameters'].replace('\r', ''))
        return redirect(url_for('.view_experiment', experiment_id=experiment_id))

    message = load_json(msg_file)
    form.name.data = message['name']
    form.type.data = message['type']
    form.standard.data = message['standard']
    form.parameters.data = message['parameters']
    form.descript.data = message['descript']
    return render_template('experiment/create_experiment.html', form=form)


@experiment_bp.route('/delete_experiment/<int:experiment_id>')
@login_required
def delete_experiment(experiment_id):
    experiments_path = current_app.config['EXPERIMENT_PATH']
    experiment_path = os.path.join(experiments_path, str(experiment_id))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'warning')
        return redirect(url_for('.manage_experiments'))
    if os.path.exists(experiment_path):
        shutil.rmtree(experiment_path)
        flash('ABAQUS项目%s删除成功。' % experiment_id, 'success')
    else:
        flash('ABAQUS项目%s不存在。' % experiment_id, 'warning')
    return redirect(url_for('.manage_experiments'))


@experiment_bp.route('/view_experiment/<int:experiment_id>', methods=['GET', 'POST'])
@login_required
def view_experiment(experiment_id):
    experiments_path = current_app.config['EXPERIMENT_PATH']
    experiment_path = os.path.join(experiments_path, str(experiment_id))
    s = Solver(experiment_path)
    parameters = s.parameter_keys()
    form_upload = UploadForm()
    if form_upload.validate_on_submit():
        f = form_upload.filename.data
        f.save(os.path.join(experiment_path, f.filename))
        flash('上传文件%s成功。' % f.filename, 'success')
        return redirect(url_for('experiment.view_experiment', experiment_id=experiment_id))

    if os.path.exists(experiment_path):
        status = get_experiment_status(experiments_path, experiment_id)
        files = files_in_dir(experiment_path)
        return render_template('experiment/view_experiment.html', experiment_id=experiment_id, status=status,
                               files=files, form_upload=form_upload, parameters=parameters)
    else:
        abort(404)


@experiment_bp.route('/open_experiment/<int:experiment_id>')
@login_required
def open_experiment(experiment_id):
    experiments_path = current_app.config['EXPERIMENT_PATH']
    experiment_path = os.path.join(experiments_path, str(experiment_id))
    print(experiment_path)
    if os.path.exists(experiment_path):
        cmd = 'explorer %s' % experiment_path
        proc = subprocess.run(cmd)
        return redirect(url_for('.view_experiment', experiment_id=experiment_id))
    else:
        abort(404)


@experiment_bp.route('/get_experiment_file/<int:experiment_id>/<path:filename>')
@login_required
def get_experiment_file(experiment_id, filename):
    return send_from_directory(os.path.join(current_app.config['EXPERIMENT_PATH'], str(experiment_id)), filename)


@experiment_bp.route('/delete_experiment_file/<int:experiment_id>/<path:filename>')
@login_required
def delete_experiment_file(experiment_id, filename):
    experiments_path = current_app.config['EXPERIMENT_PATH']
    file = os.path.join(experiments_path, str(experiment_id), str(filename))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'warning')
        return redirect(url_for('.view_experiment', experiment_id=experiment_id))
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(url_for('.view_experiment', experiment_id=experiment_id))


@experiment_bp.route('/create_specimen/<int:experiment_id>', methods=['GET', 'POST'])
@login_required
def create_specimen(experiment_id):
    form = SpecimenForm()
    experiments_path = current_app.config['EXPERIMENT_PATH']
    experiment_path = os.path.join(experiments_path, str(experiment_id))

    if form.validate_on_submit():
        specimen_id = create_id(experiment_path)
        specimen_path = os.path.join(experiment_path, str(specimen_id))
        make_dir(specimen_path)
        message = {
            'name': form.name.data,
            'descript': form.descript.data
        }
        msg_file = os.path.join(specimen_path, '.specimen_msg')
        dump_json(msg_file, message)
        para_file = os.path.join(experiment_path, 'parameters.inp')
        if os.path.exists(para_file):
            shutil.copy(os.path.join(experiment_path, 'parameters.inp'),
                        os.path.join(specimen_path, 'parameters.inp'))

        return redirect(url_for('.view_specimen', experiment_id=experiment_id, specimen_id=specimen_id))

    return render_template('experiment/create_specimen.html', form=form)


@experiment_bp.route('/view_specimen/<int:experiment_id>/<int:specimen_id>', methods=['GET', 'POST'])
@login_required
def view_specimen(experiment_id, specimen_id):
    experiments_path = current_app.config['EXPERIMENT_PATH']
    specimen_path = os.path.join(experiments_path, str(experiment_id), str(specimen_id))
    if os.path.exists(specimen_path):
        form = ParameterForm()
        s = Solver(specimen_path)
        para = s.get_parameters()
        if form.validate_on_submit():
            para = form.para.data
            s.save_parameters(para)
            flash('parameters.inp保存成功。', 'success')
            return redirect(url_for('.view_specimen', experiment_id=experiment_id, specimen_id=specimen_id))
        form.para.data = para
        s.parameters_to_json()
        status = get_specimen_status(experiments_path, experiment_id, specimen_id)
        files = files_in_dir(specimen_path)
        return render_template('experiment/view_specimen.html', experiment_id=experiment_id, specimen_id=specimen_id,
                               status=status, form=form, files=files)
    else:
        abort(404)


@experiment_bp.route('/edit_specimen/<int:experiment_id>/<int:specimen_id>', methods=['GET', 'POST'])
@login_required
def edit_specimen(experiment_id, specimen_id):
    form = SpecimenForm()
    experiments_path = current_app.config['EXPERIMENT_PATH']
    specimen_path = os.path.join(experiments_path, str(experiment_id), str(specimen_id))
    msg_file = os.path.join(specimen_path, '.specimen_msg')
    if form.validate_on_submit():
        message = {
            'name': form.name.data,
            'descript': form.descript.data
        }
        dump_json(msg_file, message)
        return redirect(url_for('.view_specimen', experiment_id=experiment_id, specimen_id=specimen_id))

    message = load_json(msg_file)
    form.name.data = message['name']
    form.descript.data = message['descript']
    return render_template('experiment/create_specimen.html', form=form)


@experiment_bp.route('/delete_specimen/<int:experiment_id>/<int:specimen_id>')
@login_required
def delete_specimen(experiment_id, specimen_id):
    experiments_path = current_app.config['EXPERIMENT_PATH']
    specimen_path = os.path.join(experiments_path, str(experiment_id), str(specimen_id))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'warning')
        return redirect(url_for('.manage_experiments'))
    if os.path.exists(specimen_path):
        shutil.rmtree(specimen_path)
        flash('%s号实验项目%s号试件删除成功。' % (experiment_id, specimen_id), 'success')
    else:
        flash('%s号实验项目%s号试件不存在。' % (experiment_id, specimen_id), 'warning')
    return redirect(url_for('.view_experiment', experiment_id=experiment_id))


@experiment_bp.route('/get_specimen_file/<int:experiment_id>/<int:specimen_id>/<path:filename>')
@login_required
def get_specimen_file(experiment_id, specimen_id, filename):
    return send_from_directory(os.path.join(current_app.config['EXPERIMENT_PATH'], str(experiment_id), str(specimen_id)), filename)


@experiment_bp.route('/delete_specimen_file/<int:experiment_id>/<int:specimen_id>/<path:filename>')
@login_required
def delete_specimen_file(experiment_id, specimen_id, filename):
    experiments_path = current_app.config['EXPERIMENT_PATH']
    file = os.path.join(experiments_path, str(experiment_id), str(specimen_id), str(filename))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'warning')
        return redirect(url_for('.view_job', project_id=experiment_id, job_id=specimen_id))
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(request.referrer or url_for('.view_job', project_id=experiment_id, job_id=specimen_id))


@experiment_bp.route('/experiment_specimens_status/<int:experiment_id>')
def experiment_specimens_status(experiment_id):
    experiments_path = current_app.config['EXPERIMENT_PATH']
    data = experiment_specimens_detail(experiments_path, experiment_id)
    return jsonify(data)
