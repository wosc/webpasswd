==============================
Web-based UNIX password change
==============================

This packages provides a web UI for the UNIX ``passwd`` command, e.g. so that
SFTP-only user accounts can still change their password.


Usage
=====

Set up your webserver to run the CGI script. Here's an example apache
configuration snippet::

    ScriptAlias /passwd /path/to/venv/bin/webpasswd-cgi

As changing the password for another user requires root access, you also need to
setup passwordless sudo execution for the ``webpasswd-change`` helper.
Add a rule like this, e.g. in ``/etc/sudoers.d/webpasswd``::

    www-data ALL=NOPASSWD:/path/to/venv/bin/webpasswd-change

(``www-data`` means the user the webserver executing the CGI script runs as.)

You can pass the following environment variables to the CGI script:

:WEBPASSWD_CHANGE: Path to ``webpasswd-change`` helper. If unset, assumes
    a virtualenv installation (so it's located next to ``webpasswd-cgi``)
:WEBPASSWD_STYLESHEET: URL to a stylesheet to link to instead of using the
    built-in styles


Running tests
=============

You'll need to add a user account ``webpasswd``, and interactively during the
test run reset its password as instructed.
