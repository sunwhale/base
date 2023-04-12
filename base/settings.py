# -*- coding: utf-8 -*-
"""

"""
import os
import sys

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
    if os.getenv('FILE_PATH') != None:
        FILE_PATH = os.getenv('FILE_PATH')
    else:
        FILE_PATH = os.path.join(basedir, 'files')
    UPLOAD_PATH = os.path.join(FILE_PATH, 'uploads')
    UPLOAD_IMG_PATH = os.path.join(FILE_PATH, 'uploads', 'imgs')
    ABAQUS_PATH = os.path.join(FILE_PATH, 'abaqus')
    ABAQUS_POST_PATH = os.path.join(FILE_PATH, 'abaqus_post')
    ABAQUS_TEMPLATE_PATH = os.path.join(FILE_PATH, 'abaqus_template')
    EXPERIMENT_PATH = os.path.join(FILE_PATH, 'experiment')
    QUEUE_PATH = os.path.join(FILE_PATH, 'queue')
    EVENTS_NEW = os.path.join(FILE_PATH, 'queue', '.events_new')
    DOC_PATH = os.path.join(FILE_PATH, 'doc')
    SHEET_PATH = os.path.join(FILE_PATH, 'sheet')
    PACKING_PATH = os.path.join(FILE_PATH, 'packing')
    PACKING_MODELS_PATH = os.path.join(FILE_PATH, 'packing', 'models')

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

    WTF_I18N_ENABLED = False


class DevelopmentConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = prefix + os.path.join(basedir, 'data.db')
    REDIS_URL = "redis://localhost"
    SERVICE = 'client'
    

class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///'  # in-memory database
    SERVICE = 'client'


class ProductionConfig(BaseConfig):
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', prefix + os.path.join(basedir, 'data.db'))
    SERVICE = 'server'


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
}
