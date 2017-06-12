from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_login import UserMixin
from .extensions import loginmanager

@loginmanager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ : 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128),unique=False)
    email = db.Column(db.String(255), unique=True)
    password_hash = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    registered_at = db.Column(db.DateTime, default= datetime.utcnow(), onupdate=datetime.utcnow())
    confirmed_at = db.Column(db.DateTime())
    role = db.Column(db.Integer,db.ForeignKey('roles.id'))

    @property
    def password(selfs):
        raise AttributeError('Password is not a readable property')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash,password)

    def __repr__(self):
        return '<User: %s (%s)>' % (self.name,self.email)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50),unique=True)
    description = db.Column(db.String(255),unique=False)
    users = db.relationship('User',backref='roles',lazy='dynamic')

    def __repr__(self):
        return '<Role: %s>' % self.name

