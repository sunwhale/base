# -*- coding: utf-8 -*-
"""

"""
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import (BooleanField, PasswordField, StringField, SubmitField, ValidationError)
from wtforms.validators import (DataRequired, Email, EqualTo, Length, Regexp)

from base.models import User


class EditProfileForm(FlaskForm):
    name = StringField('姓名/Name', validators=[DataRequired(), Length(1, 30)])
    username = StringField('用户名/Username', validators=[DataRequired(), Length(1, 30), Regexp('^[a-zA-Z0-9]*$',
                                                                                                message='The username should contain only a-z, A-Z and 0-9.')])
    submit = SubmitField('提交/Submit')

    def validate_username(self, field):
        if field.data != current_user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已经存在。/The username is already in use.')


class ChangeEmailForm(FlaskForm):
    email = StringField('New Email', validators=[DataRequired(), Length(1, 254), Email()])
    submit = SubmitField()

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('该邮箱已经存在。/The email is already in use.')


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Old Password', validators=[DataRequired()])
    password = PasswordField('New Password', validators=[
        DataRequired(), Length(8, 128), EqualTo('password2')])
    password2 = PasswordField('Confirm Password', validators=[DataRequired()])
    submit = SubmitField()


class PrivacySettingForm(FlaskForm):
    public_collections = BooleanField('Public my collection')
    submit = SubmitField()


class DeleteAccountForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(1, 30)])
    submit = SubmitField()

    def validate_username(self, field):
        if field.data != current_user.username:
            raise ValidationError('Wrong username.')
