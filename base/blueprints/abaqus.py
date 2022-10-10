# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil
import time

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect,
                   render_template, request, send_from_directory, url_for)
from flask_login import current_user, login_required

from tools.dir_status import create_id, docs_detail

abaqus_bp = Blueprint('abaqus', __name__)


@abaqus_bp.route('/', methods=['GET', 'POST'])
@login_required
def index():

    return 'abaqus'
