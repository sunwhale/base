# -*- coding: utf-8 -*-
"""

"""
from flask import (Blueprint, jsonify, redirect, render_template, url_for)
from flask_login import login_required

from base.global_var import event_manager

queue_bp = Blueprint('queue', __name__)


@queue_bp.route('/view_queue', methods=['GET', 'POST'])
@login_required
def view_queue():
    active = event_manager.get_active()
    return render_template('queue/view_queue.html', active=active)


@queue_bp.route('/events', methods=['GET', 'POST'])
@login_required
def events():
    e_wait, e_run, e_done = event_manager.get_status()
    events = {
        'in_queue': e_wait,
        'running': e_run,
        'done': e_done
    }
    return jsonify(events)


@queue_bp.route('/start', methods=['GET', 'POST'])
@login_required
def start():
    event_manager.start()
    return redirect(url_for('.view_queue'))


@queue_bp.route('/stop', methods=['GET', 'POST'])
@login_required
def stop():
    event_manager.stop()
    return redirect(url_for('.view_queue'))
