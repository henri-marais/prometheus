from prometheus import app
from app import celery, create_app
from flask import current_app
import sqlalchemy
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound,MultipleResultsFound
from ..models import Machine,Machine_State,Machine_Type,Record,Packet_Type
import random, time
import signal
from billiard.exceptions import Terminated
from datetime import datetime, timedelta

@celery.task(bind=True, throws=(Terminated,))
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

    live_data={
        'total_run_time': '',
        'current_run_time': '',
        'cycles': '',
        'motor_current': '',
        'average_current':'',
        'state':''
    }

    def pack_time(ptime):
        hours = ptime.days * 24
        h, s = divmod(ptime.seconds, 60 * 60 * 24)
        hours = hours + h
        m, s = divmod(s, 60)
        uptime = "%04d:%02d:%02d" % (hours, m, s)
        return uptime
    #Before the packet scanner activity starts, make sure that the most recent information is available.
    #Since this is only the live viewer, no changes will be made to the underlying DB. Only loads of queries

    uri = current_app.config['SQLALCHEMY_DATABASE_URI']
    con = sqlalchemy.create_engine(uri)
    Session = sessionmaker(bind=con)
    session = Session()
    my_machine = session.query(Machine).filter_by(serial_no=machine_serial_no).one()

    live_data['cycles'] = my_machine.cycles
    live_data['total_run_time'] = 'unknown'
    live_data['state'] = my_machine.state.state_name
    live_data['current_run_time'] = 'unknown'
    live_timestamp = my_machine.last_update
    live_runtime = timedelta(0)
    live_totaltime = my_machine.running_time

    while not kill:
        print("Getting latest records. Only from %s" % live_timestamp)
        newest = session.query(Record).filter_by(machine= my_machine).filter(desc(Record.packet_timestamp)).one()
        print("Latest record for machine %d stamped as %s" % (newest.serial_no, newest.packet_timestamp))
        
        new_records = session.query(Record).filter_by(machine = my_machine)\
            .filter(Record.packet_timestamp > live_timestamp).all()
        if len(new_records) > 0:
            print("[Machine Scanner Task] %s new records found" % len(new_records))
            for record in new_records:
                print("[Machine Scanner Task] Processing a %s record" % record.packet_type.packet_name)
                print('[Machine Scanner Task] Current machine.state is %s' % live_data['state'])
                try:
                    #determine the state of the machine based on the current packet
                    machine_state_in_packet = session.query(Machine_State).filter_by(state_name=record.packet_type.packet_name).one()
                    if ((live_data['state'] != 'Stopped') and \
                                (live_data['state'] != 'Error')):
                        #update the running time based on packets that can actually induce running time behaviour
                        print("[Machine Scanner Task] Updating the current running time")
                        live_runtime += record.packet_timestamp-live_timestamp
                        print("[Machine Scanner Task] Maching runnign time (current): %s" % live_runtime)
                        print("[Machine Scanner Task] Updating the running time of te machine")
                        live_totaltime += record.packet_timestamp-live_timestamp
                        print("[Machine Scanner Task] Maching runnign time (total): %s" % live_totaltime)
                    live_timestamp = record.packet_timestamp
                    print("Updating the live_timestamp to %s" % machine_state_in_packet.state_name)
                    live_data['state'] = machine_state_in_packet.state_name
                    if live_data['state'] == "Running":
                        live_data['motor_current'] = record.packet_data
                        # print("[Machine Scanner Task] Machine is %s. Updating motor current to")
                    else:
                        live_data['motor_current'] = ''
                    if (live_data['state'] == "Shutdown"):
                        #once the shutdown packet has been processed, update machine cycles and change state to stopped
                        live_data['state'] = session.query(Machine_State).filter_by(state_name="Stopped").one().state_name
                        live_data['cycles'] += 1
                    print('[Machine Scanner Task] Machine state updated to %s' % live_data['state'])
                except NoResultFound or MultipleResultsFound:
                    print("[Machine Scanner Task] Packet does not induce a machine state change")
                    print("[Machine Scanner Task] Updating machine timestamp to %s" % record.packet_timestamp)
                    live_timestamp = record.packet_timestamp
                    if my_machine.state == session.query(Machine_State).filter_by(state_name="Offline").one():
                        print('[Machine Scanner Task] DX is Online. Changing machine state to "Stopped"')
                        my_machine.state = session.query(Machine_State).filter_by(state_name="Stopped").one()
        else:
            print("No new records found for machine %s. Sleeping for 1s" % machine_serial_no)
        live_data['current_run_time'] = pack_time(live_runtime)
        live_data['total_run_time'] = pack_time(live_totaltime)
        # if ((datetime.utcnow()-timedelta(hours=-2))-my_machine.last_update) > timedelta(seconds=30):
        #     live_data['state'] = "Offline"

        self.update_state(state='COMPUTING', meta=live_data)
        # if live_data['state'] == 'Stopped':
        #     live_data['current_run_time'] = timedelta(0)
        time.sleep(1)
        session.close()
    return False

