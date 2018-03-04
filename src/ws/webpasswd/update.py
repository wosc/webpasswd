from ctypes import POINTER, cast, byref, sizeof
from ctypes import c_char_p, c_char, c_int
from ctypes import memmove
import sys
import os
import re
import pam


encoding = 'utf-8'

if sys.version_info >= (3,):
    text_type = str
else:
    text_type = unicode

pam_chauthtok = pam.libpam.pam_chauthtok
pam_chauthtok.restype = c_int
pam_chauthtok.argtypes = [pam.PamHandle, c_int]


def change_password(user, current, new):
    """Copy&paste of pam.pam.pam_authenticate to add a `pam_chauthtok` call
    after a successful `pam_authenticate`."""
    @pam.conv_func
    def my_conv(n_messages, messages, p_response, app_data):
        """Simple conversation function that responds to any
        prompt where the echo is off with the supplied password"""
        # Create an array of n_messages response objects
        addr = pam.calloc(n_messages, sizeof(pam.PamResponse))
        response = cast(addr, POINTER(pam.PamResponse))
        p_response[0] = response
        for i in range(n_messages):
            if messages[i].contents.msg_style == pam.PAM_PROMPT_ECHO_OFF:
                pwd = password[0]
                dst = pam.calloc(len(pwd) + 1, sizeof(c_char))
                memmove(dst, c_char_p(pwd), len(pwd))
                response[i].resp = dst
                response[i].resp_retcode = 0
        return 0

    service = 'passwd'
    # python3 ctypes requires bytes
    if isinstance(service, text_type):
        service = service.encode(encoding)
    if isinstance(user, text_type):
        user = user.encode(encoding)
    if isinstance(current, text_type):
        current = current.encode(encoding)
    if isinstance(new, text_type):
        new = new.encode(encoding)

    password = [None]  # Closure transport mechanism into my_conv
    handle = pam.PamHandle()
    conv = pam.PamConv(my_conv, 0)
    retval = pam.pam_start(service, user, byref(conv), byref(handle))
    if retval != 0:
        raise RuntimeError('pam_start() failed')

    password[0] = current
    retval = pam.pam_authenticate(handle, 0)
    error = None
    if retval != 0:
        error = pam.pam_strerror(handle, retval)
        if sys.version_info >= (3,):
            error = error.decode(encoding)
        error = 'authenticate: %s' % error

    if error is None:
        password[0] = new
        retval = pam_chauthtok(handle, 0)
        if retval != 0:
            error = pam.pam_strerror(handle, retval)
            if sys.version_info >= (3,):
                error = error.decode(encoding)
            error = 'chauthtok: %s' % error

    pam.pam_end(handle, retval)

    if error is not None:
        raise RuntimeError('%s: %s' % (retval, error))


def valid_user(user):
    return user != 'root' and re.search('^[-_.a-z0-9]+$', user)


def main():
    """Changes the UNIX password using PAM. Like passwd, but non-interactive.
    Must be run with root privileges."""
    if len(sys.argv) < 4:
        sys.stderr.write(
            'Usage: %s username current-password new-password\n' % sys.argv[0])
        sys.exit(1)

    if os.getuid() != 0:
        sys.stderr.write('%s: root privileges required.\n' % sys.argv[0])
        sys.exit(1)

    user, current, new = sys.argv[1:4]
    debug = '--debug' in sys.argv

    if valid_user(user):
        try:
            change_password(user, current, new)
            sys.exit(0)
        except Exception as e:
            if debug:
                sys.stderr.write('%s\n' % e)

    sys.stderr.write('Error: Invalid username or password.\n')
    sys.exit(1)
