#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import semantic_version


def remove_spaces(string):
    return "".join(string.split())


def cmp(x, y):
    """
    Replacement for built-in Python 2 function cmp that was removed in Python 3
    From https://docs.python.org/2/library/functions.html?highlight=cmp#cmp :

        Compare the two objects x and y and return an integer according to the
        outcome. The return value is negative if x < y, zero if x == y and
        strictly positive if x > y.
    """
    if x == y:
        return 0
    elif x is None:
        return -1
    elif y is None:
        return 1
    else:
        # note that this is the minimal replacement function
        return (x > y) - (x < y)


class SortableSemverVersion(semantic_version.Version):
    """
    TODO: This is temporary workaround for unstable sort
    Revert this and associated changes once the upstream is fixed.
    https://github.com/rbarrois/python-semanticversion/issues/132
    """

    @property
    def precedence_key(self):
        return super().precedence_key + (self.build,)
