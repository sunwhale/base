# -*- coding: utf-8 -*-
"""

"""
import os

import click
from flask import Flask, render_template
from flask_wtf.csrf import CSRFError

from base.blueprints.auth import auth_bp
from base.blueprints.admin import admin_bp
from base.blueprints.doc import doc_bp
from base.blueprints.sheet import sheet_bp
from base.blueprints.main import main_bp
from base.blueprints.propellant import propellant_bp
from base.extensions import bootstrap, db, login_manager
from base.models import Role
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


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(doc_bp, url_prefix='/doc')
    app.register_blueprint(propellant_bp, url_prefix='/propellant')
    app.register_blueprint(sheet_bp, url_prefix='/sheet')


def register_errorhandlers(app):
    @app.errorhandler(400)
    def bad_request(e):
        return render_template('errors/400.html'), 400

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        return render_template('errors/413.html'), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        return render_template('errors/400.html', description=e.description), 500


def register_shell_context(app):
    pass


def register_template_context(app):
    @app.context_processor
    def make_template_context():
        if app.config['SERVICE'] == 'client':
            env = {'service': 'client'}
        else:
            env = {'service': 'server'}
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
