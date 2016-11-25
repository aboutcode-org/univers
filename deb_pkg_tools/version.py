# Debian packaging tools: Version comparison.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 25, 2016
# URL: https://github.com/xolox/python-deb-pkg-tools

"""
Version sorting according to Debian semantics.

This module supports version comparison and sorting according to `section
5.6.12 of the Debian Policy Manual`_. It does so by using the python-apt_
binding (see :func:`compare_versions_with_python_apt()`) and/or the external
command ``dpkg --compare-versions`` (see :func:`compare_versions_with_dpkg()`).

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
    Compare Debian package versions using the python-apt_ binding.

    :param version1: The version on the left side of the comparison (a string).
    :param operator: The operator to use in the comparison (a string).
    :param version2: The version on the right side of the comparison (a string).
    :returns: :data:`True` if the comparison succeeds, :data:`False` if it fails.
    :raises: :exc:`~exceptions.NotImplementedError` if python-apt_ is not
             available (neither of the functions mentioned below can be
             imported).

    This function is compatible with newer versions of python-apt_
    (:func:`apt_pkg.version_compare()`) and older versions
    (:func:`apt.VersionCompare()`).
    """
    if not have_python_apt:
        raise NotImplementedError()
    result = apt_version_compare(version1, version2)
    return ((operator == '<<' and result < 0) or
            (operator == '>>' and result > 0) or
            (operator in ('<', '<=') and result <= 0) or
            (operator in ('>', '>=') and result >= 0) or
            (operator == '=' and result == 0))


def compare_versions_with_dpkg(version1, operator, version2):
    """
    Compare Debian package versions using the external command ``dpkg --compare-versions ...``.

    :param version1: The version on the left side of the comparison (a string).
    :param operator: The operator to use in the comparison (a string).
    :param version2: The version on the right side of the comparison (a string).
    :returns: :data:`True` if the comparison succeeds, :data:`False` if it fails.
    """
    return execute('dpkg', '--compare-versions', version1, operator, version2, check=False, logger=logger)


dpkg_comparison_cache = {}


def compare_versions(version1, operator, version2):
    """
    Compare Debian package versions using the best available method.

    :param version1: The version on the left side of the comparison (a string).
    :param operator: The operator to use in the comparison (a string).
    :param version2: The version on the right side of the comparison (a string).
    :returns: :data:`True` if the comparison succeeds, :data:`False` if it fails.

    This function prefers using the python-apt_ binding (see
    :func:`compare_versions_with_python_apt()`) but will fall back to the
    external command ``dpkg --compare-versions`` when required (see
    :func:`compare_versions_with_dpkg()`).
    """
    if operator == '=' and str(version1) == str(version2):
        return True
    key = (version1, operator, version2)
    try:
        return dpkg_comparison_cache[key]
    except KeyError:
        if have_python_apt:
            value = compare_versions_with_python_apt(version1, operator, version2)
        else:
            value = compare_versions_with_dpkg(version1, operator, version2)
        dpkg_comparison_cache[key] = value
        return value


class Version(str):

    """
    Rich comparison of Debian package versions as first-class Python objects.

    The :class:`Version` class is a subclass of the built in :class:`str` type
    that implements rich comparison according to the version sorting order
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

    def __hash__(self):
        """Enable adding objects to sets and using them as dictionary keys."""
        try:
            return self._cached_hash
        except AttributeError:
            value = hash(str(self))
            self._cached_hash = value
            return value

    def __eq__(self, other):
        """Enable equality comparison between version objects."""
        return compare_versions(self, '=', other) if type(self) is type(other) else NotImplemented

    def __ne__(self, other):
        """Enable non-equality comparison between version objects."""
        return not compare_versions(self, '=', other) if type(self) is type(other) else NotImplemented

    def __lt__(self, other):
        """Enable less-than comparison between version objects."""
        return compare_versions(self, '<<', other) if type(self) is type(other) else NotImplemented

    def __le__(self, other):
        """Enable less-than-or-equal comparison between version objects."""
        return compare_versions(self, '<=', other) if type(self) is type(other) else NotImplemented

    def __gt__(self, other):
        """Enable greater-than comparison between version objects."""
        return compare_versions(self, '>>', other) if type(self) is type(other) else NotImplemented

    def __ge__(self, other):
        """Enable greater-than-or-equal comparison between version objects."""
        return compare_versions(self, '>=', other) if type(self) is type(other) else NotImplemented
