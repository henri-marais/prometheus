from flask import render_template, session, redirect, url_for, current_app
from datetime import datetime
from . import main
from flask_login import login_required


@main.route('/')
def index():
    return render_template('index.html', current_time = datetime.utcnow())

@main.route('/dashboard')
@login_required
def dashboard():
    machine_config = {'menu':False}
    return render_template('dashboard.html', current_time = session.get('login_time'), machine=machine_config)
