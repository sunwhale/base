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
    ADMIN_EMAIL = os.getenv('BASE_ADMIN', 'sunjingyu@imech.ac.cn')
    FILE_PATH = os.path.join(basedir, 'files')
    UPLOAD_PATH = os.path.join(FILE_PATH, 'uploads')
    PROPELLANT_PATH = os.path.join(FILE_PATH, 'propellant')
    PROPELLANT_PACKING_MODEL_PATH = os.path.join(PROPELLANT_PATH, 'packing', 'models')
    PROPELLANT_PACKING_SUBMODEL_PATH = os.path.join(PROPELLANT_PATH, 'packing', 'submodels')
    PROPELLANT_PACKING_MESH_PATH = os.path.join(PROPELLANT_PATH, 'packing', 'meshes')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')


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
