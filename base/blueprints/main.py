# -*- coding: utf-8 -*-
"""

"""
import os.path

from flask import (Blueprint, render_template, redirect, url_for, flash)

from flask_login import login_required

from base.decorators import admin_required, permission_required
from base.forms.main import ConfigurationForm
from base.settings import USER_CONF_FILE
from base.utils.common import dump_json, load_json

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('main/index.html')


@main_bp.route('/help')
def help():
    return render_template('main/help.html')


@main_bp.route('/configure', methods=['GET', 'POST'])
@login_required
@admin_required
def configure():
    form = ConfigurationForm()

    if form.validate_on_submit():
        message = {
            'ABAQUS': form.ABAQUS.data,
            'ABAQUS_FORTRAN': form.ABAQUS_FORTRAN.data,
            'MAX_CPUS': form.MAX_CPUS.data
        }
        dump_json(USER_CONF_FILE, message)
        flash('保存设置成功。', 'success')
        return redirect(url_for('.configure'))

    if os.path.exists(USER_CONF_FILE):
        message = load_json(USER_CONF_FILE)
        form.ABAQUS.data = message['ABAQUS']
        form.ABAQUS_FORTRAN.data = message['ABAQUS_FORTRAN']
        form.MAX_CPUS.data = message['MAX_CPUS']

    return render_template('main/configure.html', form=form)
