# -*- coding: utf-8 -*-
#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import pytest

from univers.version_range import VersionRange


@pytest.mark.parametrize(
    "vers",
    [
        "VERS:npm/1.0.0",
        "vers:NPM/1.0.0",
        "vers:npm/>=1.0.0| <2.0.0",
        "vers:npm/",
        "vers:npm/|>=1.0.0",
        "vers:npm/>=1.0.0|",
        "vers:npm/>=1.0.0||<2.0.0",
        "vers:npm/=1.0.0",
        "vers:npm/==1.0.0",
        "vers:npm/>=2.0.0|<1.0.0",
        "vers:npm/1.0.0|1.0.0",
        "vers:npm/>=1.0.0|>=2.0.0",
        "vers:datetime/2024-01-01T00:00:00Z|>2024-01-01T00:00:00Z",
    ],
)
def test_from_string_rejects_noncanonical_vers(vers):
    with pytest.raises(ValueError):
        VersionRange.from_string(vers)


def test_from_string_accepts_canonical_range():
    vers = VersionRange.from_string("vers:npm/>=1.0.0|<2.0.0")

    assert vers.to_string() == "vers:npm/>=1.0.0|<2.0.0"


def test_from_string_accepts_bare_version_as_implicit_equality():
    vers = VersionRange.from_string("vers:npm/1.0.0")

    assert vers.to_string() == "vers:npm/1.0.0"


def test_from_string_decodes_percent_encoding_once():
    vers = VersionRange.from_string("vers:npm/1.0%252F0")

    assert vers.to_dict()["constraints"] == [{"comparator": "=", "version": "1.0%2F0"}]
    vers = VersionRange.from_string("vers:lexicographic/1.0%252F0")
    assert vers.to_string() == "vers:lexicographic/1.0%252F0"


def test_from_string_decodes_percent_encoded_space():
    vers = VersionRange.from_string("vers:lexicographic/1%202")

    assert vers.to_dict()["constraints"] == [{"comparator": "=", "version": "1 2"}]
    assert vers.to_string() == "vers:lexicographic/1%202"


def test_from_string_decodes_reserved_characters_in_versions():
    vers = VersionRange.from_string("vers:lexicographic/1%3E2")

    assert vers.to_dict()["constraints"] == [{"comparator": "=", "version": "1>2"}]
    assert vers.to_string() == "vers:lexicographic/1%3E2"


@pytest.mark.parametrize(
    "vers",
    [
        "vers:lexicographic/1 2",
        "vers:lexicographic/1%092",
        "vers:npm/1.0%2G0",
        "vers:lexicographic/1%2f2",
        "vers:lexicographic/1>2",
        "vers:datetime/2024-01-01t00:00:00z",
        "vers:datetime/2024-01-01T00%3A00%3A00Z",
        "vers:datetime/2024-01-01T00:00:00%ZZ",
        "vers:datetime/2024-01-01T00%3a00%3a00Z",
    ],
)
def test_from_string_rejects_noncanonical_version_encoding(vers):
    with pytest.raises(ValueError):
        VersionRange.from_string(vers)


def test_datetime_range_serializes_canonical_version():
    vers = "vers:datetime/2024-01-01T00:00:00Z"

    assert VersionRange.from_string(vers).to_string() == vers


def test_from_string_always_validates_constraints():
    with pytest.raises(ValueError):
        VersionRange.from_string("vers:npm/>=1.0.0|>=2.0.0", validate=False)
