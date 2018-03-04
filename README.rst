==============================
Web-based UNIX password change
==============================

This packages provides a web UI for the UNIX ``passwd`` command, e.g. so that
SFTP-only user accounts can still change their password.

WARNING: The passwords are passed in plaintext via popen from the CGI process to
the helper process that runs under sudo. So maybe don't use this in an
adversarial environment where people might spy on your process list or something.


Usage
=====

Set up your webserver to run the CGI script. Here's an example apache
configuration snippet::

    ScriptAlias /passwd /path/to/venv/bin/webpasswd-cgi

As changing the password for another user requires root access, you also need to
setup passwordless sudo execution for the ``webpasswd-change`` helper.
Add a rule like this, e.g. in ``/etc/sudoers.d/webpasswd``::

    www-data ALL=NOPASSWD:/path/to/venv/bin/webpasswd-change

``www-data`` is the user the webserver that executes the CGI script runs as.


Running tests
=============

You'll need to add a user account ``webpasswd``, and interactively during the
test run reset its password as instructed.
