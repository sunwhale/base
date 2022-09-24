# -*- coding: utf-8 -*-
"""

"""
import os
import shutil
import numpy as np
import threading
import time
import json

from flask import render_template, flash, redirect, url_for, current_app, jsonify, request, Blueprint, send_from_directory
from flask_login import login_required, current_user

from psic.packing_spheres_in_cube import create_model
from psic.create_submodel import create_submodel
from psic.create_mesh import create_mesh

from base.forms.propellant import PackingForm, SubmodelForm, MeshForm, UploadForm
from base.global_var import exporting_threads, create_thread_id

from tools.dir_status import create_id, sub_dirs_int, get_model_status, get_submodel_status, get_mesh_status, packing_models_detail, packing_submodels_detail, formatSize


propellant_bp = Blueprint('propellant', __name__)


@propellant_bp.route('/create_packing_model/', methods=['GET', 'POST'])
@login_required
def create_packing_model():
    form = PackingForm()
    if form.validate_on_submit():
        ncircle = int(form.ncircle.data)
        size = eval(form.size.data)
        gap = float(form.gap.data)
        num_add = int(form.num_add.data)
        max_iter = int(form.max_iter.data)
        dt0 = float(form.dt0.data)
        dt_interval = int(form.dt_interval.data)
        rayleigh_para = float(form.rayleigh_para.data)
        num_ball = int(form.num_ball.data)
        rad_min = float(form.rad_min.data)
        rad_max = float(form.rad_max.data)

        model_id = create_id(current_app.config['PROPELLANT_PACKING_MODEL_PATH'])
        model_path = os.path.join(current_app.config['PROPELLANT_PACKING_MODEL_PATH'], str(model_id))

        if not os.path.isdir(model_path):
            os.makedirs(model_path)

        thread_id = create_thread_id()
        exporting_threads[thread_id] = {}
        status = exporting_threads[thread_id]
        status['class'] = '球体填充'
        status['class_id'] = model_id
        status['progress'] = 0
        status['status'] = 'Submit'
        status['log'] = ''

        args = (ncircle, size, gap, num_add, max_iter, dt0, dt_interval,
                rayleigh_para, num_ball, rad_min, rad_max, model_path, status)

        thread = threading.Thread(target=create_model, args=args)
        thread.start()

        return render_template('propellant/create_packing_model.html', form=form)
    return render_template('propellant/create_packing_model.html', form=form)


@propellant_bp.route('/create_packing_submodel/<int:model_id>', methods=['GET', 'POST'])
@login_required
def create_packing_submodel(model_id):
    model_path = os.path.join(
        current_app.config['PROPELLANT_PACKING_MODEL_PATH'], str(model_id))
    model_msg_file = os.path.join(model_path, 'model.msg')
    model_npy_file = os.path.join(model_path, 'model.npy')
    form = SubmodelForm()
    if os.path.exists(model_npy_file):
        if form.validate_on_submit():
            gap = float(form.gap.data)
            ndiv = int(form.ndiv.data)
            with open(model_msg_file, 'r', encoding='utf-8') as f:
                message = json.load(f)
            size = message['size']
            out_path = os.path.join(
                current_app.config['PROPELLANT_PACKING_SUBMODEL_PATH'], str(model_id))

            if os.path.exists(out_path):
                shutil.rmtree(out_path)

            thread_id = create_thread_id()
            exporting_threads[thread_id] = {}
            status = exporting_threads[thread_id]
            status['class'] = '生成子模型'
            status['class_id'] = model_id
            status['progress'] = 0
            status['status'] = 'Submit'
            status['log'] = ''

            args = (model_npy_file, model_id, size,
                    ndiv, gap, out_path, status)

            thread = threading.Thread(target=create_submodel, args=args)
            thread.start()
        return render_template('propellant/create_packing_submodel.html', form=form, model_id=model_id)
    else:
        flash('主模型%s不存在。' % model_id, 'danger')
        return render_template('propellant/create_packing_submodel.html', form=form, model_id=model_id)


@propellant_bp.route('/create_packing_mesh/<int:model_id>', methods=['GET', 'POST'])
@login_required
def create_packing_mesh(model_id):
    form = MeshForm()
    model_path = os.path.join(current_app.config['PROPELLANT_PACKING_SUBMODEL_PATH'], str(model_id))
    mesh_path = os.path.join(current_app.config['PROPELLANT_PACKING_MESH_PATH'], str(model_id))
    if os.path.isdir(model_path):
        if form.validate_on_submit():
            gap = float(form.gap.data)
            node_shape = eval(form.node_shape.data)
            element_type = form.element_type.data

            if os.path.exists(mesh_path):
                shutil.rmtree(mesh_path)

            if not os.path.isdir(mesh_path):
                os.makedirs(mesh_path)

            thread_id = create_thread_id()
            exporting_threads[thread_id] = {}
            status = exporting_threads[thread_id]
            status['class'] = '划分网格'
            status['class_id'] = model_id
            status['progress'] = 0
            status['status'] = 'Submit'
            status['log'] = ''

            def create_meshes(gap, node_shape, element_type, model_path, mesh_path, status):
                submodel_ids = sub_dirs_int(model_path)
                status['status'] = 'Running'
                for submodel_id in submodel_ids:
                    submesh_path = os.path.join(mesh_path, str(submodel_id))
                    submodel_path = os.path.join(model_path, str(submodel_id))
                    msg_file = os.path.join(model_path, str(submodel_id), 'model.msg')

                    with open(msg_file, 'r', encoding='utf-8') as f:
                        message = json.load(f)
                    size = message['subsize']
                    if len(size) > 3:
                        size = size[:3]
                    dimension = [s[1] for s in size]
                    
                    if not os.path.isdir(submesh_path):
                        os.makedirs(submesh_path)

                    status['progress'] = 100*submodel_id/len(submodel_ids)
                    substatus = {'status': 'Submit', 'log': '', 'progress': 0}

                    args = (gap, size, dimension, node_shape, element_type, submodel_path, submesh_path, substatus)
                    create_mesh(*args)

                status['progress'] = 100
                status['status'] = 'Done'

            args = (gap, node_shape, element_type, model_path, mesh_path, status)
            thread = threading.Thread(target=create_meshes, args=args)
            thread.start()
        return render_template('propellant/create_packing_mesh.html', form=form, model_id=model_id)
    else:
        flash('主模型%s不存在，或尚未生成子模型。' % model_id, 'danger')
        return render_template('propellant/create_packing_mesh.html', form=form, model_id=model_id)


@propellant_bp.route('/manage_packing_models/')
@login_required
def manage_packing_models():
    return render_template('propellant/manage_packing_models.html')


@propellant_bp.route('/manage_packing_submodels/<int:model_id>')
@login_required
def manage_packing_submodels(model_id):
    return render_template('propellant/manage_packing_submodels.html', model_id=model_id)


@propellant_bp.route('/packing_models_status/')
@login_required
def packing_models_status():
    data = packing_models_detail(
        current_app.config['PROPELLANT_PACKING_MODEL_PATH'])
    return jsonify(data)


@propellant_bp.route('/packing_submodels_status/<int:model_id>')
@login_required
def packing_submodels_status(model_id):
    data = packing_submodels_detail(
        current_app.config['PROPELLANT_PACKING_SUBMODEL_PATH'], model_id)
    return jsonify(data)


@propellant_bp.route('/get_packing_model/<path:filename>')
@login_required
def get_packing_model(filename):
    return send_from_directory(current_app.config['PROPELLANT_PACKING_MODEL_PATH'], filename)


@propellant_bp.route('/get_packing_submodel/<path:filename>')
@login_required
def get_packing_submodel(filename):
    return send_from_directory(current_app.config['PROPELLANT_PACKING_SUBMODEL_PATH'], filename)


@propellant_bp.route('/get_packing_mesh/<path:filename>')
@login_required
def get_packing_mesh(filename):
    return send_from_directory(current_app.config['PROPELLANT_PACKING_MESH_PATH'], filename)


@propellant_bp.route('/view_packing_model/<int:model_id>')
@login_required
def view_packing_model(model_id):
    path = os.path.join(current_app.config['PROPELLANT_PACKING_MODEL_PATH'])
    status = get_model_status(path, model_id)
    return render_template('propellant/view_packing_model.html', model_id=model_id, status=status)


@propellant_bp.route('/view_packing_submodel/<int:model_id>/<int:submodel_id>')
@login_required
def view_packing_submodel(model_id, submodel_id):
    path = os.path.join(current_app.config['PROPELLANT_PACKING_SUBMODEL_PATH'])
    status = get_submodel_status(path, model_id, submodel_id)
    path = os.path.join(current_app.config['PROPELLANT_PACKING_MESH_PATH'])
    status_mesh = get_mesh_status(path, model_id, submodel_id)
    return render_template('propellant/view_packing_submodel.html', model_id=model_id, submodel_id=submodel_id, status=status, status_mesh=status_mesh)


@propellant_bp.route('/delete_packing_models/<int:model_id>')
@login_required
def delete_packing_models(model_id):
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该模型！', 'danger')
        return redirect(url_for('.manage_packing_models'))
    model_path = os.path.join(current_app.config['PROPELLANT_PACKING_MODEL_PATH'], str(model_id))
    if os.path.exists(model_path):
        shutil.rmtree(model_path)
        flash('模型%s删除成功。' % model_id, 'info')
    else:
        flash('模型%s不存在。' % model_id, 'danger')
    return redirect(url_for('.manage_packing_models'))


@propellant_bp.route('/thread/<thread_id>')
@login_required
def thread_id(thread_id):
    return jsonify(exporting_threads[thread_id])


@propellant_bp.route('/thread/')
@login_required
def thread():
    return jsonify(exporting_threads)


@propellant_bp.route('/thread/clear/')
@login_required
def thread_clear():
    thread_ids = list(exporting_threads.keys())
    for thread_id in thread_ids:
        if exporting_threads[thread_id]['status'] == 'Done':
            del exporting_threads[thread_id]
    return jsonify(exporting_threads)
