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


class ProjectForm(FlaskForm):
    name = StringField('项目名称', validators=[DataRequired(), Length(1, 62)])
    descript = TextAreaField('项目备注', render_kw={'rows': 12})
    job = StringField('缺省算例名', default='Job-1', validators=[DataRequired(), Length(1, 126)])
    user = StringField('缺省user文件', default='user.for')
    cpus = IntegerField('缺省算例使用CPU核心数量', default=1, validators=[DataRequired(), NumberRange(1, 16)])
    submit = SubmitField('提交')


class TemplateForm(ProjectForm):
    pass


class ImportTemplateForm(FlaskForm):
    name = SelectField('选择模板', coerce=str)
    submit = SubmitField('导入')

    def __init__(self, *args, **kwargs):
        super(ImportTemplateForm, self).__init__(*args, **kwargs)
        self.name.choices = ['0_模板名称']


class JobForm(FlaskForm):
    job = StringField('算例名', default='Job-1', validators=[DataRequired(), Length(1, 126)])
    user = StringField('算例user文件', default='user.for')
    cpus = IntegerField('算例使用CPU核心数量', default=1, validators=[DataRequired(), NumberRange(1, 16)])
    descript = TextAreaField('算例备注', render_kw={'rows': 12})
    submit = SubmitField('提交')


class ParameterForm(FlaskForm):
    para = TextAreaField('parameters.toml')
    submit = SubmitField('保存')


class OdbForm(FlaskForm):
    odb = StringField('ODB文件', default='', validators=[DataRequired()],
                      render_kw={'class': 'form-control', 'placeholder': "输入ODB文件路径，例如：abaqus/1/1/Job-1.odb"})
    submit = SubmitField('开始预扫描', render_kw={'class': 'btn btn-info btn-flat'})
