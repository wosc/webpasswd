from ws.webpasswd.update import valid_user
import os
import os.path
import subprocess
import sys


def test_valid_user():
    assert not valid_user('root')
    assert not valid_user('foo[')
    assert valid_user('foo')
    assert valid_user('foo.de')
    assert valid_user('bar1')
    assert valid_user('foo-bar')
    assert valid_user('foo_bar')


def passwd(user, current, new, sudo=True):
    webpasswd_change = os.path.join(
        os.path.dirname(sys.executable), 'webpasswd-change')
    cmd = (webpasswd_change,)
    if user:
        cmd += (user,)
    if sudo:
        cmd = ('sudo',) + cmd
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        stdin=subprocess.PIPE)
    if sys.version_info >= (3,):
        current = current.encode('utf-8')
        new = new.encode('utf-8')
    stdout, stderr = proc.communicate(b'\n'.join([current, new]))
    status = proc.wait()
    if sys.version_info >= (3,):
        stdout = stdout.decode('utf-8')
        stderr = stderr.decode('utf-8')
    return (status, stdout, stderr)


def test_insufficient_arguments_should_fail():
    status, stdout, stderr = passwd('', '', '')
    assert status != 0
    assert 'Usage' in stderr


def test_not_sudo_should_fail():
    status, stdout, stderr = passwd('foo', 'bar', 'baz', sudo=False)
    assert status != 0
    assert 'root' in stderr


def test_nonexistent_user_should_fail():
    status, stdout, stderr = passwd('nonexistent', 'old', 'new')
    assert status != 0
    assert 'Invalid username or password' in stderr


def test_wrong_password_should_fail():
    status, stdout, stderr = passwd('webpasswd', 'wrong', 'new')
    assert status != 0
    assert 'Invalid username or password' in stderr


def test_correct_password():
    print('Please set password for user webpasswd to "asdfasdf"')
    print('sudo passwd webpasswd')
    os.system('sudo passwd webpasswd')

    status, stdout, stderr = passwd('webpasswd', 'asdfasdf', 'qwerqwer')
    assert status == 0
    assert not stdout
    assert not stderr

    status, stdout, stderr = passwd('webpasswd', 'qwerqwer', 'asdfasdf')
    assert status == 0
    assert not stdout
    assert not stderr
