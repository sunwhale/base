# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, DateField, DecimalField, FloatField,
                     HiddenField, IntegerField, MultipleFileField,
                     DateTimeField, SelectField, StringField, SubmitField,
                     TextAreaField, ValidationError)
from wtforms.validators import (URL, DataRequired, Length, NumberRange,
                                Optional, Regexp, ValidationError)


class UploadForm(FlaskForm):
    filename = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('上传')


class ParameterForm(FlaskForm):
    para = TextAreaField('parameters.inp')
    submit = SubmitField('保存')


class ExperimentForm(FlaskForm):
    name = StringField('项目名称', validators=[DataRequired(), Length(1, 64)])
    material = StringField('材料', validators=[DataRequired(), Length(1, 64)])
    type = SelectField('实验类型', coerce=str)
    standard = StringField('参考标准', default='无')
    parameters = TextAreaField('实验参数', default='请按照以下格式输入实验参数，例如：\nTemperature, ℃ = \nKt = ', render_kw={'rows': 12})
    descript = TextAreaField('项目详情', render_kw={'rows': 12})
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(ExperimentForm, self).__init__(*args, **kwargs)
        self.type.choices = sorted(['单调拉伸', '原位拉伸', '剪切', '蠕变', '应力松弛', '等温疲劳', '其他'])


class SpecimenForm(FlaskForm):
    name = StringField('试件编号', default='1', validators=[DataRequired(), Length(1, 128)])
    # time = DateTimeField('实验时间', format='%Y-%m-%d %H:%M:%S')
    descript = TextAreaField('实验详情', render_kw={'rows': 12})
    submit = SubmitField('提交')