# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (SelectField, StringField, SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, Length)


class UploadForm(FlaskForm):
    filename = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('上传')


class ParameterForm(FlaskForm):
    para = TextAreaField('parameters.inp')
    submit = SubmitField('保存')


class MaterialForm(FlaskForm):
    name = StringField('材料名称', validators=[DataRequired(), Length(1, 62)])
    type = SelectField('材料类型', coerce=str)
    descript = TextAreaField('材料备注', render_kw={'rows': 12})
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(MaterialForm, self).__init__(*args, **kwargs)
        self.type.choices = ['ABAQUS', 'ABAQUS UMAT']


class SpecimenForm(FlaskForm):
    name = StringField('试件编号', default='1', validators=[DataRequired(), Length(1, 62)])
    descript = TextAreaField('实验备注', render_kw={'rows': 12})
    submit = SubmitField('提交')
