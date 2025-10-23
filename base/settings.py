# -*- coding: utf-8 -*-
"""

"""
import os
import sys

from base.utils.common import load_json

basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'


class Operations:
    CONFIRM = 'confirm'
    RESET_PASSWORD = 'reset-password'
    CHANGE_EMAIL = 'change-email'


class BaseConfig:
    STATIC_PATH = os.path.join(basedir, 'base', 'static')
    if os.getenv('FILE_PATH') is not None:
        FILE_PATH = os.getenv('FILE_PATH')
    else:
        FILE_PATH = os.path.join(basedir, 'files')
    UPLOAD_PATH = os.path.join(FILE_PATH, 'uploads')
    UPLOAD_IMG_PATH = os.path.join(FILE_PATH, 'uploads', 'imgs')
    ABAQUS_PATH = os.path.join(FILE_PATH, 'abaqus')
    ABAQUS_POST_PATH = os.path.join(FILE_PATH, 'abaqus_post')
    ABAQUS_TEMPLATE_PATH = os.path.join(FILE_PATH, 'abaqus_template')
    ABAQUS_PRE_PATH = os.path.join(FILE_PATH, 'abaqus_pre')
    ABAQUS_INP_PATH = os.path.join(FILE_PATH, 'abaqus_inp')
    FLOW_PATH = os.path.join(FILE_PATH, 'flow')
    MATERIAL_PATH = os.path.join(FILE_PATH, 'material')
    VIRTUAL_PATH = os.path.join(FILE_PATH, 'virtual')
    EXPERIMENT_PATH = os.path.join(FILE_PATH, 'experiment')
    OPTIMIZE_PATH = os.path.join(FILE_PATH, 'optimize')
    OPTIMIZE_TEMPLATE_PATH = os.path.join(FILE_PATH, 'optimize_template')
    QUEUE_PATH = os.path.join(FILE_PATH, 'queue')
    EVENTS_NEW = os.path.join(FILE_PATH, 'queue', '.events_new')
    DOC_PATH = os.path.join(FILE_PATH, 'doc')
    SHEET_PATH = os.path.join(FILE_PATH, 'sheet')
    PACKING_PATH = os.path.join(FILE_PATH, 'packing')
    PACKING_MODELS_PATH = os.path.join(FILE_PATH, 'packing', 'models')
    PYFEM_PATH = os.path.join(FILE_PATH, 'pyfem')
    PYFEM_PROC_DICT = {}
    OPTIMIZE_PROC_DICT = {}

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')

    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'sunjingyu@imech.ac.cn')
    BASE_MAIL_SUBJECT_PREFIX = '[Base]'
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = ('Base Admin', MAIL_USERNAME)

    IS_WIN = WIN
    WTF_I18N_ENABLED = False

    if os.getenv('HOST_PORT') is None:
        HOST_PORT = 0
    else:
        HOST_PORT = os.getenv('HOST_PORT')

    if os.getenv('JUPYTER_PORT') is None:
        JUPYTER_PORT = 0
    else:
        JUPYTER_PORT = os.getenv('JUPYTER_PORT')

    if os.getenv('CLIENT') is None:
        CLIENT = False
    elif os.getenv('CLIENT') == 'True':
        CLIENT = True
    else:
        CLIENT = False

    if os.getenv('SYNC') is None:
        SYNC = False
    elif os.getenv('SYNC') == 'True':
        SYNC = True
    else:
        SYNC = False

    if os.getenv('CDN') is None:
        CDN = False
    elif os.getenv('CDN') == 'True':
        CDN = True
    else:
        CDN = False

    if os.getenv('NODE') is None:
        NODE = -1
    else:
        NODE = os.getenv('NODE')


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = prefix + os.path.join(basedir, 'data.db')
    REDIS_URL = "redis://localhost"


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'  # in-memory database


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', prefix + os.path.join(basedir, 'data.db'))


class ClientConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = prefix + os.path.join(basedir, 'data.db')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'client': ClientConfig,
}

DEFAULT_CONF_FILE = os.path.join(basedir, '.conf_default')
USER_CONF_FILE = os.path.join(basedir, '.conf_user')

if os.path.exists(USER_CONF_FILE):
    message = load_json(USER_CONF_FILE)
else:
    message = load_json(DEFAULT_CONF_FILE)

ABAQUS = message['ABAQUS']
ABAQUS_FORTRAN = message['ABAQUS_FORTRAN']
MAX_CPUS = int(message['MAX_CPUS'])
