# -*- coding: utf-8 -*-
"""

"""
from flask import (Blueprint, render_template)
from flask_login import login_required

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('/links', methods=['GET'])
@login_required
def links():
    return render_template('tools/links.html')
