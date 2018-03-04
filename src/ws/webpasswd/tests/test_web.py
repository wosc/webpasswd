import mock
import os
import pytest
import tempfile
import ws.webpasswd.web


def test_username_and_password_is_required():
    b = ws.webpasswd.web.app.test_client()
    r = b.post('/', data={})
    assert 'Username: This field is required' in r.data.decode('utf-8')
    assert 'Current Password: This field is required' in r.data.decode('utf-8')


def test_confirmation_must_match():
    b = ws.webpasswd.web.app.test_client()
    r = b.post('/', data={
        'username': 'myuser', 'current_password': 'current',
        'new_password': 'foo', 'confirm': 'bar'})
    assert 'New Password: Does not match confirm' in r.data.decode('utf-8')


def test_repopulates_username_on_error():
    b = ws.webpasswd.web.app.test_client()
    r = b.post('/', data={'username': 'myuser'})
    assert 'value="myuser"' in r.data.decode('utf-8')


def test_zero_exitcode_should_display_success():
    b = ws.webpasswd.web.app.test_client()
    with mock.patch('subprocess.Popen') as change:
        change().wait.return_value = 0
        r = b.post('/', data={
            'username': 'myuser', 'current_password': 'current',
            'new_password': 'new', 'confirm': 'new'})
    assert 'Password successfully changed' in r.data.decode('utf-8')


def test_nonzero_exitcode_should_display_error():
    b = ws.webpasswd.web.app.test_client()
    with mock.patch('subprocess.Popen') as change:
        change().wait.return_value = 1
        r = b.post('/', data={
            'username': 'myuser', 'current_password': 'current',
            'new_password': 'new', 'confirm': 'new'})
    assert 'Invalid username or password' in r.data.decode('utf-8')


@pytest.mark.parametrize(
    'exploit', ['foo; touch %s', 'foo `touch %s`', 'foo && touch %s'])
def test_parameters_should_be_shellquoted(exploit):
    tmpfile = tempfile.mkstemp()[1]
    os.unlink(tmpfile)
    b = ws.webpasswd.web.app.test_client()
    with mock.patch.dict(os.environ, {'WEBPASSWD_CHANGE': '/bin/true'}):
        r = b.post('/', data={
            'username': 'myuser', 'current_password': 'current',
            'new_password': exploit, 'confirm': exploit})
        assert 'Password successfully changed' in r.data.decode('utf-8')
    assert not os.path.exists(tmpfile)
