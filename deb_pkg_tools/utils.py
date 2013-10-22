# Debian packaging tools: Utility functions.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 22, 2013
# URL: https://github.com/xolox/python-deb-pkg-tools

"""
Miscellaneous functions
=======================

The functions in the :py:mod:`deb_pkg_tools.utils` module are not directly
related to Debian packages/repositories, however they are used by the other
modules in the `deb-pkg-tools` package.
"""

# Standard library modules.
import hashlib
import logging
import os
import pipes
import pwd
import subprocess

# Initialize a logger.
logger = logging.getLogger(__name__)

def sha1(text):
    """
    Calculate the SHA1 fingerprint of text.

    :param text: The text to fingerprint (a string).
    :returns: The fingerprint of the text (a string).
    """
    context = hashlib.sha1()
    context.update(text)
    return context.hexdigest()

def find_home_directory():
    """
    Determine the home directory of the current user.
    """
    try:
        home = os.path.realpath(os.environ['HOME'])
        assert os.path.isdir(home)
        return home
    except Exception:
        return pwd.getpwuid(os.getuid()).pw_dir

def execute(*command, **options):
    """
    Execute an external command and make sure it succeeded. Raises
    :py:class:`ExternalCommandFailed` when the command exits with
    a nonzero exit code.

    :param command: The command to execute. If this is a single string it is
                    assumed to be a shell command and executed directly.
                    Otherwise it should be a tuple of strings, in this case
                    each string will be quoted individually using
                    :py:func:`pipes.quote()`.
    :param directory: The working directory for the external command (a string,
                      defaults to the current working directory).
    :param check: If ``True`` (the default) and the external command exits with
                  a nonzero status code, an exception is raised.
    :param capture: If ``True`` (not the default) the standard output of the
                    external command is returned as a string.
    :param logger: Specifies the custom logger to use (optional).
    :param sudo: If ``True`` (the default is ``False``) and we're not running
                 with ``root`` privileges the command is prefixed with ``sudo``.
    :returns: If ``capture=True`` the standard output of the external command
              is returned as a string, otherwise ``None`` is returned.
    """
    custom_logger = options.get('logger', logger)
    if len(command) == 1:
        command = command[0]
    else:
        command = ' '.join(pipes.quote(a) for a in command)
    if options.get('sudo', False) and os.getuid() != 0:
        command = 'sudo sh -c %s' % pipes.quote(command)
    custom_logger.debug("Executing external command: %s", command)
    kw = dict(cwd=options.get('directory', '.'))
    if options.get('capture', False):
        kw['stdout'] = subprocess.PIPE
    shell = subprocess.Popen(['bash', '-c', command], **kw)
    stdout, stderr = shell.communicate()
    if options.get('check', True) and shell.returncode != 0:
        msg = "External command failed with exit code %s! (command: %s)"
        raise ExternalCommandFailed, msg % (shell.returncode, command)
    if options.get('capture', False):
        return stdout.strip()

class ExternalCommandFailed(Exception):
    """
    Raised by :py:func:`execute()` when an external command returns with a
    nonzero exit code.
    """
