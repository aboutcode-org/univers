# Debian packaging tools: Version comparison.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 25, 2014
# URL: https://github.com/xolox/python-deb-pkg-tools

"""
Version comparison
==================

This module supports version comparison and sorting according to `section
5.6.12 of the Debian Policy Manual`_. It does so by using the python-apt_
binding (see :py:func:`compare_versions_with_python_apt()`) and/or the external
command ``dpkg --compare-versions`` (see :py:func:`compare_versions_with_dpkg()`).

.. _section 5.6.12 of the Debian Policy Manual: http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
.. _python-apt: http://apt.alioth.debian.org/python-apt-doc/
"""

# Standard library modules.
import logging

# External dependencies.
from executor import execute

# Initialize a logger.
logger = logging.getLogger(__name__)

# Optional external dependency on python-apt.
try:
    # The new name of the version comparison function.
    from apt_pkg import InitSystem, version_compare as apt_version_compare
    InitSystem()
    have_python_apt = True
except ImportError:
    try:
        # The old name of the version comparison function.
        from apt import VersionCompare as apt_version_compare
        have_python_apt = True
    except ImportError:
        have_python_apt = False

def compare_versions_with_python_apt(version1, operator, version2):
    """
    Compare Debian package versions using the python-apt_ binding. Compatible
    with newer versions of python-apt_ (:py:func:`apt_pkg.version_compare()`)
    and older versions (:py:func:`apt.VersionCompare()`). Raises
    :py:exc:`NotImplementedError` if python-apt_ is not available (neither of
    the mentioned functions can be imported).

    :param version1: The version on the left side of the comparison (a string).
    :param operator: The operator to use in the comparison (a string).
    :param version2: The version on the right side of the comparison (a string).
    :returns: ``True`` if the comparison succeeds, ``False`` if it fails.
    """
    if not have_python_apt:
        raise NotImplementedError("The python-apt binding is not installed!"
                                  " (or at least the import failed)")
    else:
        result = apt_version_compare(version1, version2)
        return ((operator == '<<' and result < 0) or
                (operator == '>>' and result > 0) or
                (operator in ('<', '<=') and result <= 0) or
                (operator in ('>', '>=') and result >= 0) or
                (operator == '=' and result == 0))

dpkg_comparison_cache = {}

def compare_versions_with_dpkg(version1, operator, version2):
    """
    Compare Debian package versions using the external command ``dpkg
    --compare-versions ...``. Caches the results of previous comparisons in
    order to minimize the number of times that the external command has to be
    run.

    :param version1: The version on the left side of the comparison (a string).
    :param operator: The operator to use in the comparison (a string).
    :param version2: The version on the right side of the comparison (a string).
    :returns: ``True`` if the comparison succeeds, ``False`` if it fails.
    """
    key = (version1, operator, version2)
    if key not in dpkg_comparison_cache:
        dpkg_comparison_cache[key] = execute('dpkg', '--compare-versions', version1, operator, version2, check=False, logger=logger)
    return dpkg_comparison_cache[key]

def compare_versions(version1, operator, version2):
    """
    Compare Debian package versions by using the python-apt_ binding (see
    :py:func:`compare_versions_with_python_apt()`) or the external command
    ``dpkg --compare-versions`` (see :py:func:`compare_versions_with_dpkg()`).

    :param version1: The version on the left side of the comparison (a string).
    :param operator: The operator to use in the comparison (a string).
    :param version2: The version on the right side of the comparison (a string).
    :returns: ``True`` if the comparison succeeds, ``False`` if it fails.
    """
    if have_python_apt:
        return compare_versions_with_python_apt(version1, operator, version2)
    else:
        return compare_versions_with_dpkg(version1, operator, version2)

class Version(str):

    """
    The :py:class:`Version` class is a subclass of the built in :py:class:`str`
    type that implements rich comparison according to the version sorting order
    defined in the Debian Policy Manual. Use it to sort Debian package versions
    like this:

      >>> from deb_pkg_tools.version import Version
      >>> unsorted = ['0.1', '0.5', '1.0', '2.0', '3.0', '1:0.4', '2:0.3']
      >>> print(sorted(Version(s) for s in unsorted))
      ['0.1', '0.5', '1.0', '2.0', '3.0', '1:0.4', '2:0.3']

    This example uses 'epoch' numbers (the numbers before the colons) to
    demonstrate that this version sorting order is different from regular
    sorting and 'natural order sorting'.
    """

    def __eq__(self, other):
        return compare_versions(self, '=', other) if type(self) is type(other) else NotImplemented

    def __ne__(self, other):
        return not compare_versions(self, '=', other) if type(self) is type(other) else NotImplemented

    def __lt__(self, other):
        return compare_versions(self, '<<', other) if type(self) is type(other) else NotImplemented

    def __le__(self, other):
        return compare_versions(self, '<=', other) if type(self) is type(other) else NotImplemented

    def __gt__(self, other):
        return compare_versions(self, '>>', other) if type(self) is type(other) else NotImplemented

    def __ge__(self, other):
        return compare_versions(self, '>=', other) if type(self) is type(other) else NotImplemented

    def __hash__(self):
        return hash(self.__class__) ^ hash(str(self))
