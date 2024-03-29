# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from wtforms import (IntegerField, StringField, SubmitField)
from wtforms.validators import (DataRequired, Length, NumberRange)


class ConfigurationForm(FlaskForm):
    ABAQUS = StringField('ABAQUS命令', default='abaqus', validators=[DataRequired(), Length(1, 62)])
    ABAQUS_FORTRAN = StringField('有Fortran编译环境的ABAQUS命令', default='abaqus',
                                 validators=[DataRequired(), Length(1, 62)])
    MAX_CPUS = IntegerField('计算可以使用的CPU总数量', default=4,
                            validators=[DataRequired(), NumberRange(1, 1024)])
    submit = SubmitField('保存')
