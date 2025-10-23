# -*- coding: utf-8 -*-
"""

"""
from flask import (Blueprint, jsonify, redirect, render_template, url_for, flash)

from base.decorators import permission_required
from base.global_var import event_manager

queue_bp = Blueprint('queue', __name__)


@queue_bp.route('/view_queue', methods=['GET', 'POST'])
@permission_required('RESOURCE')
def view_queue():
    active = event_manager.get_active()
    return render_template('queue/view_queue.html', active=active)


@queue_bp.route('/events', methods=['GET', 'POST'])
@permission_required('RESOURCE')
def events():
    e_wait, e_run, e_done = event_manager.get_status()
    events = {
        'in_queue': e_wait,
        'running': e_run,
        'done': e_done
    }
    return jsonify(events)


@queue_bp.route('/start', methods=['GET', 'POST'])
@permission_required('RESOURCE')
def start():
    event_manager.start()
    return redirect(url_for('.view_queue'))


@queue_bp.route('/stop', methods=['GET', 'POST'])
@permission_required('RESOURCE')
def stop():
    event_manager.stop()
    return redirect(url_for('.view_queue'))


@queue_bp.route('/clear', methods=['GET', 'POST'])
@permission_required('RESOURCE')
def clear():
    if not event_manager.get_active():
        event_manager.clear()
        flash('队列重置成功！', 'success')
    else:
        flash('队列正在运行中，请先暂停队列！', 'warning')
    return redirect(url_for('.view_queue'))
