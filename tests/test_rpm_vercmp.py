#
# Copyright (c) nexB Inc. and others
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# This test script has been extensively modified from the original

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
    ``fobj`` Optionally includ "buggy" upstream tests.
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
    def test_from_rpmtest(self):
        test_file = os.path.join(os.path.dirname(__file__), "test_data", "rpmvercmp.at")

        with io.open(test_file, encoding="utf-8") as rpmtests:
            tests = list(parse_rpmvercmp_tests(rpmtests, with_buggy_comparisons=True))

        for test_count, (ver1, ver2, expected_comparison) in enumerate(tests, 1):
            result = vercmp.vercmp(ver1, ver2)
            if result != expected_comparison:
                assert result == (expected_comparison, ver1, ver2)

        # Make sure we still test something, in case the m4 file drops
        # content this will fail the test
        assert test_count > 20
