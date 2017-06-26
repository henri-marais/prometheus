from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from flask_login import UserMixin
from .extensions import loginmanager
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app

@loginmanager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128),unique=False)
    email = db.Column(db.String(255), unique=True)
    password_hash = db.Column(db.String(255))
    active = db.Column(db.Boolean)
    registered_at = db.Column(db.DateTime, default= datetime.utcnow())
    confirmed_at = db.Column(db.DateTime)
    confirmed = db.Column(db.Boolean, default=False)
    role_id = db.Column(db.Integer,db.ForeignKey('roles.id'))

    @property
    def password(selfs):
        raise AttributeError('Password is not a readable property')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash,password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'],expiration)
        return s.dumps({'confirm':self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        self.confirmed_at = datetime.utcnow()
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User: %s (%s)>' % (self.name,self.email)

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50),unique=True)
    description = db.Column(db.String(255),unique=False)
    users = db.relationship('User',backref='role',lazy='dynamic')

    def __repr__(self):
        return '<Role: %s>' % self.name

class Machine_Type(db.Model):
    __tablename__ = 'machine_types'
    id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.String(50))
    machines = db.relationship('Machine', backref=db.backref('type',lazy='immediate'))
    def __repr__(self):
        return '<Machine type {%s} with id {%s})' % (self.name, self.id)

class Machine_State(db.Model):
    __tablename__ = 'machine_states'
    id = db.Column(db.Integer, primary_key=True)
    state_name = db.Column(db.String(30))
    machines = db.relationship('Machine', backref=db.backref('state',lazy='joined'))

    def __repr__(self):
        return '<Machine state with id=%s is %s>' % (self.id, self.state_name)

class Packet_Type(db.Model):
    __tablename__ = 'packet_types'
    id = db.Column(db.Integer, primary_key=True)
    packet_name = db.Column(db.String, nullable=False)
    packet_id = db.Column(db.Integer, unique=True, nullable=False)
    records = db.relationship('Record', backref=db.backref('packet_type', lazy='joined'))

    def __repr__(self):
        return '%s_packet' % self.packet_name

class Record(db.Model):
    __tablename__ = 'records'
    id = db.Column(db.Integer, primary_key=True)
    server_timestamp = db.Column(db.DateTime, default = datetime.utcnow)
    packet_timestamp = db.Column(db.DateTime, nullable=False)
    packet_id = db.Column(db.Integer, db.ForeignKey('packet_types.id'))
    packet_data = db.Column(db.Numeric)
    serial_no = db.Column(db.Integer, db.ForeignKey('machines.serial_no'))

    def __repr__(self):
        return 'Record no %s - %s, %s, from %s' % (self.id, str(self.packet_timestamp), self.packet_type, self.machine)

class Machine(db.Model):
    __tablename__ = 'machines'
    id = db.Column(db.Integer, primary_key=True)
    serial_no = db.Column(db.Integer, nullable=False, unique=True)
    location = db.Column(db.String(128))
    name = db.Column(db.String(256))
    date_commisioned = db.Column(db.DateTime)
    type_id = db.Column(db.Integer, db.ForeignKey('machine_types.id'))
    #type field backref'ed

    state_id = db.Column(db.Integer, db.ForeignKey('machine_states.id'))
    #state field backref'ed

    records = db.relationship("Record", backref=db.backref("machine",lazy='joined'))

    cycles = db.Column(db.Integer, default=0)
    running_time = db.Column(db.Interval, default=timedelta(0))
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<%s, has been running for %s (%s cycles)>. Currently: %s' % (self.name, self.running_time, self.cycles, self.state.state_name)

def db_default():

    if len(Machine_Type.query.all()) == 0:
        print("No machine types exist. Building defailts")
        machine_mixer = Machine_Type(type_name='Cake Mixer')
        machine_oven = Machine_Type(type_name='Oven')
        db.session.add_all([machine_mixer,machine_oven])
        db.session.commit()
    else:
        print("Machine types already defined!")

    if len(Machine_State.query.all()) == 0:
        print("No machine states exist. Building default table")
        machine_state_stopped = Machine_State(state_name='Stopped')
        machine_state_starting = Machine_State(state_name='Starting')
        machine_state_started = Machine_State(state_name='Started')
        machine_state_running = Machine_State(state_name='Running')
        machine_state_shutdown = Machine_State(state_name='Shutdown')
        machine_state_error = Machine_State(state_name='Error')
        machine_state_offline = Machine_State(state_name='Offline')
        db.session.add_all([machine_state_offline,machine_state_started,machine_state_stopped,machine_state_starting,
                        machine_state_running,machine_state_shutdown,machine_state_error])
        db.session.commit()
    else:
        print("Machine states already defined!")

    if len(Packet_Type.query.all()) == 0:
        print("No packet types exist. Building default table")
        packet_starting = Packet_Type(packet_name='Starting',packet_id=0x01)
        packet_started  = Packet_Type(packet_name='Started',packet_id=0x02)
        packet_running  = Packet_Type(packet_name='Running',packet_id=0x03)
        packet_shutdown = Packet_Type(packet_name='Shutdown', packet_id=0x04)
        packet_heartbeat = Packet_Type(packet_name='Heartbeat',packet_id=0x05)
        db.session.add_all([packet_starting, packet_started, packet_running, packet_shutdown, packet_heartbeat])
        db.session.commit()
    else:
        print("Packet types already defined!")

    if len(Role.query.all()) == 0:
        print("No user roles exist. Defining the admin role")
        admin_role = Role(name='admin',description='Administrative user for the entire site')
        db.session.add(admin_role)
        db.session.commit()
    else:
        print("Some user roles already exist")

    if len(User.query.all()) == 0:
        print("No users defined, building a default user")
        admin_user = User(name='Henri Marais',email='henri.marais@gmail.com',password='henri',active=True,
                      confirmed=True, confirmed_at=datetime.utcnow(),role=admin_role)
        db.session.add(admin_user)
        db.session.commit()
    else:
        print("Default admin user already defined")

    if len(Machine.query.all()) == 0:
        print("No machines exist. Building a sample machine")
        mixer = Machine_Type.query.filter_by(type_name='Cake Mixer').one()
        offline = Machine_State.query.filter_by(state_name='Offline').one()
        sample_machine = Machine(serial_no=1,location="Cyberspace",name="Virtual Mixer",state=offline,
                                 type=mixer)
        db.session.add(sample_machine)
        db.session.commit()
    else:
        print("Sample machine already exists!")

