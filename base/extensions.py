# -*- coding: utf-8 -*-
"""

"""

from flask_bootstrap import Bootstrap4
from flask_login import LoginManager, AnonymousUserMixin
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flask_moment import Moment

bootstrap = Bootstrap4()
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
moment = Moment()


@login_manager.user_loader
def load_user(user_id):
    from base.models import User
    user = User.query.get(int(user_id))
    return user


login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'warning'

login_manager.refresh_view = 'auth.re_authenticate'
login_manager.needs_refresh_message_category = 'warning'


class Guest(AnonymousUserMixin):

    def can(self, permission_name):
        return False

    @property
    def is_admin(self):
        return False


login_manager.anonymous_user = Guest
