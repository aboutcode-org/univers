# Debian packaging tools: Utility functions.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: January 27, 2017
# URL: https://github.com/xolox/python-deb-pkg-tools

"""
Utility functions.

The functions in the :mod:`deb_pkg_tools.utils` module are not directly
related to Debian packages/repositories, however they are used by the other
modules in the `deb-pkg-tools` package.
"""

# Standard library modules.
import errno
import hashlib
import logging
import os
import random
import tempfile
import time

# External dependencies.
from executor import execute, ExternalCommandFailed
from humanfriendly import Spinner, Timer, compact

# Initialize a logger.
logger = logging.getLogger(__name__)

compact = compact
"""Alias for backwards compatibility."""


def sha1(text):
    """
    Calculate the SHA1 fingerprint of text.

    :param text: The text to fingerprint (a string).
    :returns: The fingerprint of the text (a string).
    """
    context = hashlib.sha1()
    context.update(text.encode('utf-8'))
    return context.hexdigest()


def makedirs(directory):
    """
    Create a directory and any missing parent directories.

    It is not an error if the directory already exists.

    :param directory: The pathname of a directory (a string).
    :returns: :data:`True` if the directory was created, :data:`False` if it already
              exists.
    """
    try:
        os.makedirs(directory)
        return True
    except OSError as e:
        if e.errno == errno.EEXIST:
            return False
        else:
            raise


def optimize_order(package_archives):
    """
    Shuffle a list of package archives in random order.

    Usually when scanning a large group of package archives, it really doesn't
    matter in which order we scan them. However the progress reported using
    :class:`humanfriendly.Spinner` can be more accurate when we shuffle the
    order. Why would that happen? When the following conditions are met:

    1. The package repository contains multiple versions of the same packages;
    2. The package repository contains both small and (very) big packages.

    If you scan the package archives in usual sorting order you will first hit
    a batch of multiple versions of the same small package which can be scanned
    very quickly (the progress counter will jump). Then you'll hit a batch of
    multiple versions of the same big package and scanning becomes much slower
    (the progress counter will hang). Shuffling mostly avoids this effect.
    """
    random.shuffle(package_archives)
    return package_archives


def find_debian_architecture():
    """
    Find the Debian architecture of the current environment.

    Uses :func:`os.uname()` to determine the current machine architecture
    (the fifth value returned by :func:`os.uname()`) and translates it into
    one of the `machine architecture labels`_ used in the Debian packaging
    system:

    ====================  ===================
    Machine architecture  Debian architecture
    ====================  ===================
    ``i686``              ``i386``
    ``x86_64``            ``amd64``
    ``armv6l``            ``armhf``
    ====================  ===================

    When the machine architecture is not listed above, this function falls back
    to the external command ``dpkg-architecture -qDEB_BUILD_ARCH`` (provided by
    the ``dpkg-dev`` package). This command is not used by default because:

    1. deb-pkg-tools doesn't have a strict dependency on ``dpkg-dev``.
    2. The ``dpkg-architecture`` program enables callers to set the current
       architecture and the exact semantics of this are unclear to me at the
       time of writing (it can't automagically provide a cross compilation
       environment, so what exactly does it do?).

    :returns: The Debian architecture (a string like ``i386``, ``amd64``,
              ``armhf``, etc).
    :raises: :exc:`~executor.ExternalCommandFailed` when the
             ``dpkg-architecture`` program is not available or reports an
             error.

    .. _machine architecture labels: https://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Architecture
    .. _more architectures: https://www.debian.org/ports/index.en.html#portlist-released
    """
    sysname, nodename, release, version, machine = os.uname()
    if machine == 'i686':
        return 'i386'
    elif machine == 'x86_64':
        return 'amd64'
    elif machine == 'armv6l':
        return 'armhf'
    else:
        return execute('dpkg-architecture', '-qDEB_BUILD_ARCH', capture=True, logger=logger).strip()


def find_installed_version(package_name):
    """
    Find the installed version of a Debian system package.

    Uses the ``dpkg-query --show --showformat='${Version}' ...`` command.

    :param package_name: The name of the package (a string).
    :returns: The installed version of the package (a string) or :data:`None` if
              the version can't be found.
    """
    try:
        return execute('dpkg-query', '--show', '--showformat=${Version}', package_name, capture=True, silent=True)
    except ExternalCommandFailed:
        return None


class atomic_lock(object):

    """
    Context manager for atomic locking of files and directories.

    This context manager exploits the fact that :func:`os.mkdir()` on UNIX
    is an atomic operation, which means it will only work on UNIX.

    Intended to be used with Python's :keyword:`with` statement:

    .. code-block:: python

       with atomic_lock('/var/www/apt-archive/some/repository'):
          # Inside the with block you have exclusive access.
          pass
    """

    def __init__(self, pathname, wait=True):
        """
        Prepare to atomically lock the given pathname.

        :param pathname: The pathname of a file or directory (a string).
        :param wait: Block until the lock can be claimed (a boolean, defaults
                     to :data:`True`).

        If ``wait=False`` and the file or directory cannot be locked,
        :exc:`ResourceLockedException` will be raised when entering the
        :keyword:`with` block.
        """
        self.wait = bool(wait)
        self.pathname = os.path.realpath(pathname)
        self.lock_directory = os.path.join(tempfile.gettempdir(), '%s.lock' % sha1(self.pathname))

    def __enter__(self):
        """Atomically lock the given pathname."""
        spinner = Spinner()
        timer = Timer()
        while True:
            if makedirs(self.lock_directory):
                return
            elif self.wait:
                spinner.step(label="Waiting for lock on %s: %s .." % (self.pathname, timer))
                time.sleep(0.1)
            else:
                msg = "Failed to lock %s for exclusive access!"
                raise ResourceLockedException(msg % self.pathname)

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Unlock the previously locked pathname."""
        if os.path.isdir(self.lock_directory):
            os.rmdir(self.lock_directory)


class ResourceLockedException(Exception):

    """Raised by :class:`atomic_lock()` when the lock can't be claimed."""
