from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user, fresh_login_required
from . import auth
from ..email import send_email
from ..models import User
from .forms import LoginForm, RegistrationForm
from ..extensions import db
from datetime import datetime

@auth.route('/login', methods=['GET','POST'])
def login():
    newLoginForm = LoginForm()
    if newLoginForm.validate_on_submit():
        user = User.query.filter_by(email=newLoginForm.email.data).first()
        if user is not None and user.verify_password(newLoginForm.password.data):
            login_user(user,newLoginForm.remember_me.data)
            flash('Thanks for signing in %s' % user.name)
            session['login_time'] = datetime.utcnow()
            return redirect(request.args.get('next') or url_for('main.dashboard'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=newLoginForm)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))

@auth.route('/register', methods=['GET','POST'])
@login_required
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(name=form.name.data, email=form.email.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email,'Confirm your account','auth/email/confirm',user=user,token=token)
        flash('New user %s added to the userbase!. Please check your email.' % user.name)
        return redirect(url_for('main.dashboard'))
    return render_template('auth/register.html', form=form)

@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.dashboard'))
    if current_user.confirm(token):
        flash('Your account has been confirmed. Thanks!')
        return redirect(url_for('main.dashboard'))
    else:
        flash('The confirmation link is invalid, or has expired!')
        return redirect(url_for('main.index'))
