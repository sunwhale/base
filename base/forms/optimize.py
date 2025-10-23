# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (SelectField, StringField, SubmitField, TextAreaField, FloatField, IntegerField)
from wtforms.validators import (DataRequired, ValidationError, Length, NumberRange)


def comma_separated_validator(form, field):
    """自定义逗号间隔字符串验证器"""
    value = field.data

    # 基本格式检查
    if not value:
        return  # DataRequired会处理空值

    # 检查是否包含逗号
    if ',' not in value:
        raise ValidationError('必须包含逗号分隔符')

    # 分割并检查每个部分
    parts = [part.strip() for part in value.split(',')]

    # 检查是否有空部分
    if any(not part for part in parts):
        raise ValidationError('逗号之间不能为空')

    # 检查每个部分的合法性（可根据需要自定义）
    for i, part in enumerate(parts):
        if len(part) < 1:  # 示例：每个部分至少1个字符
            raise ValidationError(f'第{i + 1}部分太短')
        # 可添加其他检查，如特定字符限制


class UploadForm(FlaskForm):
    filename = FileField('上传文件', validators=[FileRequired()])
    submit_upload = SubmitField('上传')


class ParameterForm(FlaskForm):
    submit_parameter = SubmitField('保存参数设置')


class ExperimentForm(FlaskForm):
    experiment_id = SelectField('实验项目编号', coerce=str)
    submit_experiment = SubmitField('保存实验设置')

    def __init__(self, *args, **kwargs):
        super(ExperimentForm, self).__init__(*args, **kwargs)
        self.experiment_id.choices = ['']


class PreprocForm(FlaskForm):
    strain_shift = FloatField('应变平移量', default=0.0)
    target_rows = IntegerField('目标数据行数（用于数据缩减）', default=100, validators=[DataRequired(), NumberRange(1, 100000)])
    strain_start = FloatField('应变范围起始值', default=0.0)
    strain_end = FloatField('应变范围结束值', default=1.0)
    stress_start = FloatField('应力范围起始值', default=0.0)
    stress_end = FloatField('应力范围结束值', default=1.0)
    threshold = FloatField('弹性极限判断阈值', default=0.1)
    fracture_slope_criteria = FloatField('断裂应变判断的斜率阈值', default=-50.0)
    preproc_mode = SelectField('预处理模式', coerce=str)
    submit_preproc = SubmitField('保存预处理设置')

    def __init__(self, *args, **kwargs):
        super(PreprocForm, self).__init__(*args, **kwargs)
        self.preproc_mode.choices = ['基础预处理', '截取弹性极限之前的部分', '截取断裂应变之前的部分', '截取极限应力之前的部分', '截取指定应变范围',
                                     '截取指定应力范围']


class OptimizeForm(FlaskForm):
    name = StringField('优化名称', validators=[DataRequired(), Length(1, 62)])
    para = StringField('参数列表', validators=[DataRequired(message="字段不能为空"), comma_separated_validator])
    job = StringField('优化算例', default='Optimize-1', validators=[DataRequired(), Length(1, 126)])
    descript = TextAreaField('优化备注', render_kw={'rows': 12})
    submit_experiment = SubmitField('提交')


class TemplateForm(OptimizeForm):
    pass
