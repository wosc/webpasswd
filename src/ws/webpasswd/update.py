from ctypes import CDLL, POINTER, cast, byref, sizeof
from ctypes import c_char_p, c_char, c_int
from ctypes import memmove
from ctypes.util import find_library
import sys
import os
import re
import pam.__internals as pam


encoding = 'utf-8'


class LibPAM(pam.PamAuthenticator):

    def __init__(self):
        super().__init__()
        libpam = CDLL(find_library("pam"))
        self.pam_chauthtok = libpam.pam_chauthtok
        self.pam_chauthtok.restype = c_int
        self.pam_chauthtok.argtypes = [pam.PamHandle, c_int]


libpam = LibPAM()


def change_password(user, current, new):
    """Copy&paste of PamAuthenticator.authenticate to add `pam_chauthtok`
    after a successful `pam_authenticate`."""
    @pam.conv_func
    def my_conv(n_messages, messages, p_response, app_data):
        """Simple conversation function that responds to any
        prompt where the echo is off with the supplied password"""
        # Create an array of n_messages response objects
        addr = libpam.calloc(n_messages, sizeof(pam.PamResponse))
        response = cast(addr, POINTER(pam.PamResponse))
        p_response[0] = response
        for i in range(n_messages):
            if messages[i].contents.msg_style == pam.PAM_PROMPT_ECHO_OFF:
                pwd = password[0]
                dst = libpam.calloc(len(pwd) + 1, sizeof(c_char))
                memmove(dst, c_char_p(pwd), len(pwd))
                response[i].resp = dst
                response[i].resp_retcode = 0
        return 0

    service = 'passwd'
    # python3 ctypes requires bytes
    if isinstance(service, str):
        service = service.encode(encoding)
    if isinstance(user, str):
        user = user.encode(encoding)
    if isinstance(current, str):
        current = current.encode(encoding)
    if isinstance(new, str):
        new = new.encode(encoding)

    password = [None]  # Closure transport mechanism into my_conv
    handle = pam.PamHandle()
    conv = pam.PamConv(my_conv, 0)
    retval = libpam.pam_start(service, user, byref(conv), byref(handle))
    if retval != 0:
        raise RuntimeError('pam_start() failed')

    password[0] = current
    retval = libpam.pam_authenticate(handle, 0)
    error = None
    if retval != 0:
        error = libpam.pam_strerror(handle, retval).decode(encoding)
        error = 'authenticate: %s' % error

    if error is None:
        password[0] = new
        retval = libpam.pam_chauthtok(handle, 0)
        if retval != 0:
            error = libpam.pam_strerror(handle, retval).decode(encoding)
            error = 'chauthtok: %s' % error

    libpam.pam_end(handle, retval)

    if error is not None:
        raise RuntimeError('%s: %s' % (retval, error))


def valid_user(user):
    return user != 'root' and re.search('^[-_.a-z0-9]+$', user)


def main():
    """Changes the UNIX password using PAM. Like passwd, but non-interactive.
    Must be run with root privileges."""
    if len(sys.argv) < 2:
        sys.stderr.write('Usage: %s username\n' % sys.argv[0])
        sys.exit(1)

    if os.getuid() != 0:
        sys.stderr.write('%s: root privileges required.\n' % sys.argv[0])
        sys.exit(1)

    user = sys.argv[1]
    debug = '--debug' in sys.argv
    current, new = [x.strip('\n') for x in sys.stdin]

    if valid_user(user):
        try:
            change_password(user, current, new)
            sys.exit(0)
        except Exception as e:
            if debug:
                sys.stderr.write('%s\n' % e)

    sys.stderr.write('Error: Invalid username or password.\n')
    sys.exit(1)
