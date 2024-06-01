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
import tempfile
import yaml

# Path to config file
config_path = "/etc/webpasswd/config.yml"

# Load config file
try:
    config = yaml.safe_load(open(config_path))
except FileNotFoundError:
    print(f"File {config_path} not found")
    sys.exit(1)

# Configure flask app
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
        if success==0:
            params['flash'] = 'Password successfully changed'
            form.username.data = None
        elif success==1:
            form._fields['current_password'].errors.append(
                'Invalid username or password.')
        else:
            form._fields['current_password'].errors.append(
                'Could not change password.')

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

    # Serialize sensitive arguments in yaml string
    data = {
        'username': username,
        'current': current,
        'new': new
    }
    
    # Create a temporary file to store sensitive arguments
    with tempfile.NamedTemporaryFile(delete=False, mode='wt') as temp_file:
        temp_file_path = temp_file.name
        yaml.dump(data, temp_file)

    # Call webpasswd_change using sudo and pass the path of the temporary file as an argument
    result = subprocess.run(['sudo', webpasswd_change, temp_file_path], capture_output=True, text=True)

    # Remove temporary file
    os.remove(temp_file_path)

    # Return status
    return result.returncode

@app.errorhandler(Exception)
def handle_error(error):
    return str(error), 500


def cgi():
    # We only have the one route
    os.environ['PATH_INFO'] = '/'
    wsgiref.handlers.CGIHandler().run(app.wsgi_app)


def serve():
    # Load parameters from config file
    server = config.get('web')
    port = server.get('port', 8080)
    ip = server.get('ip', '')
    # Start server
    print("Starting webpasswd server, on port", port)
    wsgiref.simple_server.make_server(ip, port, app.wsgi_app).serve_forever()
