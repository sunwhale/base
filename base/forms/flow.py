# -*- coding: utf-8 -*-
"""

"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from wtforms import (FloatField, IntegerField, SelectField, StringField, SubmitField, TextAreaField, BooleanField, RadioField)
from wtforms.validators import (DataRequired, Length, NumberRange)


class UploadForm(FlaskForm):
    filename = FileField('上传文件', validators=[FileRequired()])
    submit = SubmitField('上传')


class FlowForm(FlaskForm):
    name = StringField('流程名称', validators=[DataRequired(), Length(1, 62)])
    descript = TextAreaField('流程备注', render_kw={'rows': 12})
    submit = SubmitField('提交')


class JobForm(FlaskForm):
    project_id = SelectField('ABAQUS项目编号', coerce=str)
    job_id = IntegerField('需要重写的ABAQUS作业编号', default=1, validators=[DataRequired(), NumberRange(1, 1024 * 1024)])
    overwrite = BooleanField('重写作业（不选则新建作业）')
    job = StringField('算例名', default='Job-1', validators=[DataRequired(), Length(1, 126)])
    user = StringField('算例user文件', default='user.for')
    cpus = IntegerField('CPU数量', default=1, validators=[DataRequired(), NumberRange(1, 64)])
    descript = TextAreaField('算例备注', render_kw={'rows': 2})
    submit = SubmitField('提交')

    def __init__(self, *args, **kwargs):
        super(JobForm, self).__init__(*args, **kwargs)
        self.project_id.choices = ['']


class F1From(FlaskForm):
    tool_option = RadioField('刀具选项', choices=[('analytical', '理想刀具参数建模'), ('file', '从CAD文件导入')], default='analytical', validators=[DataRequired()])
    r1 = FloatField('r1，mm', default=20.0)
    r2 = FloatField('r2，mm', default=25.0)
    n = IntegerField('刀数', default=4, validators=[DataRequired(), NumberRange(4, 8)])
    length = FloatField('长度，mm', default=20.0)
    pitch = FloatField('螺距，mm', default=-60.0)
    tool_ref_point_x = FloatField('参考点x坐标，mm', default=0.0)
    tool_ref_point_y = FloatField('参考点y坐标，mm', default=0.0)
    tool_ref_point_z = FloatField('参考点z坐标，mm', default=0.0)
    step_file_name = SelectField('stp文件名称', coerce=str)
    tool_seed_size = FloatField('铣刀网格尺寸，mm', default=5.0)

    x_length_of_plane = FloatField('x方向长度，mm', default=50.0)
    y_length_of_plane = FloatField('y方向长度，mm', default=50.0)
    z_length_of_plane = FloatField('z方向长度，mm', default=10.0)
    plane_seed_size = FloatField('平面网格尺寸，mm', default=5.0)

    x_shift_of_tool = FloatField('初始x，mm', default=0.0)
    y_shift_of_tool = FloatField('初始y，mm', default=0.0)
    z_shift_of_tool = FloatField('初始z，mm', default=0.0)

    material_tool = SelectField('铣刀材料', coerce=str)
    material_plane = SelectField('平板材料', coerce=str)
    material_interaction = SelectField('接触属性', coerce=str)

    tool_rotation_speed = FloatField('铣刀转速，rpm', default=300.0)
    tool_shift_speed = FloatField('铣刀进给速度，mm/min', default=10.0)
    square_wave_width = FloatField('方波宽度，mm', default=25.0)
    square_wave_height = FloatField('方波高度，mm', default=50.0)
    square_wave_cycles = IntegerField('方波周期数', default=100, validators=[DataRequired(), NumberRange(1, 10000)])

    output_variables = StringField('输出变量', validators=[DataRequired(), Length(1, 1024)], default='S, LE, NT, STATUS')
    output_numIntervals = IntegerField('输出间隔数量', default=20, validators=[DataRequired(), NumberRange(1, 1024)])

    timeIncrementationMethod = SelectField('timeIncrementationMethod', coerce=str)
    userDefinedInc = FloatField('userDefinedInc', default=1.0e-7)
    step_time = FloatField('step_time', default=1.0)

    submit = SubmitField('保存当前参数')

    def __init__(self, *args, **kwargs):
        super(F1From, self).__init__(*args, **kwargs)
        self.step_file_name.choices = ['']
        self.timeIncrementationMethod.choices = ['AUTO', 'AUTOMATIC_EBE', 'FIXED_USER_DEFINED_INC']
        self.material_tool.choices = ['']
        self.material_plane.choices = ['']
        self.material_interaction.choices = ['']
