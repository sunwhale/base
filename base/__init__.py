# -*- coding: utf-8 -*-
"""

"""
import os

import click
from flask import Flask, render_template
from flask_login import current_user
from flask_wtf.csrf import CSRFError

from base.blueprints.main import main_bp
from base.blueprints.propellant import propellant_bp
from base.blueprints.auth import auth_bp
from base.blueprints.admin import admin_bp
from base.extensions import bootstrap, db, login_manager, csrf
from base.models import Role, User, Permission
from base.settings import config


def create_app(config_name=None):
    if config_name is None:
        config_name = os.getenv('FLASK_CONFIG', 'development')

    app = Flask('base')

    app.config.from_object(config[config_name])

    register_extensions(app)
    register_blueprints(app)
    register_commands(app)
    register_errorhandlers(app)
    register_shell_context(app)
    register_template_context(app)

    return app


def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pass


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(propellant_bp, url_prefix='/propellant')
    app.register_blueprint(admin_bp, url_prefix='/admin')


def register_errorhandlers(app):
    pass


def register_shell_context(app):
    pass


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        env = {'service': 'client'}
        return dict(env=env)


def register_commands(app):
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Create after drop.')
    def initdb(drop):
        """Initialize the database."""
        if drop:
            click.confirm('This operation will delete the database, do you want to continue?', abort=True)
            db.drop_all()
            click.echo('Drop tables.')
        db.create_all()
        click.echo('Initialized database.')

    @app.cli.command()
    def init():
        """Initialize data."""
        click.echo('Initializing the database...')
        db.create_all()

        click.echo('Initializing the roles and permissions...')
        Role.init_role()

        click.echo('Done.')
