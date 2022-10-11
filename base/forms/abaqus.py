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
    submit = SubmitField('提交')
