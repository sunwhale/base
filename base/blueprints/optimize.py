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

from base.forms.optimize import UploadForm, OptimizeForm
from base.global_var import event_source
from base.utils.abaqus.Postproc import Postproc
from base.utils.abaqus.Preproc import Preproc
from base.utils.abaqus.Solver import Solver
from base.utils.abaqus.add_phasefield_layer import add_phasefield_layer as add_phasefield_layer_abaqus
from base.utils.common import make_dir, dump_json, load_json
from base.utils.dir_status import (create_id, files_in_dir, subpaths_in_dir, get_job_status, get_project_status, get_optimize_status, project_jobs_detail,
                                   optimizes_detail, materials_detail, projects_detail, preprocs_detail, sub_dirs_int, sub_dirs, file_time)
from base.utils.events_new import update_events_new
from base.utils.make_gif import make_gif
from base.utils.read_prescan import read_prescan
from base.utils.tree import json_to_ztree, odb_json_to_ztree

optimize_bp = Blueprint('optimize', __name__)


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
            'descript': form.descript.data
        }
        msg_file = os.path.join(optimize_path, '.optimize_msg')
        dump_json(msg_file, message)
        optimize_file = os.path.join(optimize_path, 'optimize.json')
        dump_json(optimize_file, {})
        flash('项目创建成功。', 'success')
        return redirect(url_for('.view_optimize', optimize_id=optimize_id))

    return render_template('optimize/create_optimize.html', form=form)


@optimize_bp.route('/edit_optimize/<int:optimize_id>', methods=['GET', 'POST'])
@login_required
def edit_optimize(optimize_id):
    form = MaterialForm()
    optimizes_path = current_app.config['OPTIMIZE_PATH']
    optimize_path = os.path.join(optimizes_path, str(optimize_id))
    msg_file = os.path.join(optimize_path, '.optimize_msg')

    if form.validate_on_submit():
        message = {
            'name': form.name.data,
            'type': form.type.data,
            'descript': form.descript.data
        }
        dump_json(msg_file, message)
        return redirect(url_for('.view_optimize', optimize_id=optimize_id))

    message = load_json(msg_file)
    form.name.data = message['name']
    form.type.data = message['type']
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

    form_upload = UploadForm()
    if form_upload.validate_on_submit():
        f = form_upload.filename.data
        f.save(os.path.join(optimize_path, f.filename))
        flash('上传文件%s成功。' % f.filename, 'success')
        return redirect(url_for('optimize.view_optimize', optimize_id=optimize_id))

    if os.path.exists(optimize_path):
        status = get_optimize_status(optimizes_path, optimize_id)
        files = files_in_dir(optimize_path)
        return render_template('optimize/view_optimize.html', optimize_id=optimize_id, status=status, files=files, form_upload=form_upload)
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
