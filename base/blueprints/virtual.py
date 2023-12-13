# -*- coding: utf-8 -*-
"""

"""
import os
import shutil
import uuid

from flask import (abort, Blueprint, current_app, flash, jsonify, redirect, render_template, url_for, send_from_directory, request)
from flask_login import current_user, login_required

from base.forms.virtual import (VirtualForm, ParameterForm)
from base.utils.abaqus.Postproc import Postproc
from base.utils.abaqus.Solver import Solver
from base.utils.common import make_dir, dump_json, load_json
from base.utils.dir_status import (create_id, virtuals_detail, get_virtual_status, files_in_dir)

virtual_bp = Blueprint('virtual', __name__)


@virtual_bp.route('/manage_virtuals', methods=['GET', 'POST'])
@login_required
def manage_virtuals():
    return render_template('virtual/manage_virtuals.html')


@virtual_bp.route('/create_virtual', methods=['GET', 'POST'])
@login_required
def create_virtual():
    form = VirtualForm()

    if form.validate_on_submit():
        virtuals_path = current_app.config['VIRTUAL_PATH']
        virtual_id = create_id(virtuals_path)
        virtual_path = os.path.join(virtuals_path, str(virtual_id))
        make_dir(virtual_path)
        uuid_file = os.path.join(virtual_path, '.uuid')
        with open(uuid_file, 'w', encoding='utf-8') as f:
            f.write(str(uuid.uuid4()))
        message = {
            'name': form.name.data,
            'template': form.template.data,
            'descript': form.descript.data,
            'job': form.job.data,
            'user': form.user.data,
            'cpus': form.cpus.data
        }
        msg_file = os.path.join(virtual_path, '.virtual_msg')
        dump_json(msg_file, message)
        flash('项目创建成功。', 'success')

        template_id = int(form.template.data.split('_')[0])
        templates_path = current_app.config['ABAQUS_TEMPLATE_PATH']
        template_path = os.path.join(templates_path, str(template_id))
        files = files_in_dir(template_path)
        for file in files:
            shutil.copy(os.path.join(template_path, file['name']),
                        os.path.join(virtual_path, file['name']))
            flash('从模板导入文件%s成功。' % file['name'], 'success')

        return redirect(url_for('.view_virtual', virtual_id=virtual_id))

    return render_template('virtual/create_virtual.html', form=form)


@virtual_bp.route('/edit_virtual/<int:virtual_id>', methods=['GET', 'POST'])
@login_required
def edit_virtual(virtual_id):
    form = VirtualForm()
    virtuals_path = current_app.config['VIRTUAL_PATH']
    virtual_path = os.path.join(virtuals_path, str(virtual_id))
    msg_file = os.path.join(virtual_path, '.virtual_msg')

    if form.validate_on_submit():
        message = {
            'name': form.name.data,
            'template': form.template.data,
            'descript': form.descript.data,
            'job': form.job.data,
            'user': form.user.data,
            'cpus': form.cpus.data
        }
        dump_json(msg_file, message)
        return redirect(url_for('.view_virtual', project_id=virtual_id))

    message = load_json(msg_file)
    form.name.data = message['name']
    form.template.data = message['template']
    form.descript.data = message['descript']
    form.job.data = message['job']
    form.user.data = message['user']
    form.cpus.data = message['cpus']
    return render_template('virtual/create_virtual.html', form=form)


@virtual_bp.route('/view_virtual/<int:virtual_id>', methods=['GET', 'POST'])
@login_required
def view_virtual(virtual_id):
    virtuals_path = current_app.config['VIRTUAL_PATH']
    virtual_path = os.path.join(virtuals_path, str(virtual_id))
    msg_file = os.path.join(virtual_path, '.virtual_msg')

    if os.path.exists(virtual_path):
        s = Solver(virtual_path)
        s.read_msg()
        sta = s.get_sta()
        logs = s.get_log()
        run_logs = s.get_run_log()
        para = s.get_parameters()

        form = ParameterForm()
        if form.validate_on_submit():
            para = form.para.data
            s.save_parameters(para)
            flash('parameters.inp保存成功。', 'success')
            return redirect(url_for('.view_virtual', project_id=virtual_id))
        form.para.data = para

        s.parameters_to_json()
        files = files_in_dir(virtual_path)
        solver_status = s.solver_status()

        status = get_virtual_status(virtuals_path, virtual_id)
        files = files_in_dir(virtual_path)
        return render_template('virtual/view_virtual.html', virtual_id=virtual_id, form=form, status=status, files=files, solver_status=solver_status)
    else:
        abort(404)


@virtual_bp.route('/delete_virtual/<int:virtual_id>')
@login_required
def delete_virtual(virtual_id):
    virtuals_path = current_app.config['VIRTUAL_PATH']
    virtual_path = os.path.join(virtuals_path, str(virtual_id))
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该项目！', 'warning')
        return redirect(url_for('.manage_virtuals'))
    if os.path.exists(virtual_path):
        shutil.rmtree(virtual_path)
        flash('ABAQUS项目%s删除成功。' % virtual_id, 'success')
    else:
        flash('ABAQUS项目%s不存在。' % virtual_id, 'warning')
    return redirect(url_for('.manage_virtuals'))


@virtual_bp.route('/virtuals_status')
@login_required
def virtuals_status():
    data = virtuals_detail(current_app.config['VIRTUAL_PATH'])
    return jsonify(data)


@virtual_bp.route('/get_virtual_file/<int:virtual_id>/<path:filename>')
@login_required
def get_virtual_file(virtual_id, filename):
    return send_from_directory(os.path.join(current_app.config['VIRTUAL_PATH'], str(virtual_id)), filename)


@virtual_bp.route('/run_virtual/<int:virtual_id>')
@login_required
def run_virtual(virtual_id):
    virtuals_path = current_app.config['VIRTUAL_PATH']
    virtual_path = os.path.join(virtuals_path, str(virtual_id))
    if os.path.exists(virtual_path):
        s = Solver(virtual_path)
        s.read_msg()
        s.clear()
        if s.check_files():
            proc = s.run()
            with open(os.path.join(virtual_path, '.solver_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
        else:
            flash('缺少必要的计算文件。', 'warning')
        return redirect(request.referrer or url_for('.view_virtual', virtual_id=virtual_id))
    else:
        abort(404)


@virtual_bp.route('/terminate_virtual/<int:virtual_id>')
@login_required
def terminate_virtual(virtual_id):
    virtuals_path = current_app.config['VIRTUAL_PATH']
    virtual_path = os.path.join(virtuals_path, str(virtual_id))
    if os.path.exists(virtual_path):
        s = Solver(virtual_path)
        s.read_msg()
        proc = s.terminate()
        with open(os.path.join(virtual_path, '.solver_status'), 'w', encoding='utf-8') as f:
            f.write('Stopping')
        return redirect(request.referrer or url_for('.view_virtual', virtual_id=virtual_id))
    else:
        abort(404)


@virtual_bp.route('/prescan_odb/<int:virtual_id>')
@login_required
def prescan_odb(virtual_id):
    virtuals_path = current_app.config['VIRTUAL_PATH']
    virtual_path = os.path.join(virtuals_path, str(virtual_id))
    if os.path.exists(virtual_path):
        p = Postproc(virtual_path)
        p.read_msg()
        if p.has_odb():
            proc = p.prescan_odb()
            with open(os.path.join(virtual_path, '.prescan_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
        else:
            flash('缺少odb文件。', 'warning')
        return redirect(request.referrer or url_for('.view_virtual', virtual_id=virtual_id))
    else:
        abort(404)


@virtual_bp.route('/odb_to_npz/<int:virtual_id>')
@login_required
def odb_to_npz(virtual_id):
    virtuals_path = current_app.config['VIRTUAL_PATH']
    virtual_path = os.path.join(virtuals_path, str(virtual_id))
    if os.path.exists(virtual_path):
        p = Postproc(virtual_path)
        p.read_msg()
        if p.has_odb() and p.check_setting_files():
            proc = p.odb_to_npz()
            with open(os.path.join(virtual_path, '.odb_to_npz_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
            with open(os.path.join(virtual_path, '.odb_to_npz_proc'), 'w', encoding='utf-8') as f:
                f.write('0.0\n')
        else:
            flash('缺少odb文件或odb_to_npz.json配置文件。', 'warning')
        return redirect(request.referrer or url_for('.view_virtual', virtual_id=virtual_id))
    else:
        abort(404)


@virtual_bp.route('/print_figure/<int:virtual_id>', methods=['GET', 'POST'])
@login_required
def print_figure(virtual_id):
    virtuals_path = current_app.config['VIRTUAL_PATH']
    virtual_path = os.path.join(virtuals_path, str(virtual_id))
    if os.path.exists(virtual_path):
        p = Postproc(virtual_path)
        p.read_msg()
        if p.has_odb():
            proc = p.print_figure()
            with open(os.path.join(virtual_path, '.print_figure_status'), 'w', encoding='utf-8') as f:
                f.write('Submitting')
            return redirect(request.referrer or url_for('.view_virtual', virtual_id=virtual_id))
        else:
            flash('缺少odb文件。', 'warning')
        status = get_virtual_status(virtuals_path, virtual_id)
        logs = p.get_print_figure_log()
        return redirect(request.referrer or url_for('.view_virtual', virtual_id=virtual_id))
    else:
        abort(404)
