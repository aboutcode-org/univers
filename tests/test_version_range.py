#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import json
from pathlib import Path

import pytest

from tests import SchemaDrivenVersTest
from univers.version_constraint import VersionConstraint
from univers.version_range import PURL_TYPE_BY_GITLAB_SCHEME
from univers.version_range import RANGE_CLASS_BY_SCHEMES
from univers.version_range import DatetimeVersionRange
from univers.version_range import IntdotVersionRange
from univers.version_range import InvalidVersionRange
from univers.version_range import MattermostVersionRange
from univers.version_range import OpensslVersionRange
from univers.version_range import PypiVersionRange
from univers.version_range import VersionRange
from univers.version_range import build_range_from_snyk_advisory_string
from univers.version_range import from_gitlab_native
from univers.versions import DatetimeVersion
from univers.versions import IntdotVersion
from univers.versions import OpensslVersion
from univers.versions import PypiVersion
from univers.versions import SemverVersion
from univers.versions import Version

TEST_DATA_PARENT = Path(__file__).parent / "data" / "schema" / "range"
TEST_DATA_PARENT_GITLAB = TEST_DATA_PARENT / "gitlab"

TEST_DATA_COMPOSER_GITLAB_FROM_NATIVE = (
    TEST_DATA_PARENT_GITLAB / "composer_gitlab_range_from_native.json"
)
TEST_DATA_CONAN_GITLAB_FROM_NATIVE = TEST_DATA_PARENT_GITLAB / "conan_gitlab_range_from_native.json"
TEST_DATA_GEM_GITLAB_FROM_NATIVE = TEST_DATA_PARENT_GITLAB / "gem_gitlab_range_from_native.json"
TEST_DATA_GOLANG_GITLAB_FROM_NATIVE = (
    TEST_DATA_PARENT_GITLAB / "golang_gitlab_range_from_native.json"
)
TEST_DATA_NPM_GITLAB_FROM_NATIVE = TEST_DATA_PARENT_GITLAB / "npm_gitlab_range_from_native.json"
TEST_DATA_PYPI_GITLAB_FROM_NATIVE = TEST_DATA_PARENT_GITLAB / "pypi_gitlab_range_from_native.json"

TEST_DATA_CONAN_FROM_NATIVE_BASIC = TEST_DATA_PARENT / "conan_range_from_native_basic.json"
TEST_DATA_CONAN_FROM_NATIVE = TEST_DATA_PARENT / "conan_range_from_native.json"
TEST_DATA_GEM_FROM_NATIVE = TEST_DATA_PARENT / "gem_range_from_native.json"
TEST_DATA_NGINX_FROM_NATIVE = TEST_DATA_PARENT / "nginx_range_from_native.json"
TEST_DATA_NPM_FROM_NATIVE = TEST_DATA_PARENT / "npm_range_from_native.json"
TEST_DATA_NUGET_FROM_NATIVE = TEST_DATA_PARENT / "nuget_range_from_native.json"
TEST_DATA_OPENSSL_FROM_NATIVE = TEST_DATA_PARENT / "openssl_range_from_native.json"
TEST_DATA_PYPI_FROM_NATIVE = TEST_DATA_PARENT / "pypi_range_from_native.json"

TEST_DATA_NPM_CONTAINMENT = TEST_DATA_PARENT / "npm_range_containment.json"
TEST_DATA_PYPI_CONTAINMENT = TEST_DATA_PARENT / "pypi_range_containment.json"

TEST_DATA_PYPI_ROUNDTRIP = TEST_DATA_PARENT / "pypi_range_roundtrip.json"


class TestVersionRangeContainment(SchemaDrivenVersTest):
    def containment(self):
        version_range = VersionRange.from_string(self.input["vers"])
        version = version_range.version_class(self.input["version"])
        return version in version_range


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_NPM_CONTAINMENT)))
def test_range_containment(test_case):
    test = TestVersionRangeContainment.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_PYPI_CONTAINMENT)))
def test_range_containment(test_case):
    test = TestVersionRangeContainment.from_data(data=test_case)
    test.assert_result()


class TestVersionRangeRoundtrip(SchemaDrivenVersTest):
    def roundtrip(self):
        return str(VersionRange.from_string(self.input["vers"]))


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_PYPI_ROUNDTRIP)))
def test_pypi_range_roundtrip(test_case):
    test = TestVersionRangeRoundtrip.from_data(data=test_case)
    test.assert_result()


class TestVersionRangeParseNative(SchemaDrivenVersTest):
    def from_native(self):
        range_class = RANGE_CLASS_BY_SCHEMES[self.input["scheme"]]
        return str(range_class.from_native(self.input["native_range"]))


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_CONAN_FROM_NATIVE)))
def test_range_from_native(test_case):
    test = TestVersionRangeParseNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_GEM_FROM_NATIVE)))
def test_npm_range_from_native(test_case):
    test = TestVersionRangeParseNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_NGINX_FROM_NATIVE)))
def test_conan_range_from_native(test_case):
    test = TestVersionRangeParseNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_CONAN_FROM_NATIVE_BASIC)))
def test_conan_range_from_native(test_case):
    test = TestVersionRangeParseNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_CONAN_FROM_NATIVE)))
def test_conan_version_range_parse(test_case):
    avc = TestVersionRangeParseNative.from_data(data=test_case)
    avc.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_OPENSSL_FROM_NATIVE)))
def test_npm_range_from_native(test_case):
    test = TestVersionRangeParseNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_NUGET_FROM_NATIVE)))
def test_npm_range_from_native(test_case):
    test = TestVersionRangeParseNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_PYPI_FROM_NATIVE)))
def test_conan_range_from_native(test_case):
    test = TestVersionRangeParseNative.from_data(data=test_case)
    test.assert_result()


class TestGitlabVersionRangeNative(SchemaDrivenVersTest):
    GITLAB_SCHEME_MAPPING = {v: k for k, v in PURL_TYPE_BY_GITLAB_SCHEME.items()}

    def from_native(self):
        range = from_gitlab_native(
            gitlab_scheme=self.GITLAB_SCHEME_MAPPING[self.input["scheme"]],
            string=self.input["native_range"],
        )
        return str(range)


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_COMPOSER_GITLAB_FROM_NATIVE)))
def test_pypi_gitlab_range_from_native(test_case):
    test = TestGitlabVersionRangeNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_CONAN_GITLAB_FROM_NATIVE)))
def test_conan_gitlab_range_from_native(test_case):
    test = TestGitlabVersionRangeNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_GEM_GITLAB_FROM_NATIVE)))
def test_conan_gitlab_range_from_native(test_case):
    test = TestGitlabVersionRangeNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_GOLANG_GITLAB_FROM_NATIVE)))
def test_gem_gitlab_range_from_native(test_case):
    test = TestGitlabVersionRangeNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_NPM_GITLAB_FROM_NATIVE)))
def test_npm_gitlab_range_from_native(test_case):
    test = TestGitlabVersionRangeNative.from_data(data=test_case)
    test.assert_result()


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA_PYPI_GITLAB_FROM_NATIVE)))
def test_npm_gitlab_range_from_native(test_case):
    test = TestGitlabVersionRangeNative.from_data(data=test_case)
    test.assert_result()


def test_OpensslVersionRange_from_versions():
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


def test_version_range_all():
    all_vers = VersionRange.from_string("vers:all/*")
    assert all_vers.contains(Version("1.2.3"))
    assert PypiVersion("2.0.3") in all_vers
    # test for invalid all range specification
    with pytest.raises(Exception):
        VersionRange.from_string("vers:all/>1.2.3")
    with pytest.raises(Exception):
        VersionRange.from_string("vers:all/*|>1.2.3")


def test_version_range_none():
    none_vers = VersionRange.from_string("vers:none/*")
    assert not none_vers.contains(Version("1.2.3"))
    assert PypiVersion("2.0.3") not in none_vers
    # test for invalid all range specification
    with pytest.raises(Exception):
        VersionRange.from_string("vers:none/!1.2.3")
    with pytest.raises(Exception):
        VersionRange.from_string("vers:none/*|>1.2.3")


def test_version_range_intdot():
    intdot_range = IntdotVersionRange.from_string("vers:intdot/>1.2.3.4")
    assert IntdotVersion("1.3.3") in intdot_range
    assert IntdotVersion("0.3.3") not in intdot_range
    assert IntdotVersion("1.3.3alpha") in intdot_range
    assert IntdotVersion("1.2.2.pre") not in intdot_range
    assert IntdotVersion("1010.23.234203.0") in IntdotVersionRange.from_string("vers:intdot/*")


def test_version_range_datetime():
    assert DatetimeVersion("2021-05-05T01:02:03.1234Z") == DatetimeVersion(
        "2021-05-05T01:02:03.1234Z"
    )
    assert DatetimeVersion("2021-05-05T01:02:03.1234Z") != DatetimeVersion(
        "2022-05-05T01:02:03.1234Z"
    )
    assert DatetimeVersion("2021-05-05T01:02:03.1234Z") <= DatetimeVersion(
        "2022-05-05T01:02:03.1234Z"
    )
    assert DatetimeVersion("2021-05-05T01:02:03.1234Z") >= DatetimeVersion(
        "2020-05-05T01:02:03.1234Z"
    )
    assert DatetimeVersion("2021-05-05T01:02:03.1234Z") > DatetimeVersion(
        "2020-05-05T01:02:03.1234+01:00"
    )
    assert DatetimeVersion("2000-01-01T01:02:03.1234Z") in DatetimeVersionRange.from_string(
        "vers:datetime/*"
    )
    assert DatetimeVersion("2021-05-05T01:02:03Z") in DatetimeVersionRange.from_string(
        "vers:datetime/>2021-01-01T01:02:03.1234Z|<2022-01-01T01:02:03.1234Z"
    )
    datetime_constraints = DatetimeVersionRange(
        constraints=(
            VersionConstraint(
                comparator=">", version=DatetimeVersion(string="2000-01-01T01:02:03Z")
            ),
            VersionConstraint(
                comparator="<", version=DatetimeVersion(string="2002-01-01T01:02:03Z")
            ),
        )
    )
    assert DatetimeVersion("2001-01-01T01:02:03Z") in datetime_constraints
    with pytest.raises(Exception):
        VersionRange.from_string("vers:datetime/2025-08-25")
