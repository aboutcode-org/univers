#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import json
from unittest import TestCase

import pytest

from univers.version_constraint import VersionConstraint
from univers.version_range import RANGE_CLASS_BY_SCHEMES
from univers.version_range import ConanVersionRange
from univers.version_range import GemVersionRange
from univers.version_range import InvalidVersionRange
from univers.version_range import MattermostVersionRange
from univers.version_range import NpmVersionRange
from univers.version_range import NugetVersionRange
from univers.version_range import OpensslVersionRange
from univers.version_range import PypiVersionRange
from univers.version_range import VersionRange
from univers.version_range import build_range_from_snyk_advisory_string
from univers.version_range import from_gitlab_native
from univers.versions import InvalidVersion
from univers.versions import LexicographicVersion
from univers.versions import NugetVersion
from univers.versions import OpensslVersion
from univers.versions import PypiVersion
from univers.versions import RubygemsVersion
from univers.versions import SemverVersion


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
        vers = "vers:pypi/0.0.2|0.0.6|>=3.0.0|0.0.1|0.0.4|0.0.5|0.0.3"
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

    def test_VersionRange_contains_filterd_constraint_edge_case(self):
        vers = "vers:pypi/<=1.3.0|3.0.0"
        version_range = VersionRange.from_string(vers)
        assert version_range.contains(PypiVersion("1.0.0"))

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
        from univers.versions import NginxVersion

        assert NginxVersion("1.0.0") in VersionRange.from_string("vers:nginx/*")

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

    def test_NpmVersionRange_from_native_with_prerelease_carate_range(self):
        npm_range = "^1.2.3-beta.1"
        expected = NpmVersionRange(
            constraints=(
                VersionConstraint(comparator=">=", version=SemverVersion(string="1.2.3-beta.1")),
                VersionConstraint(comparator="<", version=SemverVersion(string="2.0.0")),
            )
        )
        version_range = NpmVersionRange.from_native(npm_range)
        assert version_range == expected

    def test_NpmVersionRange_from_native_with_prerelease_carate_range_wihtout_major(self):
        npm_range = "^0.2.1-beta"
        expected = NpmVersionRange(
            constraints=(
                VersionConstraint(comparator=">=", version=SemverVersion(string="0.2.1-beta")),
                VersionConstraint(comparator="<", version=SemverVersion(string="0.3.0")),
            )
        )
        version_range = NpmVersionRange.from_native(npm_range)
        assert version_range == expected

    def test_NpmVersionRange_from_native_with_prerelease_carate_range_wihtout_major_and_minor(self):
        npm_range = "^0.0.2-beta"
        expected = NpmVersionRange(
            constraints=(
                VersionConstraint(comparator=">=", version=SemverVersion(string="0.0.2-beta")),
                VersionConstraint(comparator="<", version=SemverVersion(string="0.0.3")),
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

    def test_OpensslVersionRange_from_versions(self):
        sequence = ["3.0.0", "1.0.1b", "3.0.2", "0.9.7a ", "1.1.1ka"]
        expected = OpensslVersionRange(
            constraints=(
                VersionConstraint(comparator="=", version=OpensslVersion(string="0.9.7a")),
                VersionConstraint(comparator="=", version=OpensslVersion(string="1.0.1b")),
                VersionConstraint(comparator="=", version=OpensslVersion(string="1.1.1ka")),
                VersionConstraint(comparator="=", version=OpensslVersion(string="3.0.0")),
                VersionConstraint(comparator="=", version=OpensslVersion(string="3.0.2")),
            )
        )
        version_range = OpensslVersionRange.from_versions(sequence)
        assert version_range == expected

    def test_nuget_version_range(self):
        nuget_range = "[1.0.0, 2.0.0)"
        expected = NugetVersionRange(
            constraints=(
                VersionConstraint(comparator=">=", version=NugetVersion(string="1.0.0")),
                VersionConstraint(comparator="<", version=NugetVersion(string="2.0.0")),
            )
        )
        version_range = NugetVersionRange.from_native(nuget_range)
        assert version_range == expected
        assert version_range.to_string() == "vers:nuget/>=1.0.0|<2.0.0"


VERSION_RANGE_TESTS_BY_SCHEME = {
    "nginx": ["0.8.40+", "0.7.52-0.8.39", "0.9.10", "1.5.0+, 1.4.1+"],
    "npm": [
        "^1.2.9",
        "~3.8.2",
        "5.0.0 - 7.2.3",
        "2.1.0 || 2.6.0",
        "1.1.2 1.2.2",
        "<=2.1.0 >=1.1.0",
        "1.2.x",
    ],
    "openssl": ["1.1.1ak", "1.1.0", "3.0.2", "3.0.1, 0.9.7a", "1.0.2ck, 3.1.2"],
    "pypi": [">= 1.0", "<2.1.0", "!=5"],
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


@pytest.mark.parametrize(
    "range, will_pass, expected",
    [
        (" ~= 0.9", False, "Unsupported PyPI version constraint operator"),
        ("~= 1.3", False, "Unsupported PyPI version constraint operator"),
        (" >= 1.0", True, "vers:pypi/>=1.0"),
        (" != 1.3.4.*", False, "Unsupported PyPI version"),
        ("< 2.0", True, "vers:pypi/<2.0"),
        ("~= 1.3.4.*", False, ""),
        ("==1. *", False, "Unsupported PyPI version"),
        ("==1.3.4 ) (", False, "Unsupported character"),
        ("===1.0", False, "Unsupported PyPI version"),
    ],
)
def test_PypiVersionRange_raises_ivr_for_unsupported_and_invalid_ranges(range, will_pass, expected):
    if not will_pass:
        try:
            PypiVersionRange.from_native(range)
            raise Exception("Exception not raised")
        except InvalidVersionRange as ivre:
            assert expected in str(ivre)
    else:
        assert expected == str(PypiVersionRange.from_native(range))


@pytest.mark.parametrize("test_case", json.load(open("./tests/data/pypi_gitlab.json")))
def test_pypi_gitlab_version_range_parse(test_case):
    result = from_gitlab_native(
        gitlab_scheme=test_case["scheme"],
        string=test_case["gitlab_native"],
    )
    assert str(result) == test_case["expected_vers"]


@pytest.mark.parametrize("test_case", json.load(open("./tests/data/conan_advisory.json")))
def test_conan_gitlab_version_range_parse(test_case):
    if test_case["expected_vers"] is None:
        with pytest.raises(InvalidVersion):
            ConanVersionRange.from_native(string=test_case["native"])
        return
    result = from_gitlab_native(
        gitlab_scheme=test_case["gitlab_scheme"],
        string=test_case["native"],
    )
    assert str(result) == test_case["expected_vers"]


@pytest.mark.parametrize("test_case", json.load(open("./tests/data/npm_gitlab.json")))
def test_npm_gitlab_version_range_parse(test_case):
    result = from_gitlab_native(
        gitlab_scheme=test_case["scheme"],
        string=test_case["gitlab_native"],
    )
    assert str(result) == test_case["expected_vers"]


@pytest.mark.parametrize("test_case", json.load(open("./tests/data/gem_gitlab.json")))
def test_gem_gitlab_version_range_parse(test_case):
    result = from_gitlab_native(
        gitlab_scheme=test_case["scheme"],
        string=test_case["gitlab_native"],
    )
    assert str(result) == test_case["expected_vers"]


@pytest.mark.parametrize("test_case", json.load(open("./tests/data/go_gitlab.json")))
def test_golang_gitlab_version_range_parse(test_case):
    result = from_gitlab_native(
        gitlab_scheme=test_case["scheme"],
        string=test_case["gitlab_native"],
    )
    assert str(result) == test_case["expected_vers"]


@pytest.mark.parametrize("test_case", json.load(open("./tests/data/composer_gitlab.json")))
def test_composer_gitlab_version_range_parse(test_case):
    result = from_gitlab_native(
        gitlab_scheme=test_case["scheme"],
        string=test_case["gitlab_native"],
    )
    assert str(result) == test_case["expected_vers"]


@pytest.mark.parametrize("test_case", json.load(open("./tests/data/npm_advisory.json")))
def test_npm_advisory_version_range_parse(test_case):
    result = NpmVersionRange.from_native(
        string=test_case["npm_native"],
    )
    assert str(result) == test_case["expected_vers"]


@pytest.mark.parametrize("test_case", json.load(open("./tests/data/conan_advisory.json")))
def test_conan_advisory_version_range_parse(test_case):
    if test_case["expected_vers"] is None:
        with pytest.raises(InvalidVersion):
            ConanVersionRange.from_native(string=test_case["native"])
        return
    result = ConanVersionRange.from_native(
        string=test_case["native"],
    )
    assert str(result) == test_case["expected_vers"]


def test_invert():
    vers_with_equal_operator = VersionRange.from_string("vers:gem/1.0")
    assert str(vers_with_equal_operator.invert()) == "vers:gem/!=1.0"
    assert VersionRange.from_string("vers:gem/!=1.0").invert() == vers_with_equal_operator

    vers_with_less_than_operator = VersionRange.from_string("vers:gem/<1.0")
    assert str(vers_with_less_than_operator.invert()) == "vers:gem/>=1.0"
    assert VersionRange.from_string("vers:gem/>=1.0").invert() == vers_with_less_than_operator

    vers_with_greater_than_operator = VersionRange.from_string("vers:gem/>1.0")
    assert str(vers_with_greater_than_operator.invert()) == "vers:gem/<=1.0"
    assert VersionRange.from_string("vers:gem/<=1.0").invert() == vers_with_greater_than_operator

    vers_with_complex_constraints = VersionRange.from_string("vers:gem/<=1.0|>=3.0|<4.0|!=5.0")
    assert str(vers_with_complex_constraints.invert()) == "vers:gem/>1.0|<3.0|>=4.0|5.0"

    vers_with_star_operator = VersionRange.from_string("vers:gem/*")
    assert vers_with_star_operator.invert() == None


def test_mattermost_version_range():
    assert MattermostVersionRange(
        constraints=[
            VersionConstraint(comparator="=", version=SemverVersion("5.0")),
        ]
    ) == VersionRange.from_string("vers:mattermost/5.0")

    assert MattermostVersionRange(
        constraints=[
            VersionConstraint(comparator=">=", version=SemverVersion("5.0")),
        ]
    ) == VersionRange.from_string("vers:mattermost/>=5.0")


def test_build_range_from_snyk_advisory_string():
    expression = [">=4.0.0, <4.0.10", ">7.0.0, <8.0.1"]
    vr = build_range_from_snyk_advisory_string("pypi", expression)
    expected = "vers:pypi/>=4.0.0|<4.0.10|>7.0.0|<8.0.1"

    assert str(vr) == expected


def test_build_range_from_snyk_advisory_string_bracket():
    expression = ["[3.0.0,3.1.25)", "[1.0.0,1.0.5)"]
    vr = build_range_from_snyk_advisory_string("nuget", expression)
    expected = "vers:nuget/>=1.0.0|<1.0.5|>=3.0.0|<3.1.25"

    assert str(vr) == expected


def test_build_range_from_snyk_advisory_string_spaced():
    expression = [">=4.1.0 <4.4.1", ">2.1.0 <=3.2.7"]
    vr = build_range_from_snyk_advisory_string("composer", expression)
    expected = "vers:composer/>2.1.0|<=3.2.7|>=4.1.0|<4.4.1"

    assert str(vr) == expected


def test_version_range_normalize_case1():
    known_versions = ["4.0.0", "3.0.0", "1.0.0", "2.0.0", "1.3.0", "1.1.0", "1.2.0"]

    vr = VersionRange.from_string("vers:pypi/<=1.1.0|>=1.2.0|<=1.3.0|3.0.0")
    nvr = vr.normalize(known_versions=known_versions)

    assert str(nvr) == "vers:pypi/>=1.0.0|<=1.3.0|3.0.0"


def test_version_range_normalize_case2():
    known_versions = ["4.0.0", "3.0.0", "1.0.0", "2.0.0", "1.3.0", "1.1.0", "1.2.0"]

    vr = VersionRange.from_string("vers:pypi/<=1.3.0|3.0.0")
    nvr = vr.normalize(known_versions=known_versions)

    assert str(nvr) == "vers:pypi/>=1.0.0|<=1.3.0|3.0.0"


def test_version_range_normalize_case3():
    known_versions = ["4.0.0", "3.0.0", "1.0.0", "2.0.0", "1.3.0", "1.1.0", "1.2.0"]

    vr = VersionRange.from_string("vers:pypi/<2.0.0|3.0.0")
    nvr = vr.normalize(known_versions=known_versions)

    assert str(nvr) == "vers:pypi/>=1.0.0|<=1.3.0|3.0.0"


def test_version_range_lexicographic():
    assert LexicographicVersion("1.2.3") in VersionRange.from_string(
        "vers:lexicographic/<1.2.4|>0.9"
    )
    assert LexicographicVersion(-123) in VersionRange.from_string("vers:lexicographic/<~")
    assert LexicographicVersion(None) in VersionRange.from_string("vers:lexicographic/*")
    assert LexicographicVersion("ABC") in VersionRange.from_string("vers:lexicographic/>abc|<=None")
