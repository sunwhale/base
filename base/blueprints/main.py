# -*- coding: utf-8 -*-
"""

"""
import json
import os

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('main/index.html')


@main_bp.route('/test', methods=['GET', 'POST'])
def test():
    return 'Hello world!'


@main_bp.route('/data', methods=['POST'])
def data():
    d = request.form['exceldata']
    with open('data.txt', 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False)
    return d


@main_bp.route('/readdata', methods=['POST'])
def readdata():
    with open('data.txt', 'r', encoding='utf-8') as f:
        d = json.load(f)
    return d
