#
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

from __future__ import print_function
from __future__ import unicode_literals
import io
import re
import os

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from univers import rpm as vercmp


class ACParser(object):
    R_STMT = re.compile(r"(.*)RPMVERCMP\(([^, ]*) *, *([^, ]*) *, *([^\)]*)\).*")

    def __init__(self, fobj, with_buggy_comparisons=True):
        self.fobj = fobj
        self.with_buggy_comparisons = with_buggy_comparisons

    def __iter__(self):
        for row in self.fobj:
            m = self.R_STMT.match(row)
            if not m:
                continue
            if not self.with_buggy_comparisons:
                if m.group(1).startswith("dnl "):
                    continue
            yield m.group(2), m.group(3), int(m.group(4))


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
        parser = ACParser(fobj, with_buggy_comparisons=False)
        exp = [("1", "2", -1)]
        self.assertEqual(exp, list(parser))

    def test_parse_with_buggy(self):
        fobj = io.StringIO(
            """
bla
bla
RPMVERCMP(1, 2, -1)
dnl RPMVERCMP(1a, 1b, -1)
"""
        )
        parser = ACParser(fobj, with_buggy_comparisons=True)
        exp = [("1", "2", -1), ("1a", "1b", -1)]
        self.assertEqual(exp, list(parser))


class VersionCompareTest(unittest.TestCase):
    TestFile = os.path.join(os.path.dirname(__file__), "test_data", "rpmvercmp.at")

    def setUp(self):
        super(VersionCompareTest, self).setUp()
        self.acfobj = io.open(self.TestFile, encoding="utf-8")

    def test_from_rpmtest(self):
        parser = ACParser(self.acfobj, with_buggy_comparisons=True)
        test_count = 0
        for first, second, exp in parser:
            test_count += 1
            ret = vercmp.vercmp(first, second)
            try:
                self.assertEqual(exp, ret)
            except:
                print(first, second, exp, ret)
                raise
        # Make sure we still test something, in case the m4 file drops
        # content this will fail the test
        self.assertGreater(test_count, 20)
