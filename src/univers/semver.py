#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from univers.utils import remove_spaces
from univers.version_constraint import VersionConstraint
from univers.versions import SemverVersion

"""
node-semver and Rubygems semver-like related utilities.
"""


def get_caret_constraints(string):
    """
    Return a tuple of two VersionConstraint of ``SemverVersion`` representing
    the lower and upper bound of version constraint ``string`` that contains a
    caret node-semver- like range. Raise a ValueError if this is not a caret
    range.

    For example:
    >>> lower_bound, upper_bound = get_caret_constraints("^1.0.2")
    >>> vlow = SemverVersion("1.0.2")
    >>> vup = SemverVersion("2.0.0")
    >>> assert lower_bound == VersionConstraint(comparator=">=", version=vlow)
    >>> assert upper_bound == VersionConstraint(comparator="<", version=vup)
    """
    string = remove_spaces(string)
    if not string or not string.startswith("^"):
        raise ValueError(f"Invalid caret version range: {string!r}")

    version = string.lstrip("^")
    lower_bound = SemverVersion(version)
    upper_bound = SemverVersion(str(lower_bound.value.next_major()))

    return (
        VersionConstraint(comparator=">=", version=lower_bound),
        VersionConstraint(comparator="<", version=upper_bound),
    )


def get_tilde_constraints(string, operator="~"):
    """
    Return a tuple of two VersionConstraint of ``SemverVersion`` representing
    the lower and upper bound of a version range ``string`` that contains a
    tilde node-semver-like range.
    Raise a ValueError if this is not a tilde range.

    For example:
    >>> lower_bound, upper_bound = get_tilde_constraints("~1.0.2")
    >>> vlow = SemverVersion("1.0.2")
    >>> vup = SemverVersion("1.1.0")
    >>> assert lower_bound == VersionConstraint(comparator=">=", version=vlow)
    >>> assert upper_bound == VersionConstraint(comparator="<", version=vup)
    """
    string = remove_spaces(string)
    if not string or not string.startswith(operator):
        raise ValueError(f"Invalid version range: {string!r} " f"does not start with {operator!r}")

    version = string.lstrip(operator)
    lower_bound = SemverVersion(version)
    upper_bound = SemverVersion(str(lower_bound.value.next_minor()))

    return (
        VersionConstraint(comparator=">=", version=lower_bound),
        VersionConstraint(comparator="<", version=upper_bound),
    )


# FIXME: this is unlikely correct https://github.com/npm/node-semver/issues/112
def get_pessimistic_constraints(string):
    """
    Return a tuple of two VersionConstraint of ``SemverVersion`` representing
    the lower and upper bound of version range ``string`` that contains a
    pessimistic Ruby range.  Raise a ValueError if this is not a pessimistic
    Rubygems range.

    For example:
    >>> lower_bound, upper_bound = get_pessimistic_constraints("~>2.0.8")
    >>> vlow = SemverVersion("2.0.8")
    >>> vup = SemverVersion("2.1.0")
    >>> assert lower_bound == VersionConstraint(comparator=">=", version=vlow)
    >>> assert upper_bound == VersionConstraint(comparator="<", version=vup)
    """
    return get_tilde_constraints(string, operator="~>")
