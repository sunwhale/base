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

from base.forms.propellant import PackingForm, SubmodelForm, UploadForm
from base.global_var import exporting_threads

from tools.dir_status import create_id, packing_models_detail, formatSize


propellant_bp = Blueprint('propellant', __name__)


@propellant_bp.route('/create_packing_models/', methods=['GET', 'POST'])
def create_packing_models():
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

        num_of_threads = len(exporting_threads.keys())

        if num_of_threads == 0:
            thread_id = 1
        else:
            thread_id = max(num_of_threads, max(list(exporting_threads.keys())))+1

        exporting_threads[thread_id] = {}
        status = exporting_threads[thread_id]
        status['class'] = '球体填充'
        status['class_id'] = model_id
        status['progress'] = 0
        status['status'] = 'Submit'
        status['log'] = ''

        args = (ncircle, size, gap, num_add, max_iter, dt0, dt_interval, rayleigh_para, num_ball, rad_min, rad_max, model_path, status)

        thread = threading.Thread(target=create_model, args=args)
        thread.start()

        return render_template('propellant/create_packing_models.html', form=form, exporting_threads=exporting_threads)
    return render_template('propellant/create_packing_models.html', form=form, exporting_threads=exporting_threads)


@propellant_bp.route('/manage_packing_models/')
def manage_packing_models():
    return render_template('propellant/manage_packing_models.html')


@propellant_bp.route('/packing_models_status/')
def packing_models_status():
    data = packing_models_detail(current_app.config['PROPELLANT_PACKING_MODEL_PATH'])
    return jsonify(data)


@propellant_bp.route('/get_packing_models/<path:filename>')
def get_packing_models(filename):
    return send_from_directory(current_app.config['PROPELLANT_PACKING_MODEL_PATH'], filename)


@propellant_bp.route('/view_packing_models/<int:model_id>')
def view_packing_models(model_id):
    path = current_app.config['PROPELLANT_PACKING_MODEL_PATH']
    npy_file = os.path.join(path, str(model_id)+'\\'+'model.npy')
    args_file = os.path.join(path, str(model_id)+'\\'+'args.json')
    log_file = os.path.join(path, str(model_id)+'\\'+'model.log')
    msg_file = os.path.join(path, str(model_id)+'\\'+'model.msg')
    status = {}
    npy_modified_time = os.path.getmtime(npy_file)
    with open(args_file, 'r', encoding='utf-8') as f:
        args = json.load(f)
    with open(msg_file, 'r', encoding='utf-8') as f:
        message = json.load(f)
    with open(log_file, 'r', encoding='utf-8') as f:
        status['log'] = f.read()
    status['args'] = str(args[:-1])
    status['size'] = message['size']
    status['num_ball'] = message['num_ball']
    status['gap'] = message['gap']
    status['fraction'] = '%.4f' % message['fraction']
    status['npy_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(npy_modified_time))
    status['npy_size'] = formatSize(os.path.getsize(npy_file))
    return render_template('propellant/view_packing_models.html', model_id=model_id, status=status)


@propellant_bp.route('/delete_packing_models/<int:model_id>')
def delete_packing_models(model_id):
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该模型！', 'danger')
        return redirect(url_for('.manage_packing_models'))
    model_path = os.path.join(current_app.config['PROPELLANT_PACKING_MODEL_PATH'], str(model_id))
    if os.path.exists(model_path):
        shutil.rmtree(model_path)
        flash('模型%s删除成功。' % model_id, 'info')
    else:
        flash('模型%s不存在。' % model_id, 'info')
    return redirect(url_for('.manage_packing_models'))


@propellant_bp.route('/create_packing_submodels/', methods=['GET', 'POST'])
def create_packing_submodels():
    form = SubmodelForm()
    if form.validate_on_submit():
        model_id = int(form.model_id.data)
        gap = float(form.gap.data)
        ndiv = int(form.ndiv.data)
        model_path = os.path.join(current_app.config['PROPELLANT_PACKING_MODEL_PATH'], str(model_id))
        model_msg_file = os.path.join(model_path, 'model.msg')
        model_npy_file = os.path.join(model_path, 'model.npy')
        with open(model_msg_file, 'r', encoding='utf-8') as f:
            message = json.load(f)
        size = message['size']
        out_path = os.path.join(current_app.config['PROPELLANT_PACKING_SUBMODEL_PATH'], str(model_id))
        
        num_of_threads = len(exporting_threads.keys())

        if num_of_threads == 0:
            thread_id = 1
        else:
            thread_id = max(num_of_threads, max(list(exporting_threads.keys())))+1

        exporting_threads[thread_id] = {}
        status = exporting_threads[thread_id]
        status['class'] = '生成子模型'
        status['class_id'] = model_id
        status['progress'] = 0
        status['status'] = 'Submit'
        status['log'] = ''

        args = (model_npy_file, model_id, size, ndiv, gap, out_path, status)

        thread = threading.Thread(target=create_submodel, args=args)
        thread.start()

    return render_template('propellant/create_packing_submodels.html', form=form)


@propellant_bp.route('/view_packing_submodels/<int:model_id>/<int:submodel_id>')
def view_packing_submodels(model_id, submodel_id):
    submodel_path = os.path.join(current_app.config['PROPELLANT_PACKING_SUBMODEL_PATH'], str(model_id))

    npy_file = os.path.join(submodel_path, str(submodel_id)+'\\'+'model.npy')
    args_file = os.path.join(submodel_path, str(submodel_id)+'\\'+'args.json')
    msg_file = os.path.join(submodel_path, str(submodel_id)+'\\'+'model.msg')
    status = {}
    npy_modified_time = os.path.getmtime(npy_file)
    with open(args_file, 'r', encoding='utf-8') as f:
        args = json.load(f)
    with open(msg_file, 'r', encoding='utf-8') as f:
        message = json.load(f)
    status['args'] = str(args[1:-1])
    status['size'] = message['size']
    status['num_ball'] = message['num_ball']
    status['gap'] = message['gap']
    status['fraction'] = '%.4f' % message['fraction']
    status['npy_time'] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(npy_modified_time))
    status['npy_size'] = formatSize(os.path.getsize(npy_file))
    return render_template('propellant/view_packing_submodels.html', model_id=model_id, submodel_id=submodel_id, status=status)


@propellant_bp.route('/upload/', methods=['GET', 'POST'])
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        f = form.filename.file
        print(type(f))
        # f.save(os.path.join(current_app.config['UPLOAD_PATH']))
    return render_template('propellant/upload.html', form=form)


@propellant_bp.route('/get_packing_submodels/<path:filename>')
def get_packing_submodels(filename):
    return send_from_directory(current_app.config['PROPELLANT_PACKING_SUBMODEL_PATH'], filename)


@propellant_bp.route('/thread/<thread_id>')
def thread_id(thread_id):
    return jsonify(exporting_threads[thread_id])


@propellant_bp.route('/thread/')
def thread():
    return jsonify(exporting_threads)


@propellant_bp.route('/thread/clear/')
def thread_clear():
    thread_ids = list(exporting_threads.keys())
    for thread_id in thread_ids:
        if exporting_threads[thread_id]['status'] == 'Done':
            del exporting_threads[thread_id]
    return jsonify(exporting_threads)
