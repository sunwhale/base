# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import (BooleanField, DateField, DecimalField, FloatField,
                     HiddenField, IntegerField, MultipleFileField,
                     PasswordField, SelectField, StringField, SubmitField,
                     TextAreaField, ValidationError)
from wtforms.validators import (URL, DataRequired, Length, NumberRange,
                                Optional, Regexp, ValidationError)


class UploadForm(FlaskForm):
    filename = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('上传')


class ProjectForm(FlaskForm):
    name = StringField('项目名称', validators=[DataRequired(), Length(1, 60)])
    descript = TextAreaField('项目描述')
    job = StringField('缺省算例名', default='Job-1', validators=[DataRequired(), Length(1, 128)])
    user = StringField('缺省user文件', default='user.for')
    cpus = IntegerField('缺省算例使用CPU核心数量', default=1, validators=[DataRequired(), NumberRange(1, 16)])
    submit = SubmitField(u'提交')


class JobForm(FlaskForm):
    job = StringField('算例名', default='Job-1', validators=[DataRequired(), Length(1, 128)])
    user = StringField('算例user文件', default='user.for')
    cpus = IntegerField('算例使用CPU核心数量', default=1, validators=[DataRequired(), NumberRange(1, 16)])
    submit = SubmitField(u'提交')


class ParameterForm(FlaskForm):
    para = TextAreaField('parameters.inp')
    submit = SubmitField(u'保存')


class FigureSettingFrom(FlaskForm):
    imageSize = StringField('imageSize', default='(600, 600)', validators=[DataRequired()])
    legend = SelectField('legend', coerce=str)
    plotState = SelectField('plotState', coerce=str)
    uniformScaleFactor = FloatField('uniformScaleFactor', default=1.0, validators=[DataRequired()])
    # step = StringField('step', default='Step-1', validators=[DataRequired()])
    step = SelectField('step', coerce=str)
    frame = IntegerField('frame', default=-1, validators=[DataRequired()])
    # variableLabel = StringField('variableLabel', default='S', validators=[DataRequired()])
    variableLabel = SelectField('variableLabel', coerce=str)
    refinement = StringField('refinement', default="(INVARIANT, 'Mises')", validators=[DataRequired()])
    outputPosition = SelectField('outputPosition', coerce=str)
    maxAutoCompute = SelectField('maxAutoCompute', coerce=str)
    maxValue = FloatField('maxValue', default=1.0)
    minAutoCompute = SelectField('minAutoCompute', coerce=str)
    minValue = FloatField('minValue', default=0.0)
    submit = SubmitField(u'提交')

    def __init__(self, *args, **kwargs):
        super(FigureSettingFrom, self).__init__(*args, **kwargs)
        self.legend.choices = ['ON', 'OFF']
        self.plotState.choices = ['(CONTOURS_ON_DEF, )', '(CONTOURS_ON_UNDEF, )']
        self.step.choices = ['Step-1']
        self.variableLabel.choices = ['S', 'E', 'NT11']
        self.outputPosition.choices = ['INTEGRATION_POINT', 'NODAL', 'ELEMENT_NODAL', 'CENTROID']
        self.maxAutoCompute.choices = ['ON', 'OFF']
        self.minAutoCompute.choices = ['ON', 'OFF']
