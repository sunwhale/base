# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (FloatField, IntegerField, SelectField, StringField, SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, Length, NumberRange)


class UploadForm(FlaskForm):
    filename = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('上传')


class CutFrom(FlaskForm):
    r1 = FloatField('r1', default=3.5)
    r2 = FloatField('r2', default=5.0)
    n = IntegerField('n', default=4)
    length = FloatField('length', default=10.0)

    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super(CutFrom, self).__init__(*args, **kwargs)
