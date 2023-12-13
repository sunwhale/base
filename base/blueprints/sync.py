# -*- coding: utf-8 -*-
"""

"""
from flask import (Blueprint, jsonify, redirect, render_template, url_for)
from flask_login import login_required

sync_bp = Blueprint('sync', __name__)


@sync_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():
    return render_template('sync/index.html')
