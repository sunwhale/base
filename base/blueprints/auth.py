# -*- coding: utf-8 -*-
"""

"""
from flask import render_template, flash, redirect, url_for, Blueprint
from flask_login import login_user, logout_user, login_required, current_user, login_fresh, confirm_login

from base.decorators import admin_required, permission_required
from base.extensions import db
from base.forms.auth import LoginForm, RegisterForm, ForgetPasswordForm, ResetPasswordForm
from base.models import User
from base.settings import Operations
from base.utils import generate_token, validate_token, redirect_back

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is not None and user.validate_password(form.password.data):
            if login_user(user, form.remember_me.data):
                flash('登录成功。', 'success')
                return redirect_back()
            else:
                flash('您的账号已被锁定。', 'warning')
                return redirect(url_for('main.index'))
        flash('无效的邮箱或密码。', 'warning')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/re-authenticate', methods=['GET', 'POST'])
@login_required
def re_authenticate():
    if login_fresh():
        return redirect(url_for('main.index'))

    form = LoginForm()
    if form.validate_on_submit() and current_user.validate_password(form.password.data):
        confirm_login()
        return redirect_back()
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('登出成功。', 'success')
    return redirect(url_for('main.index'))


@auth_bp.route('/register', methods=['GET', 'POST'])
@login_required
@admin_required
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data.lower()
        username = form.username.data
        password = form.password.data
        user = User(name=name, email=email, username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('注册成功。', 'success')
        return redirect(url_for('.login'))
    return render_template('auth/register.html', form=form)
