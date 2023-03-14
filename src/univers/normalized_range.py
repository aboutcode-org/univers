#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.


import operator
import re
from typing import List
from typing import Union

import attr

from univers.span import Span
from univers.version_range import VersionRange
from univers.versions import AlpineLinuxVersion
from univers.versions import ArchLinuxVersion
from univers.versions import ComposerVersion
from univers.versions import DebianVersion
from univers.versions import GenericVersion
from univers.versions import GentooVersion
from univers.versions import GolangVersion
from univers.versions import MavenVersion
from univers.versions import NginxVersion
from univers.versions import NugetVersion
from univers.versions import OpensslVersion
from univers.versions import PypiVersion
from univers.versions import RpmVersion
from univers.versions import RubygemsVersion
from univers.versions import SemverVersion


@attr.s(frozen=True, order=False, eq=True, hash=True)
class NormalizedVersionRanges:
    """
    A NormalizedVersionRange represents a list of VersionRange resolved
    from diffrent datsource.
    """

    # A tuple of VersionRange
    version_ranges = attr.ib(type=tuple, default=attr.Factory(tuple))

    def __str__(self):
        return "(" + ", ".join([f"'{str(vers)}'" for vers in self.version_ranges]) + ")"

    @staticmethod
    def get_span_boundry(comparator: str, version: str, version_map: dict):
        """
        Return Span with Lower and Upper boundry limit.
        """
        index = NormalizedVersionRanges.get_version_rank(version, version_map)
        resolved_operator = OPERATOR_BY_COMPRATOR.get(comparator, operator.eq)

        if resolved_operator == operator.lt:
            return Span(1, index - 1)
        if resolved_operator == operator.gt:
            return Span(index + 1, len(version_map))
        if resolved_operator == operator.ge:
            return Span(index, len(version_map))
        if resolved_operator == operator.le:
            return Span(1, index)
        if resolved_operator == operator.eq:
            return Span(index)
        if resolved_operator == operator.ne:
            return Span(1, index - 1).union(Span(index + 1, len(version_map)))

    @staticmethod
    def get_version_range_from_span(total_span: Span, purl_type: str, reverse_version_map: dict):
        """
        Return list containg VersionRange for all subspans in a Span.
        """
        version_ranges = []
        list_of_span = total_span.subspans()
        for span in list_of_span:
            lower_bound = reverse_version_map[span.start]
            upper_bound = reverse_version_map[span.end]
            vers_exp = (
                f"vers:{purl_type}/{lower_bound}"
                if lower_bound == upper_bound
                else f"vers:{purl_type}/>={lower_bound}|<={upper_bound}"
            )
            version_ranges.append(VersionRange.from_string(vers_exp))
        return version_ranges

    @staticmethod
    def get_version_rank(version: str, version_map: dict):
        """
        Return equivalent integer ranking for a version.
        """
        try:
            return version_map[strip_leading_v(version)]
        except KeyError as err:
            err.args = (f"{version} doesn't exist.",)
            raise

    @staticmethod
    def parse_constraint(constraint: str):
        """
        Return operator and version from a constraint
        For example:
        >>> assert NormalizedVersionRanges.parse_constraint(">=7.0.0") == ('>=', '7.0.0')
        >>> assert NormalizedVersionRanges.parse_constraint("=7.0.0") == ('=', '7.0.0')
        >>> assert NormalizedVersionRanges.parse_constraint("[3.0.0") == ('[', '3.0.0')
        >>> assert NormalizedVersionRanges.parse_constraint("3.1.25]") == (']', '3.1.25')
        """
        if constraint.startswith(("<=", ">=", "==", "!=")):
            return constraint[:2], constraint[2:]

        if constraint.startswith(("<", ">", "=", "[", "(")):
            return constraint[0], constraint[1:]

        if constraint.endswith(("]", ")")):
            return constraint[-1], constraint[:-1]
        return None, constraint

    @staticmethod
    def get_version_map(versions: List, purl_type: str):
        """
        Return dict mapping version to integer.
        """
        if purl_type not in VERSIONS_BY_PACKAGE_TYPE:
            return

        version_type = VERSIONS_BY_PACKAGE_TYPE.get(purl_type)
        sorted_versions = sorted([version_type(i) for i in versions])
        sorted_versions = [version.string for version in sorted_versions]
        index = list(range(1, len(sorted_versions) + 1, 1))
        return dict(zip(sorted_versions, index))

    @classmethod
    def from_github(cls, range_expression: Union[str, List], purl_type: str, all_versions: List):
        """
        Return NormalizedVersionRanges computed from GithHub version range expression.
        GitHub range_expression example::
            ">= 10.4.0, < 10.4.1"
            "> 7.1.1"
        """
        version_map = cls.get_version_map(all_versions, purl_type)
        reverse_version_map = {value: key for key, value in version_map.items()}

        items = [range_expression] if isinstance(range_expression, str) else range_expression
        total_span = None
        for item in items:
            gh_constraints = item.strip().replace(" ", "")
            constraints = gh_constraints.split(",")
            local_span = None
            for constraint in constraints:
                if not constraint:
                    continue
                gh_comparator, gh_version = cls.parse_constraint(constraint)
                span = cls.get_span_boundry(gh_comparator, strip_leading_v(gh_version), version_map)
                local_span = span if not local_span else local_span.intersection(span)

            total_span = local_span if not total_span else total_span.union(local_span)

        version_ranges = cls.get_version_range_from_span(total_span, purl_type, reverse_version_map)
        return cls(version_ranges=version_ranges)

    @classmethod
    def from_snyk(cls, range_expression: Union[str, List], purl_type: str, all_versions: List):
        """
        Return NormalizedVersionRanges computed from Snyk version range expression.
        Snyk range_expression example::
            ">=4.0.0, <4.0.10.16"
            " >=4.1.0, <4.4.15.7"
            "[3.0.0,3.1.25)
        """
        version_map = cls.get_version_map(all_versions, purl_type)
        reverse_version_map = {value: key for key, value in version_map.items()}

        items = [range_expression] if isinstance(range_expression, str) else range_expression
        total_span = None
        for item in items:
            delimiter = "," if "," in item else " "
            if delimiter == ",":
                snyk_constraints = item.strip().replace(" ", "")
                constraints = snyk_constraints.split(",")
            else:
                snyk_constraints = item.strip()
                constraints = snyk_constraints.split(" ")
            local_span = None
            for constraint in constraints:
                if not constraint:
                    continue
                snyk_comparator, snyk_version = cls.parse_constraint(constraint)
                if not snyk_version:
                    continue
                span = cls.get_span_boundry(
                    snyk_comparator, strip_leading_v(snyk_version), version_map
                )
                local_span = span if not local_span else local_span.intersection(span)

            total_span = local_span if not total_span else total_span.union(local_span)

        version_ranges = cls.get_version_range_from_span(total_span, purl_type, reverse_version_map)
        return cls(version_ranges=version_ranges)

    @classmethod
    def from_gitlab(cls, range_expression: Union[str, List], purl_type: str, all_versions: List):
        """
        Return NormalizedVersionRanges computed from GitLab version range expression.
        GitLab range_expression example::
            "[7.0.0,7.0.11),[7.2.0,7.2.4)"
            "[7.0.0,7.0.11),[7.2.0,7.2.4)"
            ">=4.0,<4.3||>=5.0,<5.2"
            ">=0.19.0 <0.30.0"
            ">=1.5,<1.5.2"
        """

        version_map = cls.get_version_map(all_versions, purl_type)
        reverse_version_map = {value: key for key, value in version_map.items()}

        items = [range_expression] if isinstance(range_expression, str) else range_expression
        global_span = None
        for item in items:
            gitlab_constraints = item.strip()
            if gitlab_constraints.startswith(("[", "(")):
                # transform "[7.0.0,7.0.11),[7.2.0,7.2.4)" -> [ "[7.0.0,7.0.11)", "[7.2.0,7.2.4)" ]
                splitted = gitlab_constraints.split(",")
                constraints = [f"{a},{b}" for a, b in zip(splitted[::2], splitted[1::2])]
                delimiter = ","

            else:
                # transform ">=4.0,<4.3||>=5.0,<5.2" -> [ ">=4.0,<4.3", ">=5.0,<5.2" ]
                # transform ">=0.19.0 <0.30.0" -> [ ">=0.19.0 <0.30.0" ]
                # transform ">=1.5,<1.5.2" -> [ ">=1.5,<1.5.2" ]
                delimiter = "," if "," in gitlab_constraints else " "
                constraints = gitlab_constraints.split("||")
            total_span = None
            for constraint in constraints:
                local_span = None
                for subcontraint in constraint.strip().split(delimiter):
                    if not subcontraint:
                        continue
                    gitlab_comparator, gitlab_version = cls.parse_constraint(subcontraint.strip())
                    if not gitlab_version:
                        continue
                    span = cls.get_span_boundry(
                        gitlab_comparator, strip_leading_v(gitlab_version), version_map
                    )
                    local_span = span if not local_span else local_span.intersection(span)

                total_span = local_span if not total_span else total_span.union(local_span)
            global_span = total_span if not global_span else global_span.union(total_span)

        version_ranges = cls.get_version_range_from_span(
            global_span, purl_type, reverse_version_map
        )
        return cls(version_ranges=version_ranges)

    @classmethod
    def from_discrete(cls, range_expression: Union[str, List], purl_type: str, all_versions: List):
        """
        Return NormalizedVersionRanges computed from discrete version range expression.
        Discrete range_expression example::
            ["1.5","3.1.2","3.1-beta"]
        """
        version_map = cls.get_version_map(all_versions, purl_type)
        reverse_version_map = {value: key for key, value in version_map.items()}

        item = range_expression if isinstance(range_expression, str) else " ".join(range_expression)
        discrete_versions = re.split("[ ,\n]+", item)

        rank_list = []
        for version in discrete_versions:
            try:
                rank_int = version_map[strip_leading_v(version)]
                rank_list.append(rank_int)
            except KeyError:
                pass

        total_span = Span(rank_list)

        version_ranges = cls.get_version_range_from_span(total_span, purl_type, reverse_version_map)
        return cls(version_ranges)


def strip_leading_v(version: str):
    """
    Return version without leading v.
    """
    if not version.startswith("v"):
        return version
    return version[1:]


VERSIONS_BY_PACKAGE_TYPE = {
    "alpine": AlpineLinuxVersion,
    "alpm": ArchLinuxVersion,
    "apache": SemverVersion,
    "cargo": SemverVersion,
    # "cocoapods": None,
    "composer": ComposerVersion,
    # "conan": None,
    # "conda": None,
    # "cran": None,
    "deb": DebianVersion,
    "ebuild": GentooVersion,
    "gem": RubygemsVersion,
    "generic": GenericVersion,
    "github": SemverVersion,
    "golang": GolangVersion,
    "hex": SemverVersion,
    "mattermost": SemverVersion,
    "maven": MavenVersion,
    "mozilla": SemverVersion,
    "nginx": NginxVersion,
    "npm": SemverVersion,
    "nuget": NugetVersion,
    "openssl": OpensslVersion,
    "pypi": PypiVersion,
    "rpm": RpmVersion,
    # "swift": None,
}

OPERATOR_BY_COMPRATOR = {
    "<": operator.lt,
    ">": operator.gt,
    "=": operator.eq,
    "<=": operator.le,
    ">=": operator.ge,
    "==": operator.eq,
    "!=": operator.ne,
    ")": operator.lt,
    "]": operator.le,
    "(": operator.gt,
    "[": operator.ge,
}
