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

from base.forms.flow import UploadForm, FlowForm, F1From
from base.global_var import event_source
from base.utils.abaqus.Postproc import Postproc
from base.utils.abaqus.Preproc import Preproc
from base.utils.abaqus.Solver import Solver
from base.utils.abaqus.add_phasefield_layer import add_phasefield_layer as add_phasefield_layer_abaqus
from base.utils.common import make_dir, dump_json, load_json
from base.utils.dir_status import (create_id, files_in_dir, subpaths_in_dir, get_job_status, get_project_status, get_template_status, project_jobs_detail,
                                   flows_detail, materials_detail, get_preproc_status, preprocs_detail, sub_dirs_int, sub_dirs, file_time)
from base.utils.events_new import update_events_new
from base.utils.make_gif import make_gif
from base.utils.read_prescan import read_prescan
from base.utils.tree import json_to_ztree, odb_json_to_ztree

flow_bp = Blueprint('flow', __name__)


@flow_bp.route('/flows_status/')
@login_required
def flows_status():
    data = flows_detail(current_app.config['FLOW_PATH'])
    return jsonify(data)


@flow_bp.route('/manage_flows/')
@login_required
def manage_flows():
    return render_template('flow/manage_flows.html')


@flow_bp.route('/edit_flow/<int:flow_id>', methods=['GET', 'POST'])
@login_required
def edit_flow(flow_id):
    form = FlowForm()
    flows_path = current_app.config['FLOW_PATH']
    flow_path = os.path.join(flows_path, str(flow_id))
    msg_file = os.path.join(flow_path, '.flow_msg')

    if form.validate_on_submit():
        message = {
            'name': form.name.data,
            'descript': form.descript.data
        }
        dump_json(msg_file, message)
        return redirect(url_for('.manage_flows'))

    message = load_json(msg_file)
    form.name.data = message['name']
    form.descript.data = message['descript']
    return render_template('flow/edit_flow.html', form=form)


@flow_bp.route('/get_flow_file/<int:flow_id>/<path:filename>')
@login_required
def get_flow_file(flow_id, filename):
    return send_from_directory(os.path.join(current_app.config['FLOW_PATH'], str(flow_id)), filename)


@flow_bp.route('/delete_flow_file/<int:flow_id>/<path:filename>')
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


@flow_bp.route('/run_preproc/<int:flow_id>')
@login_required
def run_preproc(flow_id):
    flows_path = current_app.config['FLOW_PATH']
    flow_path = os.path.join(flows_path, str(flow_id))
    if os.path.exists(flow_path):
        p = Preproc(flow_path)
        p.read_msg()
        p.clear()
        if p.check_setting_files():
            proc = p.run()
            with open(os.path.join(flow_path, '.preproc_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
        else:
            flash(f'缺少{p.script}脚本文件。', 'warning')
        return redirect(request.referrer)
    else:
        abort(404)


@flow_bp.route('/1', methods=['GET', 'POST'])
@login_required
def f1():
    flow_id = 1
    flows_path = current_app.config['FLOW_PATH']
    flow_path = os.path.join(flows_path, str(flow_id))
    setting_file = os.path.join(flow_path, 'setting.json')

    materials_path = current_app.config['MATERIAL_PATH']
    material_dict = materials_detail(materials_path)
    material_list = []
    for material in material_dict['data']:
        material_list.append('%s_%s' % (material['material_id'], material['name']))

    upload_form = UploadForm()
    if upload_form.validate_on_submit():
        f = upload_form.filename.data
        f.save(os.path.join(flow_path, f.filename))
        flash('上传文件%s成功。' % f.filename, 'success')
        return redirect(url_for('flow.cut', flow_id=flow_id))

    form = F1From()
    form.material_tool.choices = material_list
    form.material_plane.choices = material_list

    if form.validate_on_submit():
        message = {
            'r1': form.r1.data,
            'r2': form.r2.data,
            'n': form.n.data,
            'length': form.length.data,
            'pitch': form.pitch.data,
            'tool_seed_size': form.tool_seed_size.data,
            'x_length_of_plane': form.x_length_of_plane.data,
            'y_length_of_plane': form.y_length_of_plane.data,
            'z_length_of_plane': form.z_length_of_plane.data,
            'plane_seed_size': form.plane_seed_size.data,
            'x_shift_of_tool': form.x_shift_of_tool.data,
            'y_shift_of_tool': form.y_shift_of_tool.data,
            'z_shift_of_tool': form.z_shift_of_tool.data,
            'material_tool': form.material_tool.data,
            'material_plane': form.material_plane.data,
            'timeIncrementationMethod': form.timeIncrementationMethod.data,
            'userDefinedInc': form.userDefinedInc.data,
        }
        dump_json(setting_file, message)

        material_id = int(form.material_tool.data.split('_')[0])
        material_json_path = os.path.join(materials_path, str(material_id), 'material.json')
        shutil.copy(material_json_path, os.path.join(flow_path, 'material_tool.json'))
        flash('从材料导入文件%s成功。' % 'material_tool.json', 'success')

        material_id = int(form.material_plane.data.split('_')[0])
        material_json_path = os.path.join(materials_path, str(material_id), 'material.json')
        shutil.copy(material_json_path, os.path.join(flow_path, 'material_plane.json'))
        flash('从材料导入文件%s成功。' % 'material_plane.json', 'success')

    if os.path.exists(setting_file):
        try:
            message = load_json(setting_file)
            form.r1.data = message['r1']
            form.r2.data = message['r2']
            form.n.data = message['n']
            form.length.data = message['length']
            form.pitch.data = message['pitch']
            form.tool_seed_size.data = message['tool_seed_size']
            form.x_length_of_plane.data = message['x_length_of_plane']
            form.y_length_of_plane.data = message['y_length_of_plane']
            form.z_length_of_plane.data = message['z_length_of_plane']
            form.plane_seed_size.data = message['plane_seed_size']
            form.x_shift_of_tool.data = message['x_shift_of_tool']
            form.y_shift_of_tool.data = message['y_shift_of_tool']
            form.z_shift_of_tool.data = message['z_shift_of_tool']
            form.material_tool.data = message['material_tool']
            form.material_plane.data = message['material_plane']
            form.timeIncrementationMethod.data = message['timeIncrementationMethod']
            form.userDefinedInc.data = message['userDefinedInc']
        except KeyError:
            pass

    if os.path.exists(flow_path):
        msg_file = os.path.join(flow_path, '.flow_msg')
        status = {}
        if os.path.exists(msg_file):
            status['flow_id'] = flow_id
            try:
                with open(msg_file, 'r', encoding='utf-8') as f:
                    message = json.load(f)
                status['name'] = message['name']
                status['flow_time'] = file_time(msg_file)
                status['descript'] = message['descript']
            except (FileNotFoundError, KeyError):
                for key in ['name', 'flow_time', 'descript']:
                    status[key] = 'None'

        return render_template('flow/f1.html', flow_id=flow_id, status=status, form=form, upload_form=upload_form)
    else:
        abort(404)


@flow_bp.route('/flow_status/<int:flow_id>', methods=['GET', 'POST'])
@login_required
def flow_status(flow_id):
    flows_path = current_app.config['FLOW_PATH']
    flow_path = os.path.join(flows_path, str(flow_id))
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
