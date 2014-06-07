# Debian packaging tools: Utility functions.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: June 8, 2014
# URL: https://github.com/xolox/python-deb-pkg-tools

"""
Miscellaneous functions
=======================

The functions in the :py:mod:`deb_pkg_tools.utils` module are not directly
related to Debian packages/repositories, however they are used by the other
modules in the `deb-pkg-tools` package.
"""

# Standard library modules.
import errno
import hashlib
import os
import pwd
import tempfile
import time

# External dependencies.
from humanfriendly import Spinner, Timer

# Modules included in our package.
from deb_pkg_tools.compat import total_ordering

def sha1(text):
    """
    Calculate the SHA1 fingerprint of text.

    :param text: The text to fingerprint (a string).
    :returns: The fingerprint of the text (a string).
    """
    context = hashlib.sha1()
    context.update(text.encode('utf-8'))
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

def makedirs(directory):
    """
    Create a directory and any missing parent directories.

    It is not an error if the directory already exists.

    :param directory: The pathname of a directory (a string).
    :returns: ``True`` if the directory was created, ``False`` if it already
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

class atomic_lock(object):

    """
    Atomic locking for files and directories. Exploits the fact that
    :py:func:`os.mkdir()` is atomic. This is UNIX only.
    """

    def __init__(self, pathname, wait=True):
        """
        Prepare to atomically lock the given pathname.

        :param pathname: The pathname of a file or directory (a string).
        :param wait: Block until the lock can be claimed (a boolean, defaults
                     to ``True``).
        """
        self.wait = bool(wait)
        self.pathname = os.path.realpath(pathname)
        self.lock_directory = os.path.join(tempfile.gettempdir(), '%s.lock' % sha1(self.pathname))

    def __enter__(self):
        """
        Atomically lock the given pathname.
        """
        spinner = Spinner()
        timer = Timer()
        while True:
            if makedirs(self.lock_directory):
                return
            elif self.wait:
                spinner.step("Waiting for lock on %s: %s .." % (self.pathname, timer))
                time.sleep(0.1)
            else:
                msg = "Failed to lock %s for exclusive access!"
                raise ResourceLockedException(msg % self.pathname)

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """
        Unlock the previously locked pathname.
        """
        if os.path.isdir(self.lock_directory):
            os.rmdir(self.lock_directory)

class ResourceLockedException(Exception):

    """
    Raised by :py:class:`atomic_lock()` when the lock cannot be created because
    another process has claimed the lock.
    """

@total_ordering
class OrderedObject(object):

    """
    By inheriting from this class and implementing :py:func:`OrderedObject._key()`
    objects gain support for equality comparison, rich comparison and a hash
    method that allows objects to be added to sets and used as dictionary keys.
    """

    def __eq__(self, other):
        """
        Enables equality comparison between objects.
        """
        return type(self) is type(other) and self._key() == other._key()

    def __lt__(self, other):
        """
        Enables rich comparison between objects.
        """
        return isinstance(other, OrderedObject) and self._key() < other._key()

    def __hash__(self):
        """
        Enables adding objects to sets.
        """
        return hash(self.__class__) ^ hash(self._key())

    def _key(self):
        """
        Get the comparison key of this object. Used to implement the equality
        and rich comparison operations.
        """
        raise NotImplementedError

# vim: ts=4 sw=4 et
