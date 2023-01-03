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
    descript = TextAreaField('项目描述', render_kw={'rows': 12})
    job = StringField('缺省算例名', default='Job-1', validators=[DataRequired(), Length(1, 128)])
    user = StringField('缺省user文件', default='user.for')
    cpus = IntegerField('缺省算例使用CPU核心数量', default=1, validators=[DataRequired(), NumberRange(1, 16)])
    submit = SubmitField('提交')


class TemplateForm(ProjectForm):
    pass


class JobForm(FlaskForm):
    job = StringField('算例名', default='Job-1', validators=[DataRequired(), Length(1, 128)])
    user = StringField('算例user文件', default='user.for')
    cpus = IntegerField('算例使用CPU核心数量', default=1, validators=[DataRequired(), NumberRange(1, 16)])
    submit = SubmitField('提交')


class ParameterForm(FlaskForm):
    para = TextAreaField('parameters.inp')
    submit = SubmitField('保存')


class FigureSettingFrom(FlaskForm):
    width = FloatField('width', default=200.0)
    height = FloatField('height', default=200.0)
    imageSize = StringField('imageSize', default='(600, 600)', validators=[DataRequired()])
    legend = SelectField('legend', coerce=str)
    plotState = SelectField('plotState', coerce=str)
    uniformScaleFactor = FloatField('uniformScaleFactor', default=1.0, validators=[DataRequired()])
    step = SelectField('step', coerce=str)
    frame = IntegerField('frame', default=-1, validators=[DataRequired()])
    variableLabel = SelectField('variableLabel', coerce=str)
    refinement = SelectField('refinement', coerce=str)
    outputPosition = SelectField('outputPosition', coerce=str)
    visibleEdges = SelectField('visibleEdges', coerce=str)
    maxAutoCompute = SelectField('maxAutoCompute', coerce=str)
    maxValue = FloatField('maxValue', default=1.0)
    minAutoCompute = SelectField('minAutoCompute', coerce=str)
    minValue = FloatField('minValue', default=0.0)
    colorMappings = SelectField('colorMappings', coerce=str)

    useStatus = SelectField('useStatus', coerce=str)
    statusLabel = SelectField('statusLabel', coerce=str)
    statusPosition = SelectField('statusPosition', coerce=str)
    statusRefinement = SelectField('statusRefinement', coerce=str)
    statusMinimum = FloatField('statusMinimum', default=1.0)
    statusMaximum = FloatField('statusMaximum', default=1.0)

    animate = SelectField('animate', coerce=str)
    frameInterval = IntegerField('frameInterval', default=1, validators=[DataRequired()])
    startFrame = IntegerField('startFrame', default=0)
    endFrame = IntegerField('endFrame', default=-1, validators=[DataRequired()])
    fps = IntegerField('fps', default=12, validators=[DataRequired()])

    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(FigureSettingFrom, self).__init__(*args, **kwargs)
        self.legend.choices = ['ON', 'OFF']
        self.plotState.choices = ['(CONTOURS_ON_DEF, )', '(CONTOURS_ON_UNDEF, )', '(UNDEFORMED, )', '(DEFORMED, )']
        self.step.choices = ['Step-1']
        self.variableLabel.choices = ['S']
        self.refinement.choices = ["(INVARIANT, 'Mises')"]
        self.outputPosition.choices = ['INTEGRATION_POINT', 'NODAL']
        self.visibleEdges.choices = ['ALL', 'EXTERIOR', 'FEATURE', 'FREE', 'NONE']
        self.maxAutoCompute.choices = ['ON', 'OFF']
        self.minAutoCompute.choices = ['ON', 'OFF']
        self.colorMappings.choices = ['Default', 'Part instance', 'Set', 'Material', 'Section', 'Element type', 'Averaging region', 'Internal set', 'Composite layup', 'Composite ply']
        
        self.useStatus.choices = ['False', 'True']
        self.statusLabel.choices = ['NT11']
        self.statusPosition.choices = ['INTEGRATION_POINT', 'NODAL']
        self.statusRefinement.choices = ['()']

        self.animate.choices = ['OFF', 'ON']
