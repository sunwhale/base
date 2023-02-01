# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('/links', methods=['GET'])
@login_required
def links():
    return render_template('tools/links.html')
