# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request, url_for)
from flask_login import current_user, login_required

from base.extensions import csrf
from base.utils.dir_status import create_id, sheets_detail

sheet_bp = Blueprint('sheet', __name__)


@sheet_bp.route('/create_sheet', methods=['GET', 'POST'])
@login_required
def create_sheet():
    sheet_id = create_id(current_app.config['SHEET_PATH'])
    sheet_path = os.path.join(current_app.config['SHEET_PATH'], str(sheet_id))
    return render_template('sheet/create_sheet.html', sheet_id=sheet_id)


@sheet_bp.route('/edit_sheet/<int:sheet_id>', methods=['GET', 'POST'])
@login_required
def edit_sheet(sheet_id):
    sheet_path = os.path.join(current_app.config['SHEET_PATH'], str(sheet_id))
    sheet_file = os.path.join(sheet_path, 'sheet.json')
    msg_file = os.path.join(sheet_path, 'sheet.msg')
    with open(msg_file, 'r', encoding='utf-8') as f:
        message = json.load(f)
    if os.path.exists(sheet_file):
        return render_template('sheet/edit_sheet.html', sheet_id=sheet_id, message=message)
    else:
        abort(404)


@sheet_bp.route('/view_sheet/<int:sheet_id>', methods=['GET'])
@login_required
def view_sheet(sheet_id):
    sheet_path = os.path.join(current_app.config['SHEET_PATH'], str(sheet_id))
    sheet_file = os.path.join(sheet_path, 'sheet.json')
    msg_file = os.path.join(sheet_path, 'sheet.msg')
    with open(msg_file, 'r', encoding='utf-8') as f:
        message = json.load(f)
    if os.path.exists(sheet_file):
        return render_template('sheet/view_sheet.html', sheet_id=sheet_id, message=message)
    else:
        abort(404)


@sheet_bp.route('/upload/<int:sheet_id>', methods=['POST'])
@csrf.exempt
def upload(sheet_id):
    exceldata = request.form['exceldata']
    message = {}
    message['title'] = request.form['title']
    if not exceldata:
        res = {
            'success': 0,
            'message': '保存失败'
        }
    else:
        sheet_path = os.path.join(
            current_app.config['SHEET_PATH'], str(sheet_id))
        if not os.path.isdir(sheet_path):
            os.makedirs(sheet_path)
        try:
            sheet_file = os.path.join(sheet_path, 'sheet.json')
            with open(sheet_file, 'w', encoding='utf-8') as f:
                json.dump(exceldata, f, ensure_ascii=False)
            msg_file = os.path.join(sheet_path, 'sheet.msg')
            with open(msg_file, 'w', encoding='utf-8') as f:
                json.dump(message, f, ensure_ascii=False)
            res = {
                'success': 1,
                'message': '保存成功'
            }
        except:
            res = {
                'success': 0,
                'message': '保存失败'
            }
    return res


@sheet_bp.route('/read/<int:sheet_id>', methods=['POST'])
@csrf.exempt
def read(sheet_id):
    sheet_path = os.path.join(current_app.config['SHEET_PATH'], str(sheet_id))
    sheet_file = os.path.join(sheet_path, 'sheet.json')
    with open(sheet_file, 'r', encoding='utf-8') as f:
        exceldata = json.load(f)
    return exceldata


@sheet_bp.route('/sheets_status/')
@login_required
def sheets_status():
    data = sheets_detail(current_app.config['SHEET_PATH'])
    return jsonify(data)


@sheet_bp.route('/manage_sheets/')
@login_required
def manage_sheets():
    return render_template('sheet/manage_sheets.html')


@sheet_bp.route('/delete_sheet/<int:sheet_id>')
@login_required
def delete_sheet(sheet_id):
    if not current_user.can('MODERATE'):
        flash('您的权限不能删除该数据表格！', 'warning')
        return redirect(url_for('.manage_sheets'))
    sheet_path = os.path.join(current_app.config['SHEET_PATH'], str(sheet_id))
    if os.path.exists(sheet_path):
        shutil.rmtree(sheet_path)
        flash('数据表格%s删除成功。' % sheet_id, 'success')
    else:
        flash('数据表格%s不存在！' % sheet_id, 'warning')
    return redirect(url_for('.manage_sheets'))
