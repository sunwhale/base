# -*- coding: utf-8 -*-
"""

"""
import os

from flask import current_app, Blueprint, render_template, request, jsonify

from base.decorators import permission_required
from base.extensions import csrf

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('/links', methods=['GET'])
@permission_required('TOOLS')
def links():
    return render_template('tools/links.html')


@tools_bp.route('/code', methods=['GET'])
@permission_required('CODE')
def code():
    return render_template('tools/code.html')


@csrf.exempt
@tools_bp.route('/code_save/<path:url>', methods=['POST'])
def code_save(url):
    if 'pyfem/get_job_file/' in url:
        info = url.split('pyfem/get_job_file/')[1].split('/')
        project_id, job_id, filename = info[0], info[1], info[2]
        filepath = os.path.join(current_app.config['PYFEM_PATH'], str(project_id), str(job_id), filename)
    elif 'pyfem/get_project_file/' in url:
        info = url.split('pyfem/get_project_file/')[1].split('/')
        project_id, filename = info[0], info[1]
        filepath = os.path.join(current_app.config['PYFEM_PATH'], str(project_id), filename)
    elif 'abaqus/get_job_file/' in url:
        info = url.split('abaqus/get_job_file/')[1].split('/')
        project_id, job_id, filename = info[0], info[1], info[2]
        filepath = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id), str(job_id), filename)
    elif 'abaqus/get_project_file/' in url:
        info = url.split('abaqus/get_project_file/')[1].split('/')
        project_id, filename = info[0], info[1]
        filepath = os.path.join(current_app.config['ABAQUS_PATH'], str(project_id), filename)
    elif 'abaqus/get_template_file/' in url:
        info = url.split('abaqus/get_template_file/')[1].split('/')
        template_id, filename = info[0], info[1]
        filepath = os.path.join(current_app.config['ABAQUS_TEMPLATE_PATH'], str(template_id), filename)
    elif 'abaqus/get_preproc_file/' in url:
        info = url.split('abaqus/get_preproc_file/')[1].split('/')
        preproc_id, filename = info[0], info[1]
        filepath = os.path.join(current_app.config['ABAQUS_PRE_PATH'], str(preproc_id), filename)
    elif 'optimize/get_optimize_file/' in url:
        info = url.split('optimize/get_optimize_file/')[1].split('/')
        optimize_id, filename = info[0], info[1]
        filepath = os.path.join(current_app.config['OPTIMIZE_PATH'], str(optimize_id), filename)
    elif 'optimize/get_template_file/' in url:
        info = url.split('optimize/get_template_file/')[1].split('/')
        template_id, filename = info[0], info[1]
        filepath = os.path.join(current_app.config['OPTIMIZE_TEMPLATE_PATH'], str(template_id), filename)
    else:
        return jsonify({'error': 'File not founded'}), 400

    data = request.get_json()
    content = data.get('content')

    if content:
        with open(filepath, 'w', encoding='utf-8') as file:
            file.write(content)
        return jsonify({'message': 'File saved successfully'})
    else:
        return jsonify({'error': 'Content not provided'}), 400
