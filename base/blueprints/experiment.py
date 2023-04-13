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

from base.forms.experiment import ExperimentForm, UploadForm, SpecimenForm
from tools.dir_status import (create_id, files_in_dir, subpaths_in_dir, get_job_status,
                              get_experiment_status, get_specimen_status,
                              experiments_detail, templates_detail, sub_dirs_int)
from tools.common import make_dir, dump_json, load_json


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
            'descript': form.descript.data
        }
        msg_file = os.path.join(experiment_path, '.experiment_msg')
        dump_json(msg_file, message)
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
            'descript': form.descript.data,
        }
        dump_json(msg_file, message)
        return redirect(url_for('.view_experiment', experiment_id=experiment_id))

    message = load_json(msg_file)
    form.name.data = message['name']
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
    form_upload = UploadForm()
    if form_upload.validate_on_submit():
        f = form_upload.filename.data
        f.save(os.path.join(experiment_path, f.filename))
        flash('上传文件%s成功。' % f.filename, 'success')
        return redirect(url_for('experiment.view_experiment', experiment_id=experiment_id))
    
    if os.path.exists(experiment_path):
        status = get_experiment_status(experiments_path, experiment_id)
        print('status', status)
        files = files_in_dir(experiment_path)
        return render_template('experiment/view_experiment.html', experiment_id=experiment_id, status=status, files=files, form_upload=form_upload)
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
            'specimen': form.specimen.data,
            'descript': form.descript.data,
        }
        msg_file = os.path.join(specimen_path, '.specimen_msg')
        dump_json(msg_file, message)
        return redirect(url_for('.view_specimen', experiment_id=experiment_id, specimen_id=specimen_id))

    return render_template('experiment/create_specimen.html', form=form)


@experiment_bp.route('/view_specimen/<int:experiment_id>/<int:specimen_id>', methods=['GET', 'POST'])
@login_required
def view_specimen(experiment_id, specimen_id):
    experiments_path = current_app.config['EXPERIMENT_PATH']
    specimen_path = os.path.join(experiments_path, str(experiment_id), str(specimen_id))
    if os.path.exists(specimen_path):
        # form = ParameterForm()
        # if form.validate_on_submit():
        #     para = form.para.data
        #     s.save_parameters(para)
        #     flash('parameters.inp保存成功。', 'success')
        #     return redirect(url_for('.view_specimen', experiment_id=experiment_id, specimen_id=specimen_id))
        # form.para.data = para
        status = get_specimen_status(specimen_path, experiment_id, specimen_id)
        return render_template('experiment/view_specimen.html', experiment_id=experiment_id, specimen_id=specimen_id, status=status)
    else:
        abort(404)


@experiment_bp.route('/experiment_specimens_status/<int:experiment_id>')
def experiment_specimens_status(experiment_id):
    # experiments_path = current_app.config['EXPERIMENT_PATH']
    # specimen_id_list = sub_dirs_int(os.path.join(experiments_path, str(experiment_id)))
    # for specimen_id in specimen_id_list:
    #     specimen_path = os.path.join(experiments_path, str(experiment_id), str(specimen_id))
    #     s = Solver(job_path)
    #     s.solver_status()
    # data = experiment_specimenss_detail(experiments_path, experiment_id)
    return jsonify({"data": []})
