# Debian packaging tools: Utility functions.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: July 25, 2013
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
import subprocess

# Initialize a logger.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def sha1(text):
    """
    Calculate the SHA1 fingerprint of text.

    :param text: The text to fingerprint (a string).
    :returns: The fingerprint of the text (a string).
    """
    context = hashlib.sha1()
    context.update(text)
    return context.hexdigest()

def same_filesystem(path1, path2):
    """
    Check whether two pathnames reside on the same file system.

    :param path1: The pathname of an existing file or directory.
    :param path2: The pathname of an existing file or directory.
    :returns: ``True`` if the pathnames reside on the same file system,
              ``False`` otherwise.
    """
    try:
        return os.stat(path1).st_dev == os.stat(path2).st_dev
    except Exception:
        return False

def execute(command, directory='.', capture=False):
    """
    Execute an external command and make sure it succeeded. Raises
    :py:class:`ExternalCommandFailed` when the command exits with
    a nonzero exit code.

    :param command: The shell command to execute (a string).
    :param directory: The working directory for the external command (a string).
    """
    logger.info("Executing external command: %s", command)
    kw = dict(cwd=directory)
    if capture:
        kw['stdout'] = subprocess.PIPE
    shell = subprocess.Popen(['bash', '-c', command], **kw)
    stdout, stderr = shell.communicate()
    if shell.wait() != 0:
        msg = "External command failed with exit code %s! (command: %s)"
        raise ExternalCommandFailed, msg % (shell.returncode, command)
    if capture:
        return stdout.strip()

class ExternalCommandFailed(Exception):
    """
    Raised by :py:func:`execute()` when an external command returns with a
    nonzero exit code.
    """
