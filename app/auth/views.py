from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from . import auth
from ..models import User
from .forms import LoginForm

@auth.route('/login', methods=['GET','POST'])
def login():
    newLoginForm = LoginForm()
    if newLoginForm.validate_on_submit():
        user = User.query.filter_by(email=newLoginForm.email.data).first()
        if user is not None and user.verify_password(newLoginForm.password.data):
            login_user(user,newLoginForm.remember_me.data)
            flash('Thanks for signing in %s' % user.name)
            return redirect(request.args.get('next') or url_for('main.dashboard'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=newLoginForm)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))