# -*- coding: utf-8 -*-
"""

"""
import subprocess
import os
import shutil
import uuid

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required

from base.forms.material import MaterialForm, UploadForm, SpecimenForm, ParameterForm
from base.extensions import csrf
from base.utils.dir_status import create_id, materials_detail, get_material_status, files_in_dir
from base.utils.common import make_dir, dump_json, load_json

material_bp = Blueprint('material', __name__)


@material_bp.route('/materials_status/')
@login_required
def materials_status():
    data = materials_detail(current_app.config['MATERIAL_PATH'])
    return jsonify(data)


@material_bp.route('/manage_materials/')
@login_required
def manage_materials():
    return render_template('material/manage_materials.html')


@material_bp.route('/create_material', methods=['GET', 'POST'])
@login_required
def create_material():
    form = MaterialForm()

    if form.validate_on_submit():
        materials_path = current_app.config['MATERIAL_PATH']
        material_id = create_id(materials_path)
        material_path = os.path.join(materials_path, str(material_id))
        make_dir(material_path)
        uuid_file = os.path.join(material_path, '.uuid')
        with open(uuid_file, 'w', encoding='utf-8') as f:
            f.write(str(uuid.uuid4()))
        message = {
            'name': form.name.data,
            'type': form.type.data,
            'descript': form.descript.data
        }
        msg_file = os.path.join(material_path, '.material_msg')
        dump_json(msg_file, message)
        material_file = os.path.join(material_path, 'material.json')
        dump_json(material_file, {})
        flash('项目创建成功。', 'success')
        return redirect(url_for('.view_material', material_id=material_id))

    return render_template('material/create_material.html', form=form)


@material_bp.route('/edit_material/<int:material_id>', methods=['GET', 'POST'])
@login_required
def edit_material(material_id):
    form = MaterialForm()
    materials_path = current_app.config['MATERIAL_PATH']
    material_path = os.path.join(materials_path, str(material_id))
    msg_file = os.path.join(material_path, '.material_msg')

    if form.validate_on_submit():
        message = {
            'name': form.name.data,
            'type': form.type.data,
            'descript': form.descript.data
        }
        dump_json(msg_file, message)
        return redirect(url_for('.view_material', material_id=material_id))

    message = load_json(msg_file)
    form.name.data = message['name']
    form.type.data = message['type']
    form.descript.data = message['descript']
    return render_template('material/create_material.html', form=form)


@material_bp.route('/delete_material/<int:material_id>')
@login_required
def delete_material(material_id):
    materials_path = current_app.config['MATERIAL_PATH']
    material_path = os.path.join(materials_path, str(material_id))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'warning')
        return redirect(url_for('.manage_materials'))
    if os.path.exists(material_path):
        shutil.rmtree(material_path)
        flash('实验项目%s删除成功。' % material_id, 'success')
    else:
        flash('实验项目%s不存在。' % material_id, 'warning')
    return redirect(url_for('.manage_materials'))


@material_bp.route('/view_material/<int:material_id>', methods=['GET', 'POST'])
@login_required
def view_material(material_id):
    materials_path = current_app.config['MATERIAL_PATH']
    material_path = os.path.join(materials_path, str(material_id))

    form_upload = UploadForm()
    if form_upload.validate_on_submit():
        f = form_upload.filename.data
        f.save(os.path.join(material_path, f.filename))
        flash('上传文件%s成功。' % f.filename, 'success')
        return redirect(url_for('material.view_material', material_id=material_id))

    if os.path.exists(material_path):
        status = get_material_status(materials_path, material_id)
        files = files_in_dir(material_path)
        return render_template('material/view_material.html', material_id=material_id, status=status, files=files, form_upload=form_upload)
    else:
        abort(404)


@material_bp.route('/open_material/<int:material_id>')
@login_required
def open_material(material_id):
    materials_path = current_app.config['MATERIAL_PATH']
    material_path = os.path.join(materials_path, str(material_id))
    if os.path.exists(material_path):
        cmd = 'explorer %s' % material_path
        proc = subprocess.run(cmd)
        return redirect(url_for('.view_material', material_id=material_id))
    else:
        abort(404)


@material_bp.route('/get_material_file/<int:material_id>/<path:filename>')
@login_required
def get_material_file(material_id, filename):
    return send_from_directory(os.path.join(current_app.config['MATERIAL_PATH'], str(material_id)), filename)


@material_bp.route('/delete_material_file/<int:material_id>/<path:filename>')
@login_required
def delete_material_file(material_id, filename):
    materials_path = current_app.config['MATERIAL_PATH']
    file = os.path.join(materials_path, str(material_id), str(filename))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该文件！', 'warning')
        return redirect(url_for('.view_material', material_id=material_id))
    if os.path.exists(file):
        os.remove(file)
        flash('文件%s删除成功。' % filename, 'success')
    else:
        flash('文件%s不存在。' % filename, 'warning')
    return redirect(url_for('.view_material', material_id=material_id))

@csrf.exempt
@material_bp.route('/code_save/<int:material_id>', methods=['POST'])
def code_save(material_id):
    materials_path = current_app.config['MATERIAL_PATH']
    filepath = os.path.join(materials_path, str(material_id), 'material.json')

    data = request.get_json()
    content = data.get('content')

    if content:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        return jsonify({'message': 'File saved successfully'})
    else:
        return jsonify({'error': 'Content not provided'}), 400

