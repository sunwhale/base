# -*- coding: utf-8 -*-
"""

"""
import os
import shutil
import time
import json

from flask import render_template, flash, redirect, url_for, current_app, jsonify, request, Blueprint, send_from_directory
from flask_login import login_required, current_user
from tools.dir_status import create_id


doc_bp = Blueprint('doc', __name__)


@doc_bp.route('/createmd', methods=['GET', 'POST'])
@login_required
def createmd():
    doc_id = create_id(current_app.config['DOC_PATH'])
    doc_path = os.path.join(current_app.config['DOC_PATH'], str(doc_id))
    if not os.path.isdir(doc_path):
        os.makedirs(doc_path)
    with open(os.path.join(doc_path, 'article.md'), 'w', encoding='utf-8') as f:
        f.write('')
    return redirect(url_for('.editmd', doc_id=doc_id))


@doc_bp.route('/editmd/<int:doc_id>', methods=['GET', 'POST'])
@login_required
def editmd(doc_id):
    doc_path = os.path.join(current_app.config['DOC_PATH'], str(doc_id))
    filename = os.path.join(doc_path, 'article.md')
    if request.method == 'POST':
        data = request.form.to_dict()
        content = data['editormd-markdown-doc'].replace('\n', '')
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        return render_template('doc/editmd.html', doc_id=doc_id)
    if os.path.isdir(doc_path):
        return render_template('doc/editmd.html', doc_id=doc_id)
    else:
        return '页面不存在！'


@doc_bp.route('/viewmd/<int:doc_id>')
@login_required
def viewmd(doc_id):
    return render_template('doc/viewmd.html', doc_id=doc_id)


@doc_bp.route('/getmd/<int:doc_id>')
@login_required
def getmd(doc_id):
    return send_from_directory(os.path.join(current_app.config['DOC_PATH'], str(doc_id)), 'article.md')


@doc_bp.route('/upload/<int:doc_id>', methods=['POST'])
@login_required
def upload(doc_id):
    file = request.files.get('editormd-image-file')
    if not file:
        res = {
            'success': 0,
            'message': '上传失败'
        }
    else:
        filename = os.path.join(current_app.config['DOC_PATH'], str(doc_id), file.filename)
        file.save(filename)
        res = {
            'success': 1,
            'message': '上传成功',
            'url': url_for('.image', doc_id=doc_id, filename=file.filename)
        }
    return jsonify(res)


@doc_bp.route('/<int:doc_id>/image/<filename>')
def image(doc_id, filename):
    return send_from_directory(os.path.join(current_app.config['DOC_PATH'], str(doc_id)), filename)
