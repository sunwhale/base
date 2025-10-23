# -*- coding: utf-8 -*-
"""

"""

import os

from flask import (Blueprint, current_app, render_template, send_from_directory)

from base.decorators import permission_required

viewer_bp = Blueprint('viewer', __name__)


@viewer_bp.route('/', methods=['GET', 'POST'])
@permission_required('PYFEM')
def index():
    return render_template('viewer/index.html')


@viewer_bp.route('/resources/<path:filename>', methods=['GET', 'POST'])
def resources(filename):
    return send_from_directory(os.path.join(current_app.config['STATIC_PATH'], 'viewer', 'resources'), filename)
