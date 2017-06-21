from prometheus import app
from app import celery, create_app
from flask import current_app
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound
from ..models import Machine,Machine_State,Machine_Type,Record,Packet_Type
import random, time
import signal
from billiard.exceptions import Terminated

@celery.task(bind=True, throws=(Terminated,), task_track_started=True)
def machine_liveView(self,machine_serial_no):
    """Background task that determines the state of a machine and returns it to the user"""
    def handler(signum, frame):
        print('[Machine Scanner Task] Caught', signum)
        print('[Machine Scanner Task] Trying to terminate!!!')
        nonlocal kill
        print('[Machine Scanner Task] Current state of kill is %s' % kill)
        kill = True
        print('[Machine Scanner Task] State of kill after change is %s' % kill)

    signal.signal(signal.SIGINT, handler)
    print("[Machine Scanner Task] Machine serial no is %s" % machine_serial_no)

    kill = False

    import os
    from app import celery, create_app

    #This seems to be a quirk of running Celery on Windows
    import os
    if os.name=='nt':
        app = create_app(os.getenv('FLASK_CONFIG') or 'default')
        app.app_context().push()

    while not kill:
        uri = current_app.config['SQLALCHEMY_DATABASE_URI']
        con = sqlalchemy.create_engine(uri)
        Session = sessionmaker(bind=con)
        session = Session()
        my_machine = session.query(Machine).filter_by(serial_no=machine_serial_no).one()
        print("[Machine Scanner Task] Now connected to %s" % my_machine)
        new_records = session.query(Record).filter_by(machine = my_machine)\
            .filter(Record.packet_timestamp > my_machine.last_update).all()
        if len(new_records) > 0:
            print("[Machine Scanner Task] New records found (# %s)" % len(new_records))
            for record in new_records:
                print("[Machine Scanner Task] Processing a %s record" % record.packet_type.packet_name)
                print('[Machine Scanner Task] Current machine.state is %s' % my_machine.state.state_name)
                try:
                    #determine the state of the machine based on the current packet
                    machine_state_in_packet = session.query(Machine_State).filter_by(state_name=record.packet_type.packet_name).one()
                    if ((my_machine.state.state_name != 'Stopped') and \
                                (my_machine.state.state_name != 'Error')):
                        print("[Machine Scanner Task] Updating the running time of te machine")
                        my_machine.running_time += record.packet_timestamp-my_machine.last_update
                        print("[Machine Scanner Task] Maching runnign time now %s" % my_machine.running_time)
                    my_machine.last_update = record.packet_timestamp
                    my_machine.state = machine_state_in_packet
                    if (my_machine.state.state_name == "Shutdown"):
                        #once the shutdown packet has been processed, update machine cycles and change state to stopped
                        my_machine.state = session.query(Machine_State).filter_by(state_name="Stopped").one()
                        my_machine.cycles += 1
                    session.commit()
                    print('[Machine Scanner Task] Machine state updated to %s' % my_machine.state.state_name)
                except NoResultFound or MultipleResultsFound:
                    print("[Machine Scanner Task] Packet does not induce a machine state change")
                    print("[Machine Scanner Task] Updating machine timestamp to %s" % record.packet_timestamp)
                    my_machine.last_update = record.packet_timestamp
                    if my_machine.state == session.query(Machine_State).filter_by(state_name="Offline").one():
                        print('[Machine Scanner Task] DX is Online. Changing machine state to "Stopped"')
                        my_machine.state = session.query(Machine_State).filter_by(state_name="Stopped").one()
                    session.commit()

        else:
            print("No new records found. Sleeping for 1s")
        self.update_state(state='RUNNING', meta={'current': 4.5})
        time.sleep(1)
        session.close()
    return False


# self.update_state(state='PROGRESS',meta={'current': i, 'total': total,'status': message})