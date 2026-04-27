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


class F1Form(FlaskForm):
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
    tool_shift_speed = FloatField('铣刀平移速度，mm/min', default=10.0)

    temperature_tool_z1 = FloatField('铣刀端面温度，℃', default=20.0)
    temperature_tool_init = FloatField('铣刀初始温度，℃', default=20.0)
    temperature_plane_init = FloatField('平板初始温度，℃', default=20.0)

    tool_path_type = RadioField('刀具路径选项', choices=[('square_wave', '方波铣削'), ('drill', '钻孔'), ('tool_path_file', '刀具路径文件')], default='square_wave', validators=[DataRequired()])

    square_wave_width = FloatField('方波宽度，mm', default=30.0)
    square_wave_height = FloatField('方波高度，mm', default=70.0)
    square_wave_depth = FloatField('方波深度，mm', default=5.0)
    square_wave_head_shift = FloatField('头部平移量', default=0.0, validators=[NumberRange(0.0, 1.0)])
    square_wave_tail_shift = FloatField('尾部平移量', default=0.0, validators=[NumberRange(0.0, 1.0)])
    square_wave_cycles = IntegerField('面内周期数', default=2, validators=[DataRequired(), NumberRange(1, 10000)])
    square_wave_layers = IntegerField('深度层数', default=1, validators=[DataRequired(), NumberRange(1, 10000)])
    drill_depth = FloatField('钻孔深度，mm', default=10.0)
    tool_path_file_name = SelectField('刀具路径文件', coerce=str)

    output_variables = StringField('输出变量', validators=[DataRequired(), Length(1, 1024)], default='U, RF, S, LE, NT, STATUS')
    output_numIntervals = IntegerField('输出增量步数量', default=20, validators=[DataRequired(), NumberRange(1, 1024)])

    timeIncrementationMethod = SelectField('时间增量步长方法', coerce=str)
    userDefinedInc = FloatField('用户自定义增量步长', default=1.0e-7)
    step_time = FloatField('载荷步时间，s', default=1.0)
    mass_scaling_factor = FloatField('质量缩放系数', default=1.0)
    linearBulkViscosity = FloatField('线性体积粘度系数', default=0.2)
    quadBulkViscosity = FloatField('二次体粘滞系数‌', default=2.5)

    submit = SubmitField('保存当前参数')

    def __init__(self, *args, **kwargs):
        super(F1Form, self).__init__(*args, **kwargs)
        self.step_file_name.choices = ['']
        self.tool_path_file_name.choices = ['']
        self.timeIncrementationMethod.choices = ['AUTO', 'AUTOMATIC_EBE', 'FIXED_USER_DEFINED_INC']
        self.material_tool.choices = ['']
        self.material_plane.choices = ['']
        self.material_interaction.choices = ['']


class F2Form(FlaskForm):
    n = IntegerField('环向等分数 n', default=9, validators=[DataRequired()])
    d = FloatField('药柱直径 d (mm)', default=3529.0)
    x0 = FloatField('内轮廓距离 x0 (mm)', default=500.0)

    l_c1_c2 = FloatField('前后椭圆中心距离 (mm)', default=17300.0)
    ellipse_ratio = FloatField('椭圆长短轴比', default=1.69)
    a_front = FloatField('前椭圆长轴 (mm)', default=1772.47)
    a_behind = FloatField('后椭圆长轴 (mm)', default=1772.47)
    rotate_angle_deg = FloatField('旋转体转角 (度)', default=40.0)

    block_length = FloatField('药块长度 (mm)', default=1508.0)
    block_insulation_thickness_z = FloatField('z方向绝热层厚度 (mm)', default=3.0)
    block_insulation_thickness_r = FloatField('r方向绝热层厚度 (mm)', default=3.0)
    block_insulation_thickness_t = FloatField('θ方向绝热层厚度 (mm)', default=3.0)
    block_gap_z = FloatField('z方向药块间隙 (mm)', default=8.0)
    block_gap_t = FloatField('θ方向药块间隙 (mm)', default=8.0)

    slot_deep = FloatField('星槽深度 (mm)', default=380.0)
    slot_ellipse_a = FloatField('星槽椭圆长轴 a (mm)', default=50.0)
    slot_ellipse_b = FloatField('星槽椭圆短轴 b (mm)', default=25.0)

    angle_demolding_1 = FloatField('环向脱模角度 (度)', default=1.5)
    burn_offset = FloatField('燃面退移量 (mm)', default=0.0)
    outer_partition_offset = FloatField('外轮廓剖分偏移量 (mm)', default=300.0)
    element_size = FloatField('单元尺寸 (mm)', default=40.0)
    insert_czm = BooleanField('是否插入内聚力单元', default=False)
    is_shared_node = BooleanField('随动胶和药块是否共节点，mm', default=False)
    size = SelectField('对称性', coerce=str)

    front_offset = FloatField('头部坐标系与全局坐标系的偏移 (mm)', default=350.0)
    front_ref_length = FloatField('头部参考长度 (mm)', default=509.0)
    r_cut_front = FloatField('头部星槽切割半径 (mm)', default=460.0)
    length_front = FloatField('头部拉伸长度 (mm)', default=1500.0)
    p0_x_front = FloatField('头部p0点 x坐标 (mm)', default=-857.5)
    p0_y_front = FloatField('头部p0点 y坐标 (mm)', default=794.0)
    theta0_deg_front = FloatField('头部p0点切线角度 (度)', default=90.0)
    p3_x_front = FloatField('头部p3点 x坐标 (mm)', default=0.0)
    p3_y_front = FloatField('头部p3点 y坐标 (mm)', default=1762.5)
    theta3_deg_front = FloatField('头部p3点切线角度 (度)', default=0.0)
    r1_front = FloatField('头部三段圆弧 r1 (mm)', default=829.41)
    r2_front = FloatField('头部三段圆弧 r2 (mm)', default=1515.05)
    r3_front = FloatField('头部三段圆弧 r3 (mm)', default=641.21)

    behind_ref_length = FloatField('尾部参考长度 (mm)', default=917.08)
    r_cut_behind = FloatField('尾部星槽切割半径 (mm)', default=460.0)
    length_behind = FloatField('尾部拉伸长度 (mm)', default=1500.0)
    p0_x_behind = FloatField('尾部p0点 x坐标 (mm)', default=683.73)
    p0_y_behind = FloatField('尾部p0点 y坐标 (mm)', default=1109.770)
    theta0_deg_behind = FloatField('尾部p0点切线角度 (度)', default=-90.0)
    p3_x_behind = FloatField('尾部p3点 x坐标 (mm)', default=0.0)
    p3_y_behind = FloatField('尾部p3点 y坐标 (mm)', default=1762.5)
    theta3_deg_behind = FloatField('尾部p3点切线角度 (度)', default=0.0)
    r1_behind = FloatField('尾部三段圆弧 r1 (mm)', default=525.61)
    r2_behind = FloatField('尾部三段圆弧 r2 (mm)', default=1075.96)
    r3_behind = FloatField('尾部三段圆弧 r3 (mm)', default=569.38)

    shell_r_in = FloatField('壳体中部内半径 (mm)', default=1777.5)
    shell_r_out = FloatField('壳体中部外半径 (mm)', default=1811.5)
    shell_theta_out_deg_front = FloatField('壳体头部外侧锥角 (度)', default=0.49)
    shell_theta_out_deg_behind = FloatField('壳体尾部外侧锥角 (度)', default=0.49)
    shell_r_out_at_a_front = FloatField('壳体外侧头部椭圆长轴处半径 (mm)', default=1797)
    shell_r_out_at_a_behind = FloatField('壳体外侧尾部椭圆长轴处半径 (mm)', default=1797)
    shell_theta_in_deg_front = FloatField('壳体头部内侧锥角 (度)', default=0.24)
    shell_theta_in_deg_behind = FloatField('壳体尾部内侧锥角 (度)', default=0.24)
    shell_r_in_front = FloatField('壳体前缘内侧半径 (mm)', default=562.5)
    shell_r_in_behind = FloatField('壳体尾缘内侧半径 (mm)', default=942.5)
    shell_l_c1_out = FloatField('壳体前缘距离前椭圆中心轴向距离 (mm)', default=1105.75)
    shell_l_c2_out = FloatField('壳体尾缘距离后椭圆中心轴向距离 (mm)', default=968.46)

    # shell_insulation_theta_in_deg_front = FloatField('头部绝热层内束角，度', default=0.16)
    # shell_insulation_theta_in_deg_behind = FloatField('尾部绝热层内束角，度', default=0.16)

    material_tool = SelectField('铣刀材料', coerce=str)
    material_plane = SelectField('平板材料', coerce=str)
    material_interaction = SelectField('接触属性', coerce=str)

    submit = SubmitField('保存当前参数')

    def __init__(self, *args, **kwargs):
        super(F2Form, self).__init__(*args, **kwargs)
        self.size.choices = ['1', '1/2', '1/4']
        self.material_tool.choices = ['']
        self.material_plane.choices = ['']
        self.material_interaction.choices = ['']
