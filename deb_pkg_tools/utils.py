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
import sys

# Alias for unicode() in Python 2.x and str() in Python 3.x.
if sys.version_info[0] == 2:
    unicode = unicode
else:
    unicode = str

# External dependencies.
from executor import execute

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

def str_compatible(class_to_decorate):
    """
    Class decorator that makes it easy to implement human readable object
    representations containing Unicode characters that are compatible with both
    Python 2.x (with its :py:func:`object.__unicode__()` and
    :py:func:`object.__str__()` methods) and Python 3.x (with its
    :py:func:`object.__str__()` and :py:func:`object.__bytes__()` methods).

    This decorator expects the ``__unicode__()`` method to return a Unicode
    string (i.e. you write Python 2.x compatible code). The missing part will
    be filled in automatically by encoding the Unicode string to UTF-8.
    """
    if sys.version_info[0] == 2:
        class_to_decorate.__str__ = lambda self: unicode(self).encode('utf-8')
    elif sys.version_info[0] == 3:
        class_to_decorate.__str__ = class_to_decorate.__unicode__
        class_to_decorate.__bytes__ = lambda self: str(self).encode('utf-8')
    return class_to_decorate

_comparison_cache = {}

def dpkg_compare_versions(version1, operator, version2):
    """
    Run ``dpkg --compare-versions ...`` and return the result.
    """
    key = (version1, operator, version2)
    if key not in _comparison_cache:
        _comparison_cache[key] = execute('dpkg', '--compare-versions', version1, operator, version2, check=False, logger=logger)
    return _comparison_cache[key]

# Copied from http://hg.python.org/cpython/file/2.7/Lib/functools.py#l53 for Python 2.6 compatibility.

def total_ordering(cls):
    """Class decorator that fills in missing ordering methods"""
    convert = {
        '__lt__': [('__gt__', lambda self, other: not (self < other or self == other)),
                   ('__le__', lambda self, other: self < other or self == other),
                   ('__ge__', lambda self, other: not self < other)],
        '__le__': [('__ge__', lambda self, other: not self <= other or self == other),
                   ('__lt__', lambda self, other: self <= other and not self == other),
                   ('__gt__', lambda self, other: not self <= other)],
        '__gt__': [('__lt__', lambda self, other: not (self > other or self == other)),
                   ('__ge__', lambda self, other: self > other or self == other),
                   ('__le__', lambda self, other: not self > other)],
        '__ge__': [('__le__', lambda self, other: (not self >= other) or self == other),
                   ('__gt__', lambda self, other: self >= other and not self == other),
                   ('__lt__', lambda self, other: not self >= other)]
    }
    roots = set(dir(cls)) & set(convert)
    if not roots:
        raise ValueError('must define at least one ordering operation: < > <= >=')
    root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
    for opname, opfunc in convert[root]:
        if opname not in roots:
            opfunc.__name__ = opname
            opfunc.__doc__ = getattr(int, opname).__doc__
            setattr(cls, opname, opfunc)
    return cls

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
