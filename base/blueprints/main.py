# -*- coding: utf-8 -*-
"""

"""
from flask import (Blueprint, render_template, redirect, url_for)
from flask_login import current_user, login_required

from base.decorators import admin_required
from base.forms.main import ConfigurationForm
from utils.common import dump_json, load_json

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('main/index.html')


@main_bp.route('/help')
def help():
    return render_template('main/help.html')


@main_bp.route('/configure')
@admin_required
def configure():
    form = ConfigurationForm()
    conf_file = '.conf'

    if form.validate_on_submit():
        message = {
            'ABAQUS': form.ABAQUS.data,
            'ABAQUS_FORTRAN': form.ABAQUS_FORTRAN.data,
        }
        dump_json(conf_file, message)
        return redirect(url_for('.conf'))

    message = load_json(conf_file)
    form.ABAQUS.data = message['ABAQUS']
    form.ABAQUS_FORTRAN.data = message['ABAQUS_FORTRAN']

    return render_template('main/configure.html', form=form)