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

from base.forms.flow import UploadForm, FlowForm, JobForm, F1From
from base.global_var import event_source
from base.utils.abaqus.Postproc import Postproc
from base.utils.abaqus.Preproc import Preproc
from base.utils.abaqus.Solver import Solver
from base.utils.abaqus.add_phasefield_layer import add_phasefield_layer as add_phasefield_layer_abaqus
from base.utils.common import make_dir, dump_json, load_json
from base.utils.dir_status import (create_id, files_in_dir, subpaths_in_dir, get_job_status, get_project_status, get_template_status, project_jobs_detail,
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


@optimize_bp.route('/edit_flow/<int:flow_id>', methods=['GET', 'POST'])
@login_required
def edit_flow(flow_id):
    form = FlowForm()
    optimizes_path = current_app.config['FLOW_PATH']
    flow_path = os.path.join(optimizes_path, str(flow_id))
    msg_file = os.path.join(flow_path, '.flow_msg')

    if form.validate_on_submit():
        message = {
            'name': form.name.data,
            'descript': form.descript.data
        }
        dump_json(msg_file, message)
        return redirect(url_for('.manage_optimizes'))

    message = load_json(msg_file)
    form.name.data = message['name']
    form.descript.data = message['descript']
    return render_template('flow/edit_flow.html', form=form)


@optimize_bp.route('/get_flow_file/<int:flow_id>/<path:filename>')
@login_required
def get_flow_file(flow_id, filename):
    return send_from_directory(os.path.join(current_app.config['FLOW_PATH'], str(flow_id)), filename)


@optimize_bp.route('/delete_flow_file/<int:flow_id>/<path:filename>')
@login_required
def delete_flow_file(flow_id, filename):
    flow_path = current_app.config['FLOW_PATH']
    file = os.path.join(flow_path, str(flow_id), str(filename))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'warning')
        return redirect(request.referrer)
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(request.referrer)


@optimize_bp.route('/flow_status/<int:flow_id>', methods=['GET', 'POST'])
@login_required
def flow_status(flow_id):
    optimizes_path = current_app.config['FLOW_PATH']
    flow_path = os.path.join(optimizes_path, str(flow_id))
    if os.path.exists(flow_path):
        p = Preproc(flow_path)
        p.read_msg()
        logs = p.get_rpy()
        run_logs = p.get_run_log()
        files = files_in_dir(flow_path)
        flow_status = p.preproc_status()
        status = {
            'logs': logs,
            'run_logs': run_logs,
            'files': files,
            'flow_status': flow_status
        }
        return jsonify(status)
    else:
        abort(404)
