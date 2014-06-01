# Debian packaging tools: Utility functions.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: June 1, 2014
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
import os
import pwd

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

class atomic_lock(object):

    """
    Atomic locking for files and directories. Exploits the fact that
    :py:func:`os.mkdir()` is atomic. This is UNIX only.
    """

    def __init__(self, pathname):
        """
        Atomically lock the given pathname.

        :param pathname: The pathname of a file or directory (a string).
        """
        self.pathname = pathname
        self.lock_directory = '%s.lock' % self.pathname
        parent_directory = os.path.dirname(pathname)
        if not os.path.isdir(parent_directory):
            os.makedirs(parent_directory)

    def __enter__(self):
        try:
            os.mkdir(self.lock_directory)
        except OSError as e:
            if e.errno == 17: # EEXIST
                msg = "Failed to lock %s for exclusive access!"
                raise ResourceLockedException(msg % self.pathname)
            raise

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
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
