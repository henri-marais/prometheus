from flask import render_template, redirect, url_for, flash, request, session, jsonify, g
from flask_login import login_user, logout_user, login_required, current_user, fresh_login_required
from sqlalchemy import desc, delete
from app import db
from app.models import Machine, Machine_Type, Machine_State,Record
from . import machines
from .forms import RegistrationForm, RemovalForm

@machines.route('/add',methods=['GET','POST'])
@login_required
def add():
    new_machine = RegistrationForm()
    if request.method == 'GET':
        try:
            new_machine.serial_no.data = Machine.query.order_by(desc('serial_no')).first().serial_no+1
        except:
            new_machine.serial_no.data = 1
        new_machine.state.choices = [(s.id,s.state_name) for s in Machine_State.query.order_by('id')]
        new_machine.type.choices = [(t.id, t.type_name) for t in Machine_Type.query.order_by('type_name')]
    if new_machine.is_submitted():
        user_machine = Machine()
        user_machine.name = new_machine.data['name']
        user_machine.location = new_machine.data['location']
        user_machine.serial_no = new_machine.data['serial_no']
        user_machine.state = Machine_State.query.filter_by(id=new_machine.data['state']).one()
        user_machine.type = Machine_Type.query.filter_by(id=new_machine.data['type']).one()
        db.session.add(user_machine)
        db.session.commit()
        flash("Sucessfully added a machine!")
        return redirect(url_for('main.dashboard'))

    return render_template('machines/register.html',form=new_machine)

@machines.route('/remove',methods=['GET','POST'])
@login_required
def remove():
    remove_machine = RemovalForm()
    if request.method == 'GET':
        remove_machine.machine.choices = [(m.id,m.name) for m in Machine.query.filter(Machine.serial_no).all()]
    if remove_machine.is_submitted():
        MOI = Machine.query.filter_by(serial_no=remove_machine.data['machine']).one()
        Record.query.filter_by(machine=MOI).delete()
        Machine.query.filter_by(serial_no=remove_machine.data['machine']).delete()
        db.session.commit()
        flash("Selected machine destroyed!")
        pass
    return render_template('machines/remove.html', form=remove_machine)
