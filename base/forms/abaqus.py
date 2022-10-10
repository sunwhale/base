# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateField, DecimalField, FileField,
                     FloatField, HiddenField, IntegerField, MultipleFileField,
                     PasswordField, SelectField, StringField, SubmitField,
                     TextAreaField, ValidationError)
from wtforms.validators import (URL, DataRequired, Length, NumberRange,
                                Optional, Regexp, ValidationError)


class UploadForm(FlaskForm):
    filename = FileField('上传文件')
    submit = SubmitField('提交')
