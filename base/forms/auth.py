# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email, EqualTo, Regexp

from base.models import User


class LoginForm(FlaskForm):
    email = StringField(
        '邮箱/Email', validators=[DataRequired(), Length(1, 254), Email()])
    password = PasswordField('密码/Password', validators=[DataRequired()])
    remember_me = BooleanField('记住我的登录状态')
    submit = SubmitField('登录/Submit')


class RegisterForm(FlaskForm):
    name = StringField('姓名/Name', validators=[DataRequired(), Length(1, 30)])
    email = StringField(
        '邮箱/Email', validators=[DataRequired(), Length(1, 254), Email()])
    username = StringField('用户名/Username', validators=[DataRequired(), Length(1, 20), Regexp(
        '^[a-zA-Z0-9]*$', message='The username should contain only a-z, A-Z and 0-9.')])
    password = PasswordField(
        '密码/Password', validators=[DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('确认密码/Confirm password',
                              validators=[DataRequired()])
    submit = SubmitField('提交/Submit')

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('该邮箱已被注册。/The email is already in use.')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已被注册。/The username is already in use.')


class ForgetPasswordForm(FlaskForm):
    email = StringField(
        '请输入要重置密码的邮箱帐号', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField('下一步')


class ResetPasswordForm(FlaskForm):
    email = StringField(
        '邮箱/Email', validators=[DataRequired(), Length(1, 254), Email()])
    password = PasswordField(
        '密码/Password', validators=[DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('确认密码/Confirm password',
                              validators=[DataRequired()])
    submit = SubmitField('提交/Submit')
