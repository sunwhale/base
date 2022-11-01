# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import (BooleanField, DateField, DecimalField,
                     FloatField, HiddenField, IntegerField, MultipleFileField,
                     PasswordField, SelectField, StringField, SubmitField,
                     TextAreaField, ValidationError)
from wtforms.validators import (URL, DataRequired, Length, NumberRange,
                                Optional, Regexp, ValidationError)


class UploadForm(FlaskForm):
    filename = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('上传')


class ProjectForm(FlaskForm):
    name = StringField('项目名称', validators=[DataRequired(), Length(1, 60)])
    descript = TextAreaField('项目描述')
    submit = SubmitField(u'提交')


class JobForm(FlaskForm):
    job = StringField('算例inp文件', default='Job-1.inp', validators=[DataRequired(), Length(1, 128)])
    user = StringField('算例user文件', default='user.for')
    cpus = IntegerField('算例使用CPU核心数量', default=1, validators=[DataRequired(), NumberRange(1, 16)])
    submit = SubmitField(u'提交')