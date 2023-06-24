# -*- coding: utf-8 -*-
"""

"""
from flask import (current_app)
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (IntegerField, SelectField, StringField, SubmitField, TextAreaField)
from wtforms.validators import (DataRequired, Length, NumberRange)

from base.utils.dir_status import (templates_detail)


class UploadForm(FlaskForm):
    filename = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('上传')


class VirtualForm(FlaskForm):
    name = StringField('项目名称', validators=[DataRequired(), Length(1, 62)])
    template = SelectField('选择模板', coerce=str)
    descript = TextAreaField('项目描述', render_kw={'rows': 12})
    job = StringField('缺省算例名', default='Job-1', validators=[DataRequired(), Length(1, 126)])
    user = StringField('缺省user文件', default='user.for')
    cpus = IntegerField('缺省算例使用CPU核心数量', default=1, validators=[DataRequired(), NumberRange(1, 16)])
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(VirtualForm, self).__init__(*args, **kwargs)

        templates_path = current_app.config['ABAQUS_TEMPLATE_PATH']
        template_dict = templates_detail(templates_path)
        template_list = []
        for template in template_dict['data']:
            template_list.append('%s_%s' % (template['template_id'], template['name']))

        self.template.choices = template_list


class ParameterForm(FlaskForm):
    para = TextAreaField('parameters.inp')
    submit = SubmitField('保存')
