from flask import render_template, redirect, url_for, flash, request, session, jsonify, g
from flask_login import login_user, logout_user, login_required, current_user, fresh_login_required
from . import diagnostics
from app import celery
import random, time
import signal
from billiard.exceptions import Terminated



@diagnostics.route('/historic')
def historic():
    machines = ["Virtual Machine","Henri's Unit"]
    return render_template('/diagnostics/index3.html',machines=machines)

@diagnostics.route('/start', methods=['POST'])
def machine_scanner_start():
    if request.get_json()['action']=='Connect':
        print("[FLASK] Starting LiveView Scanner on serial no: %s" % request.get_json()['serial'])
        task = machine_scanner_task.apply_async(args=[request.get_json()['serial']])
        session['livetaskid'] = task.id
        print("[FLASK] Celery process ID is %s" % task.id)
        return jsonify({}), 202, {'Location': url_for('diagnostics.machine_scanner',task_id=task.id)}
    elif request.get_json()['action']=='Disconnect':
        print("[FLASK] Stopping LiveView Scanner on serial no: %s" % request.get_json()['serial'])
        print("[FLASK] Trying to terminate celery task with ID %s" % session['livetaskid'])
        # scanner = machine_scanner_task.AsyncResult(session['livetaskid'])
        celery.control.revoke(session['livetaskid'],terminate=True, signal=signal.SIGINT)
        return jsonify({}), 204, {'Location': 'Done'}


@diagnostics.route('/monitor/<task_id>')
def machine_scanner(task_id):
    print("In machine scanner!")
    task = machine_scanner_task.AsyncResult(task_id)
    print("Task ID state is %s" % task.state)
    if task.state == 'PENDING':
        #Job did not start yet
        response = {
            'state': task.state,
            'current':0,
            'total':1,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'current': task.info.get('current',0),
            'total': task.info.get('total',1),
            'status': task.info.get('status','')
        }
        if 'result' in task.info:
            response['result'] = task.info['result']
    else:
        #Something went wrong
        response = {
            'state': task.state,
            'current': 1,
            'total': 1,
            'status': str(task.info)
        }
    return jsonify(response)


@celery.task(bind=True, throws=(Terminated,))
def machine_scanner_task(self,machine_id):
    """Background task that determines the state of a machine and returns it to the user"""
    kill = False

    def handler(signum, frame):
        print('Caught', signum)
        print('Trying to terminate!!!')
        nonlocal kill
        print('Current state of kill is %s' % kill)
        kill = True
        print('State of kill after change is %s' % kill)
    signal.signal(signal.SIGINT, handler)
    print("[Machine Scanner Celery Task] Machine ID is %s" % machine_id)
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    i = 0
    while not kill:
        i =+ 1
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...|mach {3}|'.format(random.choice(verb),random.choice(adjective),
                                                        random.choice(noun),machine_id)
        self.update_state(state='PROGRESS',meta={'current':1, 'total': 2, 'status':message})
        print("Machine scanner is alive (i = %s" % i)
        time.sleep(1)
        if i>10:
            kill = True
    print("Machine scanner is aborted")
    return {'current':100, 'total':100,'status':'Task Complete','result':42}