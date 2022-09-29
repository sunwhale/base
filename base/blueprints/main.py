# -*- coding: utf-8 -*-
"""

"""
import os
import json

from flask import jsonify, render_template, flash, redirect, url_for, current_app, send_from_directory, request, abort, Blueprint
from flask_login import login_required, current_user


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('main/index.html')


@main_bp.route('/test', methods=['GET', 'POST'])
def test():
    return render_template('main/test.html')


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
