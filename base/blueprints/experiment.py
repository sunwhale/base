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

from base.forms.experiment import ExperimentForm, UploadForm
from tools.dir_status import (create_id, files_in_dir, subpaths_in_dir, get_job_status,
                              get_experiment_status, get_template_status,
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
        experiment_path = current_app.config['EXPERIMENT_PATH']
        experiment_id = create_id(experiment_path)
        experiment_path = os.path.join(experiment_path, str(experiment_id))
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
    form = ProjectForm()
    experiment_path = current_app.config['EXPERIMENT_PATH']
    experiment_path = os.path.join(experiment_path, str(experiment_id))
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


@experiment_bp.route('/view_experiment/<int:experiment_id>', methods=['GET', 'POST'])
@login_required
def view_experiment(experiment_id):
    experiment_path = current_app.config['EXPERIMENT_PATH']
    experiment_path = os.path.join(experiment_path, str(experiment_id))
    form_upload = UploadForm()
    if form_upload.validate_on_submit():
        f = form_upload.filename.data
        f.save(os.path.join(experiment_path, f.filename))
        flash('上传文件%s成功。' % f.filename, 'success')
        return redirect(url_for('experiment.view_experiment', experiment_id=experiment_id))
    
    if os.path.exists(experiment_path):
        status = get_experiment_status(experiment_path, experiment_id)
        files = files_in_dir(experiment_path)
        return render_template('experiment/view_experiment.html', experiment_id=experiment_id, status=status, files=files, form_upload=form_upload)
    else:
        abort(404)