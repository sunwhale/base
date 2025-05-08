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
    r1 = FloatField('r1，mm', default=3.5)
    r2 = FloatField('r2，mm', default=5.0)
    n = IntegerField('刀数', default=4, validators=[DataRequired(), NumberRange(4, 8)])
    length = FloatField('长度，mm', default=10.0)
    pitch = FloatField('螺距，mm', default=-60.0)
    tool_seed_size = FloatField('铣刀网格尺寸，mm', default=1.0)

    x_length_of_plane = FloatField('x方向长度，mm', default=10.0)
    y_length_of_plane = FloatField('y方向长度，mm', default=10.0)
    z_length_of_plane = FloatField('z方向长度，mm', default=10.0)
    plane_seed_size = FloatField('平面网格尺寸，mm', default=1.0)

    x_shift_of_tool = FloatField('x，mm', default=0.0)
    y_shift_of_tool = FloatField('y，mm', default=0.0)
    z_shift_of_tool = FloatField('z，mm', default=0.0)

    material_tool = SelectField('material_tool', coerce=str)
    material_plane = SelectField('material_plane', coerce=str)

    timeIncrementationMethod = SelectField('timeIncrementationMethod', coerce=str)
    userDefinedInc = FloatField('userDefinedInc', default=1.0e-7)

    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super(CutFrom, self).__init__(*args, **kwargs)
        self.timeIncrementationMethod.choices = ['AUTO', 'AUTOMATIC_EBE', 'FIXED_USER_DEFINED_INC']
        self.material_tool.choices = ['']
        self.material_plane.choices = ['']
