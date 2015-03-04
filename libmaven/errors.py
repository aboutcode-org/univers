#
# Copyright (c) 2015 SAS Institute, Inc
#

"""
Exceptions used by libmaven
"""


class ArtifactParseError(Exception):
    """Raised when an error is encountered parsing maven coordinates"""


class RestrictionParseError(Exception):
    """Raised when an error is encountered parsing a restriction spec"""


class VersionRangeParseError(Exception):
    """Raised when an error is encountered parsing a range spec"""
