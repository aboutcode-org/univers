#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from unittest import TestCase

from univers.version_constraint import VersionConstraint
from univers.version_range import GemVersionRange
from univers.version_range import PypiVersionRange
from univers.version_range import VersionRange
from univers.versions import PypiVersion
from univers.versions import RubygemsVersion


class TestVersionRange(TestCase):
    def test_VersionRange_afrom_string(self):
        version_range = VersionRange.from_string("vers:pypi/>0.0.2")
        assert version_range == PypiVersionRange(
            constraints=[VersionConstraint(comparator=">", version=PypiVersion(string="0.0.2"))]
        )

    def test_VersionRange_to_string(self):
        vers = "vers:pypi/0.0.2|0.0.6|>=0.0.0|0.0.1|0.0.4|0.0.5|0.0.3"
        version_range = VersionRange.from_string(vers)
        # note the sorting taking place
        assert str(version_range) == "vers:pypi/>=0.0.0|0.0.1|0.0.2|0.0.3|0.0.4|0.0.5|0.0.6"

    def test_VersionRange_not_contains(self):
        vers = "vers:pypi/0.0.2|0.0.6|>=0.0.0|0.0.1|0.0.4|0.0.5|0.0.3"
        version_range = VersionRange.from_string(vers)
        assert not version_range.contains(PypiVersion("2.0.3"))

    def test_VersionRange_contains(self):
        version_range = VersionRange.from_string("vers:pypi/>0.0.2")
        assert PypiVersion("0.0.3") in version_range

    def test_VersionRange_from_string_pypi(self):
        vers = "vers:pypi/0.0.2|0.0.6|0.0.0|0.0.1|0.0.4|0.0.5|0.0.3"
        version_range = VersionRange.from_string(vers)
        assert version_range.scheme == "pypi"
        # note the sorting taking place
        expected = [
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.0")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.1")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.2")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.3")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.4")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.5")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.6")),
        ]
        assert version_range.constraints == expected
        # note the sorting taking place
        assert str(version_range) == "vers:pypi/0.0.0|0.0.1|0.0.2|0.0.3|0.0.4|0.0.5|0.0.6"

        version_range1 = VersionRange.from_string(vers, dedupe=False, validate=True)
        assert version_range1.constraints == expected

        version_range2 = VersionRange.from_string(vers, dedupe=True, validate=False)
        assert version_range2.constraints == expected

        version_range3 = VersionRange.from_string(vers, dedupe=True, validate=True)
        assert version_range3.constraints == expected

    def test_VersionRange_from_string_pypi_complex_dedupe(self):
        vers = "vers:pypi/0.0.2|>=0.0.6|>0.0.0|>=0.0.1|0.0.4|<0.0.5|<0.0.3"
        version_range = VersionRange.from_string(vers, dedupe=True)
        assert str(version_range) == "vers:pypi/>0.0.0|<0.0.5|>=0.0.6"
        try:
            version_range = VersionRange.from_string(vers, validate=True)
            raise Exception(f"Exception not raised: {vers}")
        except ValueError:
            pass
        version_range = VersionRange.from_string(vers, validate=True, dedupe=True)
        assert str(version_range) == "vers:pypi/>0.0.0|<0.0.5|>=0.0.6"

    def test_VersionRange_from_string_pypi_complex_dedupe_and_validate(self):
        vers = "vers:pypi/0.0.2|>=0.0.6|>0.0.0|>=0.0.1|0.0.4|<0.0.5|0.0.3"
        version_range = VersionRange.from_string(vers, dedupe=True)
        assert str(version_range) == "vers:pypi/>0.0.0|<0.0.5|>=0.0.6"

    def test_GemVersionRange_from_native_range_with_pessimistic_operator(self):
        gem_range = "~>2.0.8"
        version_range = GemVersionRange.from_native(gem_range)
        assert version_range.to_string() == "vers:gem/>=2.0.8|<2.1"
        assert version_range.constraints == [
            VersionConstraint(comparator=">=", version=RubygemsVersion(string="2.0.8")),
            VersionConstraint(comparator="<", version=RubygemsVersion(string="2.1")),
        ]
