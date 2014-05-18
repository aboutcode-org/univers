# Debian packaging tools: Utility functions.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 18, 2014
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
import pwd

# External dependencies.
from executor import execute

# Modules included in our package.
from deb_pkg_tools.compat import total_ordering

# Initialize a logger.
logger = logging.getLogger(__name__)

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

try:
    # Version comparison using the python-apt binding.
    from apt import VersionCompare
    def dpkg_compare_versions(version1, operator, version2):
        """
        Compare Debian package versions using :py:func:`apt.VersionCompare()`.
        """
        vc = VersionCompare(version1, version2)
        return ((operator == '<<' and vc < 0) or
                (operator == '>>' and vc > 0) or
                (operator in ('<', '<=') and vc <= 0) or
                (operator in ('>', '>=') and vc >= 0) or
                (operator == '=' and vc == 0))
except ImportError:
    # Version comparison using the `dpkg --compare-versions ...' command.
    _comparison_cache = {}
    def dpkg_compare_versions(version1, operator, version2):
        """
        Compare Debian package versions using ``dpkg --compare-versions ...``.
        """
        key = (version1, operator, version2)
        if key not in _comparison_cache:
            _comparison_cache[key] = execute('dpkg', '--compare-versions', version1, operator, version2, check=False, logger=logger)
        return _comparison_cache[key]

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
        raise NotImplemented

# vim: ts=4 sw=4 et
