# -*- coding: utf-8 -*-
"""

"""
from wtforms import StringField, SelectField, BooleanField, SubmitField
from wtforms import ValidationError
from wtforms.validators import DataRequired, Length, Email

from base.forms.user import EditProfileForm
from base.models import User, Role


class EditProfileAdminForm(EditProfileForm):
    email = StringField('邮箱/Email', validators=[DataRequired(), Length(1, 254), Email()])
    role = SelectField('用户组/Role', coerce=int)
    active = BooleanField('激活/Active')
    confirmed = BooleanField('确认/Confirmed')
    submit = SubmitField('提交/Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('该用户名已经存在。/The username is already in use.')

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data.lower()).first():
            raise ValidationError('该邮箱已经存在。/The email is already in use.')
