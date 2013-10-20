# Debian packaging tools: Utility functions.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 20, 2013
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
import subprocess
import sys
import time

# External dependencies.
import coloredlogs
from debian.deb822 import Deb822
from humanfriendly import concatenate, format_timespan, pluralize

# Initialize a logger.
logger = logging.getLogger(__name__)

# Cache of installed packages.
installed_packages = set()

def sha1(text):
    """
    Calculate the SHA1 fingerprint of text.

    :param text: The text to fingerprint (a string).
    :returns: The fingerprint of the text (a string).
    """
    context = hashlib.sha1()
    context.update(text)
    return context.hexdigest()

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

def install_dependencies(package, dependencies, logger=logger):
    """
    Install dependencies on system programs using ``apt-get``. When the
    required packages are already installed this is very fast because it just
    needs to confirm the existence of a couple of files. How the packages are
    installed depends on the privilege level:

    1. When running as ``root`` any missing dependencies are installed
       automatically and non-interactively using ``apt-get install --yes``.
       This is very useful when setting up a build environment in a chroot. My
       justification for this is that if you trust ``deb-pkg-tools`` enough to
       run it as ``root``, you probably trust it enough to install a couple of
       harmless dependencies...

    2. When not running as ``root``, missing dependencies trigger an
       interactive confirmation prompt. If the user confirms, the missing
       dependencies are installed using ``sudo apt-get install --yes``. If the
       user doesn't confirm, the exception :py:class:`DependencyProblem` is
       raised.

    :param package: The name of the Python package that is requesting the
                    Debian package(s) to be installed (a string).
    :param dependencies: A list of strings with the names of the required
                         Debian packages.
    :param logger: Specifies the custom logger to use (optional).
    """
    coloredlogs.install()
    find_installed_packages()
    missing_dependencies = [d for d in dependencies if d not in installed_packages]
    if missing_dependencies:
        missing_dependencies = sorted(missing_dependencies)
        dependencies_label = pluralize(len(missing_dependencies), "dependency", "dependencies")
        logger.warn("The package %s is missing %s (%s).", package,
                    dependencies_label, concatenate(missing_dependencies))
        if os.getuid() != 0:
            okay_to_install = False
            try:
                sys.stderr.write("Is it okay if I install the missing system packages? [Y/n] ")
                reply = raw_input()
                okay_to_install = reply.strip() in ('', 'Y', 'y')
            except:
                okay_to_install = False
            if not okay_to_install:
                msg = "The package %s is missing %s! (%s)"
                raise DependencyProblem, msg % (package, dependencies_label, concatenate(missing_dependencies))
        logger.info("Installing %s of %s: %s", dependencies_label,
                    package, concatenate(missing_dependencies))
        execute('apt-get', 'install', '--yes', *missing_dependencies, sudo=True, logger=logger)
        for package in missing_dependencies:
            installed_packages.add(package)

def find_installed_packages():
    """
    Find the names of the system packages that are currently installed.

    :returns: A :py:class:`set` of package names (strings).
    """
    if not installed_packages:
        time_started = time.time()
        filename = '/var/lib/dpkg/status'
        logger.info("Checking installed system packages by parsing %s ..", filename)
        handle = open(filename)
        for entry in Deb822.iter_paragraphs(handle):
            if entry.get('Status') == 'install ok installed':
                installed_packages.add(entry['Package'])
        handle.close()
        logger.info("Found %d installed system packages in %s.",
                    len(installed_packages),
                    format_timespan(time.time() - time_started))
    return installed_packages

class ExternalCommandFailed(Exception):
    """
    Raised by :py:func:`execute()` when an external command returns with a
    nonzero exit code.
    """

class DependencyProblem(Exception):
    """
    Raised by :py:func:`install_dependencies()` when the user refuses
    installation of missing dependencies.
    """
