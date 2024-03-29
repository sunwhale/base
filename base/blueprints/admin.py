# -*- coding: utf-8 -*-
"""

"""
from flask import Blueprint, flash, render_template, request
from flask_login import login_required

from base.decorators import admin_required, permission_required
from base.extensions import db
from base.forms.admin import EditProfileAdminForm
from base.models import Role, User
from base.security import redirect_back

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
@permission_required('MODERATE')
def index():
    user_count = User.query.count()
    locked_user_count = User.query.filter_by(locked=True).count()
    blocked_user_count = User.query.filter_by(active=False).count()
    return render_template('admin/index.html', user_count=user_count, locked_user_count=locked_user_count,
                           blocked_user_count=blocked_user_count)


@admin_bp.route('/profile/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(user_id):
    user = User.query.get_or_404(user_id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.name = form.name.data
        role = Role.query.get(form.role.data)
        if role.name == 'Locked':
            user.lock()
        user.role = role
        user.confirmed = form.confirmed.data
        user.active = form.active.data
        user.username = form.username.data
        user.email = form.email.data
        db.session.commit()
        flash('用户信息更新。/Profile updated.', 'success')
        return redirect_back()
    form.name.data = user.name
    form.role.data = user.role_id
    form.username.data = user.username
    form.email.data = user.email
    form.confirmed.data = user.confirmed
    form.active.data = user.active
    return render_template('admin/edit_profile.html', form=form, user=user)


@admin_bp.route('/block/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def block_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role.name in ['Administrator', 'Moderator']:
        flash('权限不足。/Permission denied.', 'warning')
    else:
        user.block()
        flash('账号冻结。/Account blocked.', 'info')
    return redirect_back()


@admin_bp.route('/unblock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def unblock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unblock()
    flash('账号解冻。Block canceled.', 'info')
    return redirect_back()


@admin_bp.route('/lock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def lock_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role.name in ['Administrator', 'Moderator']:
        flash('权限不足。/Permission denied.', 'warning')
    else:
        user.lock()
        flash('账号锁定。/Account locked.', 'info')
    return redirect_back()


@admin_bp.route('/unlock/user/<int:user_id>', methods=['POST'])
@login_required
@permission_required('MODERATE')
def unlock_user(user_id):
    user = User.query.get_or_404(user_id)
    user.unlock()
    flash('账号解锁。/Lock canceled.', 'info')
    return redirect_back()


@admin_bp.route('/manage/user')
@login_required
@permission_required('MODERATE')
def manage_user():
    filter_rule = request.args.get('filter', 'all')  # 'all', 'locked', 'blocked', 'administrator', 'moderator'
    page = request.args.get('page', 1, type=int)
    per_page = 10
    administrator = Role.query.filter_by(name='Administrator').first()
    moderator = Role.query.filter_by(name='Moderator').first()

    if filter_rule == 'locked':
        filtered_users = User.query.filter_by(locked=True)
    elif filter_rule == 'blocked':
        filtered_users = User.query.filter_by(active=False)
    elif filter_rule == 'administrator':
        filtered_users = User.query.filter_by(role=administrator)
    elif filter_rule == 'moderator':
        filtered_users = User.query.filter_by(role=moderator)
    else:
        filtered_users = User.query
    pagination = filtered_users.order_by(User.member_since.desc()).paginate(page=page, per_page=per_page)
    users = pagination.items
    return render_template('admin/manage_user.html', pagination=pagination, users=users)
