#
# Copyright [2017] The Climate Corporation (https://climate.com)
# https://github.com/TheClimateCorporation/python-dpkg
# original author: Nathan J. Meh

# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debian_inspector/

# SPDX-License-Identifier: Apache-2.0
# this has been significantly modified from the original
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from unittest import TestCase

import pytest

import univers.debian as version
from univers.debian import compare_strings
from univers.debian import compare_versions
from univers.debian import Version

"""
Parse, compare and sort Debian package versions.

This has been substantially modified from python-dpkg to extract the version
comparison code.
"""


def get_non_digit_prefix(s):
    val = version.get_non_digit_prefix(list(s))
    return "".join(val)


def get_digit_prefix(s):
    return version.get_digit_prefix(list(s))


class DebianVersionTest(TestCase):
    def test_Version_from_string_epoch(self):
        assert Version.from_string("0").epoch == 0
        assert Version.from_string("0:0").epoch == 0
        assert Version.from_string("1:0").epoch == 1

    def test_Version_from_string_validates(self):
        self.assertRaises(ValueError, Version.from_string, "a")
        self.assertRaises(ValueError, Version.from_string, "1a:0")
        self.assertRaises(ValueError, Version.from_string, "0:a.0.0-foo")

    def test_Version_from_string_tuples(self):
        assert Version.from_string("00").tuple() == (0, "00", "0")
        assert Version.from_string("00-00").tuple() == (0, "00", "00")
        assert Version.from_string("0:0").tuple() == (0, "0", "0")
        assert Version.from_string("0:0-0").tuple() == (0, "0", "0")
        assert Version.from_string("0:0.0").tuple() == (0, "0.0", "0")
        assert Version.from_string("0:0.0-0").tuple() == (0, "0.0", "0")
        assert Version.from_string("0:0.0-00").tuple() == (0, "0.0", "00")

    def test_get_non_digit_prefix(self):
        assert get_non_digit_prefix("") == ""
        assert get_non_digit_prefix("0") == ""
        assert get_non_digit_prefix("00") == ""
        assert get_non_digit_prefix("0a") == ""
        assert get_non_digit_prefix("a") == "a"
        assert get_non_digit_prefix("a0") == "a"
        assert get_non_digit_prefix("aHAD0030") == "aHAD"

    def test_get_digit_prefix(self):
        assert get_digit_prefix("00") == 0
        assert get_digit_prefix("0") == 0
        assert get_digit_prefix("0a") == 0
        assert get_digit_prefix("12a") == 12
        assert get_digit_prefix("a") == 0
        assert get_digit_prefix("a0") == 0
        assert get_digit_prefix("arttr23123") == 0
        assert get_digit_prefix("123sdf") == 123
        assert get_digit_prefix("0123sdf") == 123

    def test_compare_strings(self):
        assert compare_strings("~", ".") == -1
        assert compare_strings("~", "a") == -1
        assert compare_strings("a", ".") == -1
        assert compare_strings("a", "~") == 1
        assert compare_strings(".", "~") == 1
        assert compare_strings(".", "a") == 1
        assert compare_strings(".", ".") == 0
        assert compare_strings("0", "0") == 0
        assert compare_strings("a", "a") == 0

    def test_compare_strings_can_sort(self):
        # taken from
        # http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
        result = sorted(["a", "", "~", "~~a", "~~"], key=version.compare_strings_key)
        expected = ["~~", "~~a", "~", "", "a"]
        assert expected == result

    def test_compare_strings_more(self):
        # note that these are testing a single revision string, not the full
        # upstream+debian version.  IOW, "0.0.9-foo" is an upstream or debian
        # revision onto itself, not an upstream of 0.0.9 and a debian of foo.

        # equals
        assert compare_strings("0", "0") == 0
        assert compare_strings("0", "00") == 0
        assert compare_strings("00.0.9", "0.0.9") == 0
        assert compare_strings("0.00.9-foo", "0.0.9-foo") == 0
        assert compare_strings("0.0.9-1.00foo", "0.0.9-1.0foo") == 0

        # less than
        assert compare_strings("0.0.9", "0.0.10") == -1
        assert compare_strings("0.0.9-foo", "0.0.10-foo") == -1
        assert compare_strings("0.0.9-foo", "0.0.10-goo") == -1
        assert compare_strings("0.0.9-foo", "0.0.9-goo") == -1
        assert compare_strings("0.0.10-foo", "0.0.10-goo") == -1
        assert compare_strings("0.0.9-1.0foo", "0.0.9-1.1foo") == -1

        # greater than
        assert compare_strings("0.0.10", "0.0.9") == 1
        assert compare_strings("0.0.10-foo", "0.0.9-foo") == 1
        assert compare_strings("0.0.10-foo", "0.0.9-goo") == 1
        assert compare_strings("0.0.9-1.0foo", "0.0.9-1.0bar") == 1

    def test_compare_versions(self):
        # "This [the epoch] is a single (generally small) unsigned integer.
        # It may be omitted, in which case zero is assumed."
        assert compare_versions("0.0.0", "0:0.0.0") == 0
        assert compare_versions("0:0.0.0-foo", "0.0.0-foo") == 0
        assert compare_versions("0.0.0-a", "0:0.0.0-a") == 0

        # "The absence of a debian_revision is equivalent to a debian_revision of 0."
        assert compare_versions("0.0.0", "0.0.0-0") == 0
        # tricksy:
        assert compare_versions("0.0.0", "0.0.0-00") == 0

        # combining the above
        assert compare_versions("0.0.0-0", "0:0.0.0") == 0

        # explicitly equal
        assert compare_versions("0.0.0", "0.0.0") == 0
        assert compare_versions("1:0.0.0", "1:0.0.0") == 0
        assert compare_versions("0.0.0-10", "0.0.0-10") == 0
        assert compare_versions("2:0.0.0-1", "2:0.0.0-1") == 0

        # less than
        assert compare_versions("0.0.0-0", "0:0.0.1") == -1
        assert compare_versions("0.0.0-0", "0:0.0.0-a") == -1
        assert compare_versions("0.0.0-0", "0:0.0.0-1") == -1
        assert compare_versions("0.0.9", "0.0.10") == -1
        assert compare_versions("0.9.0", "0.10.0") == -1
        assert compare_versions("9.0.0", "10.0.0") == -1

        assert compare_versions("1.2.3-1~deb7u1", "1.2.3-1") == -1
        assert compare_versions("2.7.4+reloaded2-13ubuntu1", "2.7.4+reloaded2-13+deb9u1") == -1
        assert compare_versions("2.7.4+reloaded2-13", "2.7.4+reloaded2-13+deb9u1") == -1

        # greater than
        assert compare_versions("0.0.1-0", "0:0.0.0") == 1
        assert compare_versions("0.0.0-a", "0:0.0.0-1") == 1
        assert compare_versions("0.0.0-a", "0:0.0.0-0") == 1
        assert compare_versions("0.0.9", "0.0.1") == 1
        assert compare_versions("0.9.0", "0.1.0") == 1
        assert compare_versions("9.0.0", "1.0.0") == 1

        assert compare_versions("1.2.3-1", "1.2.3-1~deb7u1") == 1
        assert compare_versions("2.7.4+reloaded2-13+deb9u1", "2.7.4+reloaded2-13ubuntu1") == 1
        assert compare_versions("2.7.4+reloaded2-13+deb9u1", "2.7.4+reloaded2-13") == 1

        # unicode
        assert compare_versions(u"2:0.0.44-1", u"2:0.0.44-nobin") == -1
        assert compare_versions(u"2:0.0.44-nobin", u"2:0.0.44-1") == 1
        assert compare_versions(u"2:0.0.44-1", u"2:0.0.44-1") == 0

    @pytest.mark.xfail(reason="Not yet supported")
    def test_can_parse_complex_version_is_not_invalid(self):
        Version.from_string("1:1.12_1.12.6-1+deb9u1build0.18.04.1")
