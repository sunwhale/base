# -*- coding: utf-8 -*-
"""

"""
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
from base.extensions import csrf

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('/links', methods=['GET'])
@login_required
def links():
    return render_template('tools/links.html')


@tools_bp.route('/code', methods=['GET'])
@login_required
def code():
    return render_template('tools/code.html')


@csrf.exempt
@tools_bp.route('/code_save', methods=['POST'])
def code_save():
    data = request.get_json()
    content = data.get('content')

    if content:
        with open('saved_file.txt', 'w') as file:
            file.write(content)
        return jsonify({'message': 'File saved successfully'})
    else:
        return jsonify({'error': 'Content not provided'}), 400
