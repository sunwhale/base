# -*- coding: utf-8 -*-
"""

"""
import os

from flask import abort, render_template, flash, redirect, url_for, current_app, send_from_directory, request, abort, Blueprint
from flask_login import login_required, current_user


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('main/index.html')


@main_bp.route('/test')
def test():
    abort(400)