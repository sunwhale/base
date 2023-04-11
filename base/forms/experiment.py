# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, DateField, DecimalField, FloatField,
                     HiddenField, IntegerField, MultipleFileField,
                     PasswordField, SelectField, StringField, SubmitField,
                     TextAreaField, ValidationError)
from wtforms.validators import (URL, DataRequired, Length, NumberRange,
                                Optional, Regexp, ValidationError)


class UploadForm(FlaskForm):
    filename = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('上传')


class ExperimentForm(FlaskForm):
    name = StringField('项目名称', validators=[DataRequired(), Length(1, 60)])
    descript = TextAreaField('项目描述', render_kw={'rows': 12})
    submit = SubmitField('提交')
