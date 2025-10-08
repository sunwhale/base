# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (SelectField, StringField, SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, ValidationError, Length)


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
    submit = SubmitField('上传')


class ParameterForm(FlaskForm):
    submit = SubmitField('提交')


class ExperimentForm(FlaskForm):
    experiment_id = SelectField('实验项目编号', coerce=str)
    submit = SubmitField('保存')

    def __init__(self, *args, **kwargs):
        super(ExperimentForm, self).__init__(*args, **kwargs)
        self.experiment_id.choices = ['']


class OptimizeForm(FlaskForm):
    name = StringField('优化名称', validators=[DataRequired(), Length(1, 62)])
    type = SelectField('优化类型', coerce=str)
    para = StringField('参数列表', validators=[DataRequired(message="字段不能为空"), comma_separated_validator])
    descript = TextAreaField('优化备注', render_kw={'rows': 12})
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(OptimizeForm, self).__init__(*args, **kwargs)
        self.type.choices = ['解析函数', 'PYFEM', 'ABAQUS UMAT']


class SpecimenForm(FlaskForm):
    name = StringField('试件编号', default='1', validators=[DataRequired(), Length(1, 62)])
    descript = TextAreaField('实验备注', render_kw={'rows': 12})
    submit = SubmitField('提交')
