# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil
import threading
import time

import numpy as np
from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required
from psic.create_mesh import create_mesh as psic_create_mesh
from psic.create_submodel import create_submodel as psic_create_submodel
from psic.packing_spheres_in_cube import create_model as psic_create_model

from base.forms.packing import (MeshForm, PackingForm, PostForm,
                                   SubmodelForm, UploadForm)
from base.global_var import create_thread_id, exporting_threads
from tools.dir_status import (create_id, format_size, get_mesh_status,
                              get_model_status, get_submodel_status,
                              packing_models_detail, packing_submodels_detail,
                              sub_dirs_int)

packing_bp = Blueprint('packing', __name__)


@packing_bp.route('/create_model/', methods=['GET', 'POST'])
@login_required
def create_model():
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

        model_id = create_id(current_app.config['PACKING_MODEL_PATH'])
        model_path = os.path.join(current_app.config['PACKING_MODEL_PATH'], str(model_id))

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

        thread = threading.Thread(target=psic_create_model, args=args)
        thread.start()

        return render_template('packing/create_model.html', form=form)
    return render_template('packing/create_model.html', form=form)


@packing_bp.route('/create_submodel/<int:model_id>', methods=['GET', 'POST'])
@login_required
def create_submodel(model_id):
    model_path = os.path.join(current_app.config['PACKING_MODEL_PATH'], str(model_id))
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
            submodel_path = os.path.join(model_path, 'submodels')

            if os.path.exists(submodel_path):
                shutil.rmtree(submodel_path)

            thread_id = create_thread_id()
            exporting_threads[thread_id] = {}
            status = exporting_threads[thread_id]
            status['class'] = '生成子模型'
            status['class_id'] = model_id
            status['progress'] = 0
            status['status'] = 'Submit'
            status['log'] = ''

            args = (model_npy_file, model_id, size,
                    ndiv, gap, submodel_path, status)

            thread = threading.Thread(target=psic_create_submodel, args=args)
            thread.start()
        return render_template('packing/create_submodel.html', form=form, model_id=model_id)
    else:
        flash('主模型%s不存在。' % model_id, 'warning')
        return render_template('packing/create_submodel.html', form=form, model_id=model_id)


@packing_bp.route('/create_mesh/<int:model_id>', methods=['GET', 'POST'])
@login_required
def create_mesh(model_id):
    form = MeshForm()
    model_path = os.path.join(current_app.config['PACKING_MODEL_PATH'], str(model_id))
    submodels_path = os.path.join(model_path, 'submodels')
    meshes_path = os.path.join(model_path, 'meshes')
    if os.path.isdir(model_path):
        if form.validate_on_submit():
            gap = float(form.gap.data)
            node_shape = eval(form.node_shape.data)
            element_type = form.element_type.data

            if os.path.exists(meshes_path):
                shutil.rmtree(meshes_path)

            if not os.path.isdir(meshes_path):
                os.makedirs(meshes_path)

            thread_id = create_thread_id()
            exporting_threads[thread_id] = {}
            status = exporting_threads[thread_id]
            status['class'] = '划分网格'
            status['class_id'] = model_id
            status['progress'] = 0
            status['status'] = 'Submit'
            status['log'] = ''

            def create_meshes(gap, node_shape, element_type, submodels_path, meshes_path, status):
                submodel_ids = sub_dirs_int(submodels_path)
                status['status'] = 'Running'
                for submodel_id in submodel_ids:
                    mesh_path = os.path.join(meshes_path, str(submodel_id))
                    submodel_path = os.path.join(submodels_path, str(submodel_id))
                    msg_file = os.path.join(submodel_path, 'model.msg')

                    with open(msg_file, 'r', encoding='utf-8') as f:
                        message = json.load(f)
                    size = message['subsize']
                    if len(size) > 3:
                        size = size[:3]
                    dimension = [s[1] for s in size]
                    
                    if not os.path.isdir(mesh_path):
                        os.makedirs(mesh_path)

                    status['progress'] = 100*submodel_id/len(submodel_ids)
                    substatus = {'status': 'Submit', 'log': '', 'progress': 0}

                    args = (gap, size, dimension, node_shape, element_type, submodel_path, mesh_path, substatus)
                    psic_create_mesh(*args)

                status['progress'] = 100
                status['status'] = 'Done'

            args = (gap, node_shape, element_type, submodels_path, meshes_path, status)
            thread = threading.Thread(target=create_meshes, args=args)
            thread.start()
        return render_template('packing/create_mesh.html', form=form, model_id=model_id)
    else:
        flash('主模型%s不存在，或尚未生成子模型。' % model_id, 'warning')
        return render_template('packing/create_mesh.html', form=form, model_id=model_id)


@packing_bp.route('/manage_models/')
@login_required
def manage_models():
    return render_template('packing/manage_models.html')


@packing_bp.route('/manage_submodels/<int:model_id>')
@login_required
def manage_submodels(model_id):
    return render_template('packing/manage_submodels.html', model_id=model_id)


@packing_bp.route('/models_status/')
@login_required
def models_status():
    data = packing_models_detail(
        current_app.config['PACKING_MODEL_PATH'])
    return jsonify(data)


@packing_bp.route('/submodels_status/<int:model_id>')
@login_required
def submodels_status(model_id):
    submodel_path = os.path.join(current_app.config['PACKING_MODEL_PATH'], str(model_id), 'submodels')
    data = packing_submodels_detail(submodel_path, model_id)
    return jsonify(data)


@packing_bp.route('/get_model/<int:model_id>/<path:filename>')
@login_required
def get_model(model_id, filename):
    model_path = os.path.join(current_app.config['PACKING_MODEL_PATH'], str(model_id))
    return send_from_directory(model_path, filename)


@packing_bp.route('/get_submodel/<int:model_id>/<int:submodel_id>/<path:filename>')
@login_required
def get_submodel(model_id, submodel_id, filename):
    submodel_path = os.path.join(current_app.config['PACKING_MODEL_PATH'], str(model_id), 'submodels', str(submodel_id))
    return send_from_directory(submodel_path, filename)


@packing_bp.route('/get_mesh/<int:model_id>/<int:submodel_id>/<path:filename>')
@login_required
def get_mesh(model_id, submodel_id, filename):
    mesh_path = os.path.join(current_app.config['PACKING_MODEL_PATH'], str(model_id), 'meshes', str(submodel_id))
    return send_from_directory(mesh_path, filename)


@packing_bp.route('/view_model/<int:model_id>')
@login_required
def view_model(model_id):
    path = os.path.join(current_app.config['PACKING_MODEL_PATH'])
    if os.path.exists(os.path.join(path, str(model_id))):
        status = get_model_status(path, model_id)
        return render_template('packing/view_model.html', model_id=model_id, status=status)
    else:
        abort(404)


@packing_bp.route('/view_submodel/<int:model_id>/<int:submodel_id>')
@login_required
def view_submodel(model_id, submodel_id):
    model_path = os.path.join(current_app.config['PACKING_MODEL_PATH'], str(model_id))
    submodels_path = os.path.join(model_path, 'submodels')
    meshes_path = os.path.join(model_path, 'meshes')
    if os.path.exists(os.path.join(submodels_path, str(submodel_id))):
        status = get_submodel_status(submodels_path, model_id, submodel_id)
        status_mesh = get_mesh_status(meshes_path, model_id, submodel_id)
        return render_template('packing/view_submodel.html', model_id=model_id, submodel_id=submodel_id, status=status, status_mesh=status_mesh)
    else:
        abort(404)


@packing_bp.route('/delete_models/<int:model_id>')
@login_required
def delete_models(model_id):
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该模型！', 'danger')
        return redirect(url_for('.manage_models'))
    model_path = os.path.join(current_app.config['PACKING_MODEL_PATH'], str(model_id))
    if os.path.exists(model_path):
        shutil.rmtree(model_path)
        flash('模型%s删除成功。' % model_id, 'success')
    else:
        flash('模型%s不存在。' % model_id, 'warning')
    return redirect(url_for('.manage_models'))


@packing_bp.route('/thread/<thread_id>')
@login_required
def thread_id(thread_id):
    return jsonify(exporting_threads[thread_id])


@packing_bp.route('/thread/')
@login_required
def thread():
    return jsonify(exporting_threads)


@packing_bp.route('/thread/clear/')
@login_required
def thread_clear():
    thread_ids = list(exporting_threads.keys())
    for thread_id in thread_ids:
        if exporting_threads[thread_id]['status'] == 'Done':
            del exporting_threads[thread_id]
    return jsonify(exporting_threads)


@packing_bp.route('/status')
@login_required
def status():
    return str(threading.active_count()) +  str([t.current_thread() for t in threading.enumerate()])