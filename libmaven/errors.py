#
# Copyright (c) 2015 SAS Institute, Inc
#

"""
Exceptions used by libmaven
"""


class RestrictionParseError(Exception):
    """Raised when an error is encountered parsing a restriction spec"""


class VersionRangeParseError(Exception):
    """Raised when an error is encountered parsing a range spec"""
