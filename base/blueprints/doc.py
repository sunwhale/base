# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil
import time

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

from base.extensions import csrf
from tools.dir_status import create_id, docs_detail

doc_bp = Blueprint('doc', __name__)


@doc_bp.route('/createmd', methods=['GET', 'POST'])
@login_required
def createmd():
    doc_id = create_id(current_app.config['DOC_PATH'])
    doc_path = os.path.join(current_app.config['DOC_PATH'], str(doc_id))
    if not os.path.isdir(doc_path):
        os.makedirs(doc_path)
    with open(os.path.join(doc_path, 'article.md'), 'w', encoding='utf-8') as f:
        f.write(' ')
    return redirect(url_for('.editmd', doc_id=doc_id))


@doc_bp.route('/editmd/<int:doc_id>', methods=['GET', 'POST'])
@login_required
def editmd(doc_id):
    doc_path = os.path.join(current_app.config['DOC_PATH'], str(doc_id))
    md_file = os.path.join(doc_path, 'article.md')
    msg_file = os.path.join(doc_path, 'article.msg')
    try:
        with open(msg_file, 'r', encoding='utf-8') as f:
            message = json.load(f)
    except:
        message = {}
    if request.method == 'POST':
        data = request.form.to_dict()
        message = {}
        message['title'] = data['title']
        content = data['editormd-markdown-doc'].replace('\n', '')
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(content)
        with open(msg_file, 'w', encoding='utf-8') as f:
            json.dump(message, f, ensure_ascii=False)
        return render_template('doc/editmd.html', doc_id=doc_id, message=message)
    if os.path.exists(md_file):
        return render_template('doc/editmd.html', doc_id=doc_id, message=message)
    else:
        abort(404)


@doc_bp.route('/viewmd/<int:doc_id>')
def viewmd(doc_id):
    doc_path = os.path.join(current_app.config['DOC_PATH'], str(doc_id))
    msg_file = os.path.join(doc_path, 'article.msg')
    try:
        with open(msg_file, 'r', encoding='utf-8') as f:
            message = json.load(f)
    except:
        message = {}
    return render_template('doc/viewmd.html', doc_id=doc_id, message=message)


@doc_bp.route('/getmd/<int:doc_id>')
def getmd(doc_id):
    return send_from_directory(os.path.join(current_app.config['DOC_PATH'], str(doc_id)), 'article.md')


@csrf.exempt
@doc_bp.route('/upload/<int:doc_id>', methods=['POST'])
@login_required
def upload(doc_id):
    file = request.files.get('editormd-image-file')
    if not file:
        res = {
            'success': 0,
            'message': '????????????'
        }
    else:
        filename = os.path.join(current_app.config['DOC_PATH'], str(doc_id), file.filename)
        file.save(filename)
        res = {
            'success': 1,
            'message': '????????????',
            'url': url_for('.image', doc_id=doc_id, filename=file.filename)
        }
    return jsonify(res)


@doc_bp.route('/<int:doc_id>/image/<filename>')
def image(doc_id, filename):
    return send_from_directory(os.path.join(current_app.config['DOC_PATH'], str(doc_id)), filename)


@doc_bp.route('/docs_status/')
@login_required
def docs_status():
    data = docs_detail(current_app.config['DOC_PATH'])
    return jsonify(data)


@doc_bp.route('/manage_docs/')
@login_required
def manage_docs():
    return render_template('doc/manage_docs.html')


@doc_bp.route('/deletemd/<int:doc_id>')
@login_required
def deletemd(doc_id):
    if not current_user.can('MODERATE'):
        flash('????????????????????????????????????', 'warning')
        return redirect(url_for('.manage_docs'))
    doc_path = os.path.join(current_app.config['DOC_PATH'], str(doc_id))
    if os.path.exists(doc_path):
        shutil.rmtree(doc_path)
        flash('??????%s???????????????' % doc_id, 'success')
    else:
        flash('??????%s????????????' % doc_id, 'warning')
    return redirect(url_for('.manage_docs'))