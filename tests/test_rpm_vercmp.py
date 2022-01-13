#
# Copyright (c) nexB Inc. and others
# Copyright (c) SAS Institute Inc.
# SPDX-License-Identifier: Apache-2.0
# this has been significantly modified from the original
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

import io
import os
import re
import unittest

from univers import rpm as vercmp

get_vercmp_test = re.compile(
    r"(.*)" r"RPMVERCMP\(" r"([^, ]*) *, *" r"([^, ]*) *, *" r"([^\)]*)" r"\).*"
).match


def parse_rpmvercmp_tests(fobj, with_buggy_comparisons=True):
    """
    Yield triples (version1, version2, comparison result) describing the RPM
    version comparison tests found in the rpmvercmp.at test file-like  object at
    ``fobj`` Optionally include "buggy" upstream tests.
    """
    for line in fobj:
        line = line.strip()
        if not line:
            continue
        if not with_buggy_comparisons and line.startswith("dnl"):
            continue
        match = get_vercmp_test(line)
        if not match:
            continue
        yield match.group(2), match.group(3), int(match.group(4))


class ParserTest(unittest.TestCase):
    def test_parse_without_buggy(self):
        fobj = io.StringIO(
            """
bla
bla
RPMVERCMP(1, 2, -1)
dnl RPMVERCMP(1a, 1b, -1)
"""
        )
        parser = parse_rpmvercmp_tests(fobj, with_buggy_comparisons=False)
        expected = [("1", "2", -1)]
        assert list(parser) == expected

    def test_parse_with_buggy(self):
        fobj = io.StringIO(
            """
bla
bla
RPMVERCMP(1, 2, -1)
dnl RPMVERCMP(1a, 1b, -1)
"""
        )
        parser = parse_rpmvercmp_tests(fobj, with_buggy_comparisons=True)
        expected = [("1", "2", -1), ("1a", "1b", -1)]
        assert list(parser) == expected


class VersionCompareTest(unittest.TestCase):
    pass


def create_test_function(ver1, ver2, expected, name):
    """
    Return a test function closed on test arguments.
    """

    def test_rpm_version(self):
        print(f"testing (ver1={ver1}, ver2={ver2}, expected=expected{expected}")
        result = vercmp.vercmp(ver1, ver2)
        if result != expected:
            assert result == (expected, ver1, ver2)

    test_rpm_version.__name__ = name
    return test_rpm_version


def get_tests():
    """
    Yield test function from rpmvercmp.at data.
    """
    test_file = os.path.join(os.path.dirname(__file__), "data", "rpmvercmp.at")

    with io.open(test_file, encoding="utf-8") as rpmtests:
        tests = list(parse_rpmvercmp_tests(rpmtests, with_buggy_comparisons=True))
        for test_count, (ver1, ver2, expected) in enumerate(tests, 1):
            name = f"test_rpm_version_{test_count}"
            yield create_test_function(ver1, ver2, expected, name)

    # Make sure we still test something, in case the m4 file drops
    # content this will fail the test
    assert test_count > 20


def build_tests():
    """
    Create tests from rpmvercmp.at data and attach them to a test class.
    """
    for i, test_func in enumerate(get_tests()):
        name = f"test_rpm_version_{i}"
        setattr(VersionCompareTest, name, test_func)


build_tests()
