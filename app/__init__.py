from flask import Flask
from .extensions import bootstrap,db,mail,loginmanager,moment
from config import config, Config
from celery import Celery

celery = Celery()

def register_extensions(app):
    bootstrap.init_app(app)
    db.init_app(app)
    loginmanager.init_app(app)
    moment.init_app(app)
    mail.init_app(app)
    celery.conf.update(app.config)

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)

    register_extensions(app)
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    from .diagnostics import diagnostics as diagnostics_blueprint
    app.register_blueprint(diagnostics_blueprint, url_prefix='/diagx')

    return app

