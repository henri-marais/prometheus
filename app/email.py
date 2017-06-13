from flask import current_app, render_template
from flask_mail import Message
from . import mail, celery, create_app
from threading import Thread

@celery.task
def send_async_email(msg):
    print("before trying to get the context")
    app = create_app('default')
    with app.app_context():
        print("trying to send mail")
        mail.send(msg)

def send_email(to, subject, template, **kwargs):
    app = current_app._get_current_object()

    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    send_async_email.delay(msg)

def send_async_email_threaded(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email_threaded(to, subject, template, **kwargs):
    app = current_app._get_current_object()
    msg = Message(app.config['MAIL_SUBJECT_PREFIX'] + ' ' + subject,
                  sender=app.config['MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=send_async_email_threaded, args=[app, msg])
    thr.start()
    return thr