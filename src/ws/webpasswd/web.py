from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, EqualTo
import flask
import os
import os.path
import socket
import subprocess
import sys
import wsgiref.handlers
import wsgiref.simple_server


app = flask.Flask(__name__)
# We don't have any state, so we're not vulnerable to CSRF
app.config['WTF_CSRF_ENABLED'] = False


@app.route('/', methods=('GET', 'POST'))
def passwd_view():
    form = Form()
    params = {
        'form': form,
        'flash': None,
        'hostname': socket.getfqdn(),
        'stylesheet': os.environ.get('WEBPASSWD_STYLESHEET'),
    }
    if form.validate_on_submit():
        success = changepasswd(
            form.username.data,
            form.current_password.data, form.new_password.data)
        if success:
            params['flash'] = 'Password successfully changed'
            form.username.data = None
        else:
            form.errors['current_password'] = ['Invalid username or password.']
    return flask.render_template('form.html', **params)


class Form(FlaskForm):

    username = StringField('Username', validators=[DataRequired()])
    current_password = PasswordField(
        'Current Password', validators=[DataRequired()])
    new_password = PasswordField(
        'New Password', validators=[
            DataRequired(),
            EqualTo('confirm', message='Does not match confirm')])
    confirm = PasswordField('Confirm', validators=[DataRequired()])


def changepasswd(username, current, new):
    webpasswd_change = os.environ.get('WEBPASSWD_CHANGE')
    if not webpasswd_change:
        webpasswd_change = os.path.join(
            os.path.dirname(sys.executable), 'webpasswd-change')
    proc = subprocess.Popen(
        ['sudo', webpasswd_change, username, current, new],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    status = proc.wait()
    return status == 0


@app.errorhandler(Exception)
def handle_error(error):
    return str(error), 500


def cgi():
    # We only have the one route
    os.environ['PATH_INFO'] = '/'
    wsgiref.handlers.CGIHandler().run(app.wsgi_app)


def serve():
    wsgiref.simple_server.make_server('', 8080, app.wsgi_app).serve_forever()
