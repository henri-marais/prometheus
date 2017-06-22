from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Interval, Numeric
from sqlalchemy.orm import relationship,backref
from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, timedelta
import time
import os
basedir = os.path.abspath(os.path.dirname(__file__))

Base = declarative_base()

class Machine_Type(Base):
    __tablename__ = 'machine_types'
    id = Column(Integer, primary_key=True)
    type_name = Column(String(50))
    machines = relationship('Machine', backref=backref('type',lazy='immediate'))
    def __repr__(self):
        return '<Machine type {%s} with id {%s})' % (self.name, self.id)

class Machine_State(Base):
    __tablename__ = 'machine_states'
    id = Column(Integer, primary_key=True)
    state_name = Column(String(30))
    machines = relationship('Machine', backref=backref('state',lazy='joined'))

    def __repr__(self):
        return '<Machine state with id=%s is %s>' % (self.id, self.state_name)

class Packet_Type(Base):
    __tablename__ = 'packet_types'
    id = Column(Integer, primary_key=True)
    packet_name = Column(String, nullable=False)
    packet_id = Column(Integer, unique=True, nullable=False)
    records = relationship('Record', backref=backref('packet_type', lazy='joined'))

    def __repr__(self):
        return '%s_packet' % self.packet_name

class Record(Base):
    __tablename__ = 'records'
    id = Column(Integer, primary_key=True)
    server_timestamp = Column(DateTime, default = datetime.utcnow)
    packet_timestamp = Column(DateTime, nullable=False)
    packet_id = Column(Integer, ForeignKey('packet_types.id'))
    packet_data = Column(Numeric)
    serial_no = Column(Integer, ForeignKey('machines.serial_no'))

    def __repr__(self):
        return 'Record no %s - %s, %s, from %s' % (self.id, str(self.packet_timestamp), self.packet_type, self.machine)

class Machine(Base):
    __tablename__ = 'machines'
    id = Column(Integer, primary_key=True)
    serial_no = Column(Integer, nullable=False, unique=True)
    location = Column(String(128))
    name = Column(String(256))
    date_commisioned = Column(DateTime, default=datetime.utcnow)
    type_id = Column(Integer, ForeignKey('machine_types.id'))

    # type = relationship("Machine_Type", backref=backref('types', uselist=True))
    state_id = Column(Integer, ForeignKey('machine_states.id'))
    # state = relationship(Machine_State, backref=backref('states', uselist=True))

    records = relationship("Record", backref=backref("machine",lazy='joined'))

    cycles = Column(Integer, default=0)
    running_time = Column(Interval, default=timedelta(0))
    last_update = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return '<%s, has been running for %s (%s cycles)>. Currently: %s. Last update %s' % (self.name,
                                                                                             self.running_time,
                                                                                             self.cycles,
                                                                                             self.state.state_name,
                                                                                             self.last_update)

def connect_db(database_location):
    from sqlalchemy import create_engine
    if database_location == '':
        print("Test DB constructed at: " + 'sqlite:///' + os.path.join(basedir, 'data.sqlite'))
        engine = create_engine('sqlite:///' + os.path.join(basedir, 'data.sqlite'))
        from sqlalchemy.orm import sessionmaker
        session = sessionmaker()
        session.configure(bind=engine)
        Base.metadata.drop_all(engine)
        Base.metadata.create_all(engine)
    else:
        print("Connecting to existing DB at: %s" % database_location)
        engine = create_engine(database_location)
        from sqlalchemy.orm import sessionmaker
        session = sessionmaker()
        session.configure(bind=engine)
    return session()

def build_db(db):
    #make a new DB session
    machine_1 = Machine_Type(type_name='Cake Mixer')
    machine_2 = Machine_Type(type_name='Oven')
    db.add(machine_1)
    db.add(machine_2)
    #define the relevant machine states - should be as generic as possible
    machine_state_stopped = Machine_State(state_name='Stopped')
    machine_state_starting = Machine_State(state_name='Starting')
    machine_state_started = Machine_State(state_name='Started')
    machine_state_running = Machine_State(state_name='Running')
    machine_state_shutdown = Machine_State(state_name='Shutdown')
    machine_state_error = Machine_State(state_name='Error')
    machine_state_offline = Machine_State(state_name='Offline')
    #add the machine states into the database
    packet_starting = Packet_Type(packet_name='Starting',packet_id=0x01)
    packet_started  = Packet_Type(packet_name='Started',packet_id=0x02)
    packet_running  = Packet_Type(packet_name='Running',packet_id=0x03)
    packet_shutdown = Packet_Type(packet_name='Shutdown', packet_id=0x04)
    packet_heartbeat = Packet_Type(packet_name='Heartbeat',packet_id=0x05)

    db.add(machine_state_stopped)
    db.add(machine_state_starting)
    db.add(machine_state_started)
    db.add(machine_state_running)
    db.add(machine_state_shutdown)
    db.add(machine_state_error)
    db.add(machine_state_offline)
    db.commit()

    # sample_mixer = Machine(serial_no=1,location='Cyberspace',name='Virtual Mixer 1',date_commisioned=datetime.utcnow(),
    #                        cycles=0, running_time=timedelta(0),type=machine_1, state=machine_state_stopped)
    # sample_mixer2 = Machine(serial_no=3,location='Cyberspace',name='Virtual Mixer 2',date_commisioned=datetime.utcnow(),
    #                        cycles=0, running_time=timedelta(0),type=machine_1, state=machine_state_started)
    # sample_mixer3 = Machine(serial_no=4,location='Cyberspace',name='Virtual Mixer 3',date_commisioned=datetime.utcnow(),
    #                        cycles=0, running_time=timedelta(0),type=machine_1, state=machine_state_offline)
    #
    # sample_oven = Machine(serial_no=2,location='Cyberspace',name='Virtual Oven',date_commisioned=datetime.utcnow(),
    #                        cycles=0, running_time=timedelta(0),type=machine_2, state=machine_state_stopped)
    #
    # db.add_all([sample_mixer, sample_oven, sample_mixer2, sample_mixer3])
    # db.commit()



    db.add_all([packet_starting, packet_started, packet_running, packet_shutdown, packet_heartbeat])
    db.commit()
    db.close()
    # rec_starting = Record(packet_timestamp = datetime.utcnow(), packet_type=packet_starting, machine=sample_mixer)
    # time.sleep(0.1)
    # rec_started  = Record(packet_timestamp = datetime.utcnow(), packet_type=packet_started, machine=sample_mixer)
    # time.sleep(0.1)
    # rec_run_1   = Record(packet_timestamp= datetime.utcnow(), packet_type=packet_running, machine=sample_mixer)
    # time.sleep(2)
    # rec_run_2   = Record(packet_timestamp= datetime.utcnow(), packet_type=packet_running, machine=sample_mixer)
    # time.sleep(2)
    # rec_stop    = Record(packet_timestamp=datetime.utcnow(), packet_type=packet_shutdown, machine=sample_mixer)
    # db.add_all([rec_starting, rec_started, rec_run_1, rec_run_2, rec_stop])
    # db.commit()

# The following query can be used to retrieve the latest record from the database. There might be loads of issues in
# doing this but let's see how it goes. Maybe server-default timestamping for this purpose is more suited?
# TODO: Critical for the short term. Send packets of data from a CLI to the database thread processor. Theoretically,
# TODO: thread processor and the web app can be completely decoupled. Ideadlly, something like a celery job seems ideal.

# TODO: As it turns out the packet processor is completely decoupled, and there still is a celery taks to handle the
# TODO: analytics aspects of the UX
# sorted_times = db.query(DXrecord).order_by(DXrecord.timestamp.desc()).all()
#
# 