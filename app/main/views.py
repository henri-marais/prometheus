from flask import render_template, session, redirect, url_for, current_app
from datetime import datetime
from . import main
from flask_login import login_required, current_user


@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'),302)
    else:
        return render_template('index.html', current_time = datetime.utcnow())

@main.route('/dashboard')
@login_required
def dashboard():
    machine_config = {'menu':True}
    return render_template('dashboard.html', current_time = session.get('login_time'), machine=machine_config)
