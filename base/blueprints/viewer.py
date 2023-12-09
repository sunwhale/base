# -*- coding: utf-8 -*-
"""

"""

import os
from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import login_required

viewer_bp = Blueprint('viewer', __name__)


@login_required
@viewer_bp.route('/', methods=['GET', 'POST'])
def index():
    return render_template('viewer/index.html')


@viewer_bp.route('/resources/<path:filename>', methods=['GET', 'POST'])
def resources(filename):
    return send_from_directory(os.path.join(current_app.config['STATIC_PATH'], 'viewer', 'resources'), filename)
