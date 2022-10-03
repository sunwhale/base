# -*- coding: utf-8 -*-
"""

"""
from flask import (Blueprint, current_app, flash, redirect, render_template,
                   url_for)
from flask_login import (confirm_login, current_user, login_fresh,
                         login_required, login_user, logout_user)

from base.decorators import admin_required, permission_required
from base.emails import send_confirm_email, send_reset_password_email
from base.extensions import db
from base.forms.auth import (ForgetPasswordForm, LoginForm, RegisterForm,
                             ResetPasswordForm)
from base.models import User
from base.settings import Operations
from base.utils import generate_token, redirect_back, validate_token

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
                flash('登录成功。/Login success.', 'success')
                return redirect_back()
            else:
                flash('您的账号已被锁定。/Your account is blocked.', 'warning')
                return redirect(url_for('main.index'))
        flash('无效的邮箱或密码。/Invalid email or password.', 'warning')
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
    flash('登出成功。/Logout success.', 'success')
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
        flash('注册成功。/Register success.', 'success')
        return redirect(url_for('.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user is None:
            return redirect(url_for('main.index'))
        if validate_token(user=user, token=token, operation=Operations.RESET_PASSWORD,
                          new_password=form.password.data):
            flash('密码更新成功。/Password updated.', 'success')
            return redirect(url_for('.login'))
        else:
            flash('链接无效或过期。/Invalid or expired link.', 'danger')
            return redirect(url_for('.forget_password'))
    return render_template('auth/reset_password.html', form=form)


@auth_bp.route('/forget_password', methods=['GET', 'POST'])
def forget_password():
    form = ForgetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user:
            token = generate_token(user=user, operation=Operations.RESET_PASSWORD)
            send_reset_password_email(user=user, token=token)
            flash('密码重置邮件已发送，请检查您的收件箱。/Password reset email sent, check your inbox.', 'info')
            return redirect(url_for('.login'))
        flash('无效邮箱。/Invalid email.', 'warning')
        return redirect(url_for('.forget_password'))
    return render_template('auth/reset_password.html', form=form)
