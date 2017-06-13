from flask import render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user, fresh_login_required
from . import diagnostics
from app import celery
import random, time

@diagnostics.route('/historic')
def historic():
    return render_template('/diagnostics/index.html')

@diagnostics.route('/start', methods=['POST'])
def machine_scanner_start():
    task = machine_scanner_task.apply_async(args=['27'])
    return jsonify({}), 202, {'Location': url_for('diagnostics.machine_scanner_monitor',task_id=task.id)}

@diagnostics.route('/monitor/<task_id>')
def machine_scanner_monitor(task_id):
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


@celery.task(bind=True)
def machine_scanner_task(self,machine_id):
    """Background task that determines the state of a machine and returns it to the user"""
    verb = ['Starting up', 'Booting', 'Repairing', 'Loading', 'Checking']
    adjective = ['master', 'radiant', 'silent', 'harmonic', 'fast']
    noun = ['solar array', 'particle reshaper', 'cosmic ray', 'orbiter', 'bit']
    message = ''
    total = random.randint(10,50)
    for i in range(total):
        if not message or random.random() < 0.25:
            message = '{0} {1} {2}...|mach {3}|'.format(random.choice(verb),random.choice(adjective),
                                                        random.choice(noun),machine_id)
        self.update_state(state='PROGRESS',meta={'current':i, 'total': total, 'status':message})
        time.sleep(1)
    return {'current':100, 'total':100,'status':'Task Complete','result':42}