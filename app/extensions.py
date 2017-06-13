from flask_sqlalchemy import SQLAlchemy
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_login import LoginManager
from flask_moment import Moment

db = SQLAlchemy()
bootstrap = Bootstrap()
mail = Mail()
loginmanager = LoginManager()
loginmanager.session_protection = 'strong'
loginmanager.login_view = 'auth.login'
moment = Moment()
