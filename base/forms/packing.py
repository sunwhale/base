# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, DateField, DecimalField, FileField,
                     FloatField, HiddenField, IntegerField, MultipleFileField,
                     PasswordField, SelectField, StringField, SubmitField,
                     TextAreaField, ValidationError)
from wtforms.validators import (URL, DataRequired, Length, NumberRange,
                                Optional, Regexp, ValidationError)


class PackingForm(FlaskForm):
    ncircle = IntegerField('每次填充的球体数目', default=8, validators=[DataRequired(), NumberRange(0, 1024)])
    gap = DecimalField('两球间距', default=0.0, validators=[NumberRange(0, 0.1)])
    num_add = IntegerField('最大填充次数', default=10000, validators=[DataRequired(), NumberRange(0, 1000000)])
    dt0 = DecimalField('初始时间步长', default=0.01, validators=[DataRequired(), NumberRange(0, 1)])
    dt_interval = IntegerField('运动/每填充次数', default=1000000, validators=[DataRequired(), NumberRange(0, 1000000000)])
    max_iter = IntegerField('计算球体碰撞的最大迭代次数', default=1000, validators=[DataRequired(), NumberRange(0, 1024)])
    size = StringField('计算域尺寸，毫米', default='[[0,1],[0,1]]', validators=[DataRequired()])
    rayleigh_para = DecimalField('球体直径瑞利分布参数，微米', default=20.32, validators=[DataRequired(), NumberRange(0, 100)])
    num_ball = IntegerField('填充球体数量', default=5000, validators=[DataRequired(), NumberRange(0, 10000)])
    rad_max = DecimalField('最大球体直径，微米', default=100, validators=[DataRequired(), NumberRange(0, 1000)])
    rad_min = DecimalField('最小球体直径，微米', default=10, validators=[DataRequired(), NumberRange(0, 1000)])
    submit = SubmitField(u'提交')


class SubmodelForm(FlaskForm):
    gap = DecimalField('两球间距', default=0.0, validators=[NumberRange(0, 0.1)])
    ndiv = IntegerField('每个坐标轴方向等分数', default=2, validators=[DataRequired(), NumberRange(1, 100)])
    submit = SubmitField('生成子模型')


class MeshForm(FlaskForm):
    gap = DecimalField('两圆间距，gap', default=0.0, validators=[NumberRange(0, 0.1)])
    node_shape = StringField('划分网格节点维度',default='[128,128]',validators=[DataRequired()])
    element_type = StringField('单元类型，CPE4/C3D8等',default='CPE4T',validators=[DataRequired()])
    submit = SubmitField('提交')


class UploadForm(FlaskForm):
    filename = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('上传')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 60)])
    body = TextAreaField('Body', validators=[DataRequired()])
    submit = SubmitField('提交')


class ABAQUSForm(FlaskForm):
    name = StringField('项目名称', render_kw = {'readonly': True})
    descript = TextAreaField('项目描述')
    job = StringField('缺省算例名', default='Job-1')
    user = StringField('缺省user文件', default='user.for')
    cpus = IntegerField('缺省算例使用CPU核心数量', default=1, validators=[DataRequired(), NumberRange(1, 16)])
    submit = SubmitField(u'提交')