# -*- coding: utf-8 -*-
"""

"""
import json
import os
import shutil
import subprocess
import time

from flask import (Blueprint, abort, current_app, flash, jsonify, redirect, render_template, request,
                   send_from_directory, url_for)
from flask_login import current_user, login_required

from base.forms.abaqus import (JobForm, ParameterForm, ProjectForm, TemplateForm, ImportTemplateForm, UploadForm,
                               FigureSettingFrom, OdbForm)
from base.global_var import event_source
from base.utils.abaqus.Postproc import Postproc
from base.utils.abaqus.Solver import Solver
from base.utils.common import make_dir, dump_json, load_json
from base.utils.dir_status import (create_id, files_in_dir, subpaths_in_dir, get_job_status, get_project_status,
                                   get_template_status, project_jobs_detail, projects_detail, templates_detail,
                                   sub_dirs_int)
from base.utils.events_new import update_events_new
from base.utils.make_gif import make_gif
from base.utils.read_prescan import read_prescan
from base.utils.tree import json_to_ztree, odb_json_to_ztree

virtual_bp = Blueprint('virtual', __name__)


@virtual_bp.route('/manage_virtuals', methods=['GET', 'POST'])
@login_required
def manage_virtuals():
    return render_template('virtual/manage_virtuals.html')
