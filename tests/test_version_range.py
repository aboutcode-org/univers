#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from unittest import TestCase
import pytest

from univers.version_constraint import VersionConstraint
from univers.version_range import GemVersionRange
from univers.version_range import InvalidVersionRange
from univers.version_range import PypiVersionRange
from univers.version_range import VersionRange
from univers.version_range import RANGE_CLASS_BY_SCHEMES
from univers.version_range import NpmVersionRange
from univers.version_range import OpensslVersionRange
from univers.versions import PypiVersion
from univers.versions import RubygemsVersion
from univers.versions import SemverVersion
from univers.versions import OpensslVersion


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

    def test_VersionRange_pypi_does_not_contain_basic(self):
        vers = "vers:pypi/0.0.2|0.0.6|>=0.0.0|0.0.1|0.0.4|0.0.5|0.0.3"
        version_range = VersionRange.from_string(vers)
        assert not version_range.contains(PypiVersion("2.0.3"))

    def test_VersionRange_does_not_contain_version_after_range(self):
        vers = "vers:pypi/>=1.0.0|<=2.0.0"
        version_range = VersionRange.from_string(vers)
        assert not version_range.contains(PypiVersion("2.0.3"))

    def test_VersionRange_does_not_contain_version_before_range(self):
        vers = "vers:pypi/>=1.0.0|<=2.0.0"
        version_range = VersionRange.from_string(vers)
        assert not version_range.contains(PypiVersion("0.0.9"))

    def test_VersionRange_does_not_contain_version_in_between(self):
        vers = "vers:pypi/<=1.0.0|>=2.0.0"
        version_range = VersionRange.from_string(vers)
        assert not version_range.contains(PypiVersion("1.5"))

    def test_VersionRange_does_not_contain_version_excluded(self):
        vers = "vers:pypi/>=3.0.0|!=2.0.3"
        version_range = VersionRange.from_string(vers)
        assert not version_range.contains(PypiVersion("2.0.3"))

    def test_VersionRange_contains_version_after(self):
        version_range = VersionRange.from_string("vers:pypi/>0.0.2")
        assert PypiVersion("0.0.3") in version_range

    def test_VersionRange_contains_version_before(self):
        version_range = VersionRange.from_string("vers:pypi/<0.0.2")
        assert PypiVersion("0.0.0.1") in version_range

    def test_VersionRange_contains_version_included(self):
        vers = "vers:pypi/>=3.0.0|2.0.3"
        version_range = VersionRange.from_string(vers)
        assert version_range.contains(PypiVersion("2.0.3"))

    def test_VersionRange_contains_version_in_between(self):
        vers = "vers:pypi/>=1.0.0|<=2.0.0"
        version_range = VersionRange.from_string(vers)
        assert version_range.contains(PypiVersion("1.5"))

    def test_VersionRange_from_string_pypi(self):
        vers = "vers:pypi/0.0.2|0.0.6|0.0.0|0.0.1|0.0.4|0.0.5|0.0.3"
        version_range = VersionRange.from_string(vers)
        assert version_range.scheme == "pypi"
        # note the sorting taking place
        expected = (
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.0")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.1")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.2")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.3")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.4")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.5")),
            VersionConstraint(comparator="=", version=PypiVersion(string="0.0.6")),
        )
        assert version_range.constraints == expected
        # note the sorting taking place
        assert str(version_range) == "vers:pypi/0.0.0|0.0.1|0.0.2|0.0.3|0.0.4|0.0.5|0.0.6"

        version_range1 = VersionRange.from_string(vers, simplify=False, validate=True)
        assert version_range1.constraints == expected

        version_range2 = VersionRange.from_string(vers, simplify=True, validate=False)
        assert version_range2.constraints == expected

        version_range3 = VersionRange.from_string(vers, simplify=True, validate=True)
        assert version_range3.constraints == expected

    def test_VersionRange_from_string_pypi_complex_simplify(self):
        vers = "vers:pypi/>0.0.0|>=0.0.1|0.0.2|<0.0.3|0.0.4|<0.0.5|>=0.0.6"
        version_range = VersionRange.from_string(vers, simplify=True)
        assert str(version_range) == "vers:pypi/>0.0.0|<0.0.5|>=0.0.6"
        try:
            version_range = VersionRange.from_string(vers, validate=True)
            raise Exception(f"Exception not raised: {vers}")
        except ValueError:
            pass
        version_range = VersionRange.from_string(vers, validate=True, simplify=True)
        assert str(version_range) == "vers:pypi/>0.0.0|<0.0.5|>=0.0.6"

    def test_VersionRange_from_string_pypi_complex_simplify_and_validate(self):
        vers = "vers:pypi/>0.0.0|>=0.0.1|0.0.2|0.0.3|0.0.4|<0.0.5|>=0.0.6|!=0.8"
        version_range = VersionRange.from_string(vers, simplify=True)
        assert str(version_range) == "vers:pypi/>0.0.0|<0.0.5|>=0.0.6|!=0.8"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)

    def test_VersionRange_from_string_pypi_complex_simplify2(self):
        vers = (
            "vers:pypi/>0.0.0|>=0.0.1|>=0.0.1|0.0.2|0.0.3|0.0.4|<0.0.5|<=0.0.6|!=0.7|8.0|>12|<15.3"
        )
        version_range = VersionRange.from_string(vers, simplify=True)
        assert str(version_range) == "vers:pypi/>0.0.0|<=0.0.6|!=0.7|8.0|>12|<15.3"

    def test_VersionRange_from_string_pypi_simple_cases(self):
        vers = "vers:pypi/>0.0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/>=0.0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/<0.0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/<=0.0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/0.0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/!=0.0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/*"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

    def test_VersionRange_from_string_pypi_two_cases(self):
        vers = "vers:pypi/>0.0.1|<0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/>=0.0.1|<0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/<0.0.1|>0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/<=0.0.1|>0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/0.0.1|>0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

        vers = "vers:pypi/!=0.0.1|>0.1"
        version_range = VersionRange.from_string(vers, simplify=True, validate=True)
        assert str(version_range) == vers

    def test_GemVersionRange_from_native_range_with_pessimistic_operator(self):
        gem_range = "~>2.0.8"
        version_range = GemVersionRange.from_native(gem_range)
        assert version_range.to_string() == "vers:gem/>=2.0.8|<2.1"
        assert version_range.constraints == (
            VersionConstraint(comparator=">=", version=RubygemsVersion(string="2.0.8")),
            VersionConstraint(comparator="<", version=RubygemsVersion(string="2.1")),
        )

    def test_VersionRange_contains_works_for_star_range(self):
        from univers.versions import SemverVersion

        assert SemverVersion("1.0.0") in VersionRange.from_string("vers:nginx/*")

    def test_PypiVersionRange_raises_ivr_for_unsupported_ranges(self):
        try:
            PypiVersionRange.from_native(
                "~= 0.9, >= 1.0, != 1.3.4.*, < 2.0, ~= 1.3.4.*, ===1.0, ==1.*"
            )
            raise Exception("Exception not raised")
        except InvalidVersionRange as ivre:
            assert str(ivre).startswith("Unsupported character")

    def test_PypiVersionRange_raises_ivr_for_invalid_ranges(self):
        try:
            PypiVersionRange.from_native("~= 1.3, ===1.0, ==1.*")
            raise Exception("Exception not raised")
        except InvalidVersionRange as ivre:
            assert str(ivre).startswith("Unsupported character")

    def test_NpmVersionRange_from_native_with_compatible_with_version_operator(self):
        npm_range = "^1.2.9"
        expected = NpmVersionRange(
            constraints=(
                VersionConstraint(comparator=">=", version=SemverVersion(string="1.2.9")),
                VersionConstraint(comparator="<", version=SemverVersion(string="2.0.0")),
            )
        )
        version_range = NpmVersionRange.from_native(npm_range)
        assert version_range == expected

    def test_NpmVersionRange_from_native_with_approximately_equal_to_operator(self):
        npm_range = "~3.8.2"
        expected = NpmVersionRange(
            constraints=(
                VersionConstraint(comparator=">=", version=SemverVersion(string="3.8.2")),
                VersionConstraint(comparator="<", version=SemverVersion(string="3.9.0")),
            )
        )
        version_range = NpmVersionRange.from_native(npm_range)
        assert version_range == expected

    def test_OpensslVersionRange_from_native_single_legacy(self):
        openssl_range = "0.9.8j"
        expected = OpensslVersionRange(
            constraints=(
                VersionConstraint(comparator="=", version=OpensslVersion(string="0.9.8j")),
            )
        )
        version_range = OpensslVersionRange.from_native(openssl_range)
        assert version_range == expected

    def test_OpensslVersionRange_from_native_single_new_semver(self):
        openssl_range = "3.0.1"
        expected = OpensslVersionRange(
            constraints=(VersionConstraint(comparator="=", version=OpensslVersion(string="3.0.1")),)
        )
        version_range = OpensslVersionRange.from_native(openssl_range)
        assert version_range == expected

    def test_OpensslVersionRange_from_native_mixed(self):
        openssl_range = "3.0.0, 1.0.1b"
        expected = OpensslVersionRange(
            constraints=(
                VersionConstraint(comparator="=", version=OpensslVersion(string="1.0.1b")),
                VersionConstraint(comparator="=", version=OpensslVersion(string="3.0.0")),
            )
        )
        version_range = OpensslVersionRange.from_native(openssl_range)
        assert version_range == expected


VERSION_RANGE_TESTS_BY_SCHEME = {
    "nginx": ["0.8.40+", "0.7.52-0.8.39", "0.9.10", "1.5.0+, 1.4.1+"],
    "npm": ["^1.2.9", "~3.8.2", "5.0.0 - 7.2.3", "2.1 || 2.6", "1.1.2 1.2.2", "<=2.1 >=1.1"],
    "openssl": ["1.1.1ak", "1.1.0", "3.0.2", "3.0.1, 0.9.7a", "1.0.2ck, 3.1.2"],
}


@pytest.mark.xfail(reason="Not all schemes are implemented yet")
def test_all_schemes_are_tested_for_round_tripping():
    untested_schemes = []
    for scheme in RANGE_CLASS_BY_SCHEMES:
        if scheme not in VERSION_RANGE_TESTS_BY_SCHEME:
            untested_schemes.append(scheme)
    assert not untested_schemes


@pytest.mark.parametrize(
    "scheme, native_ranges",
    VERSION_RANGE_TESTS_BY_SCHEME.items(),
)
def test_from_native_and_from_string_round_trip(scheme, native_ranges):

    range_class = RANGE_CLASS_BY_SCHEMES[scheme]
    for rng in native_ranges:
        from_native = range_class.from_native(rng)
        from_string = range_class.from_string(from_native.to_string())
        assert from_native == from_string
