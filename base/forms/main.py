# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from wtforms import (SelectField, StringField, SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, Length)


class ConfigurationForm(FlaskForm):
    ABAQUS = StringField('ABAQUS命令', default='abaqus', validators=[DataRequired(), Length(1, 62)])
    ABAQUS_FORTRAN = StringField('有Fortran编译环境的ABAQUS命令', default='abaqus_fortran', validators=[DataRequired(), Length(1, 62)])
    submit = SubmitField('提交')
