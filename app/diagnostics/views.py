from flask import render_template, redirect, url_for, flash, request, session, jsonify, g
from flask_login import login_user, logout_user, login_required, current_user, fresh_login_required
from . import diagnostics
from app import celery,db
from app.models import Machine, Machine_State, Record, Packet_Type
from sqlalchemy.orm.exc import MultipleResultsFound,NoResultFound
import signal
from .tasks import machine_liveView
from celery.states import PENDING, REVOKED, FAILURE, SUCCESS
from datetime import datetime, timedelta


@diagnostics.route('/dashboard')
@login_required
def dashboard():
    machines = Machine.query.all()
    if len(machines)==0:
        machines = ['No machine configured']
    return render_template('/diagnostics/index3.html',machines=machines)

@login_required
@diagnostics.route('/historic', methods=['POST'])
def historic():
    response ={
        'Cycles':'unknown',
        'Uptime':'nodata',
        'State':'unknown',
        'AvgRunCurrent': 'unknown'
    }
    try:
        update_machine(request.get_json()['serial_no'])
        my_machine = Machine.query.filter_by(serial_no=request.get_json()['serial_no']).first()
        avg_running_current = update_machine_avgCurrent(request.get_json()['serial_no'])
        response['Cycles'] = my_machine.cycles
        response['Uptime'] = pack_time(my_machine.running_time)
        response['State'] = my_machine.state.state_name
        if my_machine.date_commissioned == None:
            response['Commisioned'] = "No data"
        else:
            response['Commisioned'] = (my_machine.date_commissioned).strftime("%Y %b %d at %H:%M")
        if avg_running_current == 0:
            response['AvgRunCurrent'] = "Not yet"
        else:
            response['AvgRunCurrent'] = "{:2.2f} A".format(avg_running_current)
    except:
        pass
    return jsonify(response)

@diagnostics.route('/packet_loader', methods=['POST'])
def packet_loader():
    if request.get_json()['serial_no'] == "1":
        my_machine = Machine.query.filter_by(serial_no=request.get_json()['serial_no']).one()
        this_packet = Packet_Type.query.filter_by(packet_name=request.get_json()['type']).one()
        #Here the UTC server time is adjusted to allow fot naive GTM+2 times
        if 'data' in request.get_json():
            new_record = Record(machine=my_machine, packet_type= this_packet, packet_timestamp= datetime.utcnow()-timedelta(hours=-2)
                            , packet_data= float(request.get_json()['data']))
        else:
            new_record = Record(machine=my_machine, packet_type=this_packet, packet_timestamp=datetime.utcnow()-timedelta(hours=-2))
        db.session.add(new_record)
        db.session.commit()

    return jsonify({}), 200

@diagnostics.route('/start', methods=['POST'])
def machine_scanner_start():
    if request.get_json()['action']=='Connect':
        print("[FLASK] Starting LiveView Scanner on serial no: %s" % request.get_json()['serial'])
        task = machine_liveView.apply_async(args=[request.get_json()['serial']])
        session['livetaskid'] = task.id
        print("[FLASK] Celery process ID is %s" % task.id)
        return jsonify({}), 202, {'Location': url_for('diagnostics.machine_scanner',task_id=task.id)}
    elif request.get_json()['action']=='Disconnect':
        print("[FLASK] Stopping LiveView Scanner on serial no: %s" % request.get_json()['serial'])
        print("[FLASK] Trying to terminate celery task with ID %s" % session['livetaskid'])
        celery.control.revoke(session['livetaskid'],terminate=True, signal=signal.SIGINT)
        return jsonify({}), 204, {'Location': 'Done'}


@diagnostics.route('/monitor/<task_id>')
def machine_scanner(task_id):
    print("Waiting for reply from Celery worker")
    task = machine_liveView.AsyncResult(task_id)
    print("Task ID state is %s" % task.state)
    response = {'worker_state':task.state}
    if task.state == PENDING:
        #Job did not start yet
        response = {
            'state': 'Connecting',
            'worker_state': task.state
        }
    elif task.state == REVOKED:
        response= {'state': 'Offline',
                   'worker_state': task.state}
    elif task.state == SUCCESS:
        response= {'state': 'Offline',
                   'worker_state': task.state}
    elif task.state == 'COMPUTING':
        #This is essentially the normal operating state
        response = {
        'total_run_time': task.info.get('total_run_time'),
        'current_run_time': task.info.get('current_run_time'),
        'cycles': task.info.get('cycles'),
        'motor_current': "{:.5s} A".format(task.info.get('motor_current')),
        'average_current':'',
        'state':task.info.get('state'),
        'worker_state': task.state}
        print(response)
    else:
        #Something went wrong, most likely the worker has crashed
        response = {
            'state': task.state,
            'worker_state': task.state
        }
    return jsonify(response)

def update_machine(serial_no):
    print("[Machine Updater] - Updating the machine")
    my_machine = Machine.query.filter_by(serial_no=serial_no).one()
    try:
        start_packet = Packet_Type.query.filter_by(packet_name="Starting").one()
        start_record = Record.query.filter_by(machine=my_machine).filter_by(packet_type=start_packet).one()
        my_machine.date_commissioned = start_record.packet_timestamp
    except:
        pass

    new_records = Record.query.filter_by(machine=my_machine) \
        .filter(Record.packet_timestamp > my_machine.last_update).all()
    if len(new_records) > 0:
        print("[Machine Updater] - New records found (# %s)" % len(new_records))
        for record in new_records:
            print("[Machine Updater] - Processing a %s record" % record.packet_type.packet_name)
            print('[Machine Updater] - Current machine.state is %s' % my_machine.state.state_name)
            try:
                # determine the state of the machine based on the current packet
                machine_state_in_packet = Machine_State.query.filter_by(
                    state_name=record.packet_type.packet_name).one()
                if ((my_machine.state.state_name != 'Stopped') and \
                            (my_machine.state.state_name != 'Error')):
                    print("[Machine Updater] - Updating the running time of te machine")
                    my_machine.running_time += record.packet_timestamp - my_machine.last_update
                    print("[Machine Updater] - Maching runnign time now %s" % my_machine.running_time)
                my_machine.last_update = record.packet_timestamp
                my_machine.state = machine_state_in_packet
                if (my_machine.state.state_name == "Shutdown"):
                    # once the shutdown packet has been processed, update machine cycles and change state to stopped
                    my_machine.state = Machine_State.query.filter_by(state_name="Stopped").one()
                    my_machine.cycles += 1
                db.session.commit()
                print('[Machine Updater] - Machine state updated to %s' % my_machine.state.state_name)
            except NoResultFound or MultipleResultsFound:
                print("[Machine Updater] - Packet does not induce a machine state change")
                print("[Machine Updater] - Updating machine timestamp to %s" % record.packet_timestamp)
                my_machine.last_update = record.packet_timestamp
                if my_machine.state == Machine_State.query.filter_by(state_name="Offline").one():
                    print('[Machine Updater] - DX is Online. Changing machine state to "Stopped"')
                    my_machine.state = Machine_State.query.filter_by(state_name="Stopped").one()
                db.session.commit()
    else:
        print("[Machine Updater] - No new records found.")

def update_machine_avgCurrent(serial_no):
    print("Calculating average run current")
    my_machine = Machine.query.filter_by(serial_no=serial_no).one()
    running = Packet_Type.query.filter_by(packet_name='Running').one()
    records = Record.query.filter_by(machine= my_machine).filter_by(packet_type=running).all()
    if len(records) > 0:
        total_current = 0
        for record in records:
            total_current += record.packet_data
        avg_current = total_current / len(records)
    else:
        avg_current = 0
    return avg_current

def pack_time(ptime):
    hours = ptime.days*24
    h,s = divmod(ptime.seconds,60*60*24)
    hours = hours+h
    m,s = divmod(s,60)
    uptime = "%04d:%02d:%02d" % (hours, m,s)
    return uptime

