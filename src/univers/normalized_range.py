#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.


from typing import List

import attr

from univers.span import Span
from univers.version_constraint import VersionConstraint
from univers.version_range import RANGE_CLASS_BY_SCHEMES
from univers.version_range import VersionRange


@attr.s(frozen=True, order=False, eq=True, hash=True)
class NormalizedVersionRange:
    """
    A normalized_range is a summation of the largest contiguous version ranges.

    For example, for an npm package with the version range "vers:npm/<=2.0.0|>=3.0.0|<3.1.0|4.0.0"
    and available package versions ["1.0.0", "2.0.0", "3.0.0", "3.1.0", "4.0.0"], the normalized range
    would be "vers:npm/>=1.0.0|<=3.0.0|4.0.0".
    """

    normalized_range = attr.ib(type=VersionRange, default=None)

    def __str__(self):
        return str(self.normalized_range)

    @classmethod
    def from_vers(cls, vers_range: VersionRange, all_versions: List):
        """
        Return NormalizedVersionRange computed from vers_range and all the available version of package.
        """
        version_class = vers_range.version_class
        versions = sorted([version_class(i.lstrip("vV")) for i in all_versions])

        bounded_span = None
        total_span = None
        for constraint in vers_range.constraints:
            local_span = get_region(constraint=constraint, versions=versions)

            if bounded_span and constraint.comparator in ("<", "<="):
                local_span = bounded_span.intersection(local_span)
            elif constraint.comparator in (">", ">="):
                bounded_span = local_span
                continue

            total_span = local_span if not total_span else total_span.union(local_span)
            bounded_span = None

        # If '<' or '<=' is the last constraint.
        if bounded_span:
            total_span = bounded_span if not total_span else total_span.union(bounded_span)

        normalized_version_range = get_version_range_from_span(
            span=total_span, purl_type=vers_range.scheme, versions=versions
        )
        return cls(normalized_range=normalized_version_range)


def get_version_range_from_span(span: Span, purl_type: str, versions: List):
    """
    Return VersionRange computed from the span and all the versions available for package.

    For example::
    >>> from univers.versions import SemverVersion as SV
    >>> versions = [SV("1.0"), SV("1.1"), SV("1.2"), SV("1.3")]
    >>> span = Span(0,1).union(Span(3))
    >>> vr = get_version_range_from_span(span, "npm", versions)
    >>> assert str(vr) == "vers:npm/>=1.0.0|<=1.1.0|1.3.0"
    """

    version_range_class = RANGE_CLASS_BY_SCHEMES[purl_type]
    version_constraints = []
    spans = span.subspans()
    for subspan in spans:
        lower_bound = versions[subspan.start]
        upper_bound = versions[subspan.end]
        if lower_bound == upper_bound:
            version_constraints.append(
                VersionConstraint(
                    version=lower_bound,
                )
            )
            continue
        version_constraints.append(VersionConstraint(comparator=">=", version=lower_bound))
        version_constraints.append(
            VersionConstraint(
                comparator="<=",
                version=upper_bound,
            )
        )

    return version_range_class(constraints=version_constraints)


def get_region(constraint: VersionConstraint, versions: List):
    """
    Return a Span representing the region covered by the constraint on
    the given universe of versions.

    For example::
    >>> from univers.versions import SemverVersion as SV
    >>> versions = [SV("1.0"), SV("1.1"), SV("1.2"), SV("1.3")]
    >>> constraint = VersionConstraint(comparator="<", version=SV("1.2"))
    >>> get_region(constraint, versions)
    Span(0, 1)
    """

    try:
        index = 0
        if str(constraint.version) != "0":
            index = versions.index(constraint.version)
    except ValueError as err:
        err.args = (f"'{constraint.version}' doesn't exist in the versions list.",)
        raise

    last_index = len(versions) - 1
    comparator = constraint.comparator

    if comparator == "<":
        return Span(0, index - 1)
    if comparator == ">":
        return Span(index + 1, last_index)
    if comparator == ">=":
        return Span(index, last_index)
    if comparator == "<=":
        return Span(0, index)
    if comparator == "=":
        return Span(index)
    if comparator == "!=":
        return Span(0, last_index).difference(Span(index))
