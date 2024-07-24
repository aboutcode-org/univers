#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from unittest import TestCase

from univers.normalized_range import NormalizedVersionRange
from univers.normalized_range import get_region
from univers.normalized_range import get_version_range_from_span
from univers.span import Span
from univers.version_constraint import VersionConstraint
from univers.version_range import VersionRange
from univers.versions import SemverVersion


class TestNormalizedVersionRange(TestCase):
    purl_type = "pypi"
    all_versions = versions = [
        "1.0.0",
        "1.1.0",
        "1.2.0",
        "1.3.0",
        "2.0.0",
        "3.0.0",
    ]
    versions = [SemverVersion(i) for i in all_versions]

    def test_get_region(self):

        constraint1 = VersionConstraint(comparator="<=", version=SemverVersion("1.0.0"))
        constraint2 = VersionConstraint(comparator="!=", version=SemverVersion("1.1.0"))
        constraint3 = VersionConstraint(comparator=">", version=SemverVersion("1.3.0"))

        assert get_region(constraint=constraint1, versions=self.versions) == Span(0)
        assert get_region(constraint=constraint2, versions=self.versions) == Span(0).union(
            Span(2, 5)
        )
        assert get_region(constraint=constraint3, versions=self.versions) == Span(4, 5)

    def test_get_version_range_from_span(self):
        span1 = Span(1)
        span2 = Span(1, 4)
        span3 = Span(1, 4).intersection(Span(3, 5))
        span4 = Span(0).union(Span(2, 3)).union(Span(5))

        vr1 = get_version_range_from_span(
            span=span1, purl_type=self.purl_type, versions=self.versions
        )
        vr2 = get_version_range_from_span(
            span=span2, purl_type=self.purl_type, versions=self.versions
        )
        vr3 = get_version_range_from_span(
            span=span3, purl_type=self.purl_type, versions=self.versions
        )
        vr4 = get_version_range_from_span(
            span=span4, purl_type=self.purl_type, versions=self.versions
        )

        assert str(vr1) == "vers:pypi/1.1.0"
        assert str(vr2) == "vers:pypi/>=1.1.0|<=2.0.0"
        assert str(vr3) == "vers:pypi/>=1.3.0|<=2.0.0"
        assert str(vr4) == "vers:pypi/1.0.0|>=1.2.0|<=1.3.0|3.0.0"

    def test_NormalizedVersionRange_from_vers(self):
        vr1 = VersionRange.from_string("vers:pypi/<=1.1.0|>=1.2.0|<=1.3.0|3.0.0")
        nvr1 = NormalizedVersionRange.from_vers(vers_range=vr1, all_versions=self.all_versions)

        vr2 = VersionRange.from_string("vers:pypi/>=1.0.0|<=1.1.0|>=1.2.0|<=1.3.0|3.0.0")
        nvr2 = NormalizedVersionRange.from_vers(vers_range=vr2, all_versions=self.all_versions)

        vr3 = VersionRange.from_string("vers:pypi/<=1.3.0|3.0.0")
        nvr3 = NormalizedVersionRange.from_vers(vers_range=vr3, all_versions=self.all_versions)

        vr4 = VersionRange.from_string("vers:pypi/<2.0.0|3.0.0")
        nvr4 = NormalizedVersionRange.from_vers(vers_range=vr4, all_versions=self.all_versions)

        assert str(nvr1) == "vers:pypi/>=1.0.0|<=1.3.0|3.0.0"
        assert str(nvr2) == "vers:pypi/>=1.0.0|<=1.3.0|3.0.0"
        assert str(nvr3) == "vers:pypi/>=1.0.0|<=1.3.0|3.0.0"
        assert str(nvr4) == "vers:pypi/>=1.0.0|<=1.3.0|3.0.0"
