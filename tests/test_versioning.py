#
# Copyright (c) 2015 SAS Institute, Inc.
#
"""
Test version handling
"""
from collections import namedtuple
import unittest

from libmaven.versioning import Version


class TestVersion(unittest.TestCase):
    """Tests the Version object"""
    def _assertVersionEqual(self, v1, v2):
        V1 = Version(v1)
        V2 = Version(v2)
        assert V1 == V2, \
            "%s != %s" % (V1._parsed, V2._parsed)
        assert V2 == V1, \
            "%s != %s" % (V2._parsed, V1._parsed)

    def _assertVersionOrder(self, v1, v2):
        V1 = Version(v1)
        V2 = Version(v2)
        assert V1 < V2, \
            "%s >= %s" % (V1._parsed, V2._parsed)
        assert V2 > V1, \
            "%s >= %s" % (V2._parsed, V1._parsed)

    def testFromString(self):
        testPairs = (
            # test some major.minor.tiny parsing
            ("1", [1]), ("1.0", [1]), ("1.0.0", [1]),
            ("1.0.0.0", [1]), ("11", [11]), ("11.0", [11]),
            ("1-1", [1, [1]]), ("1-1-1", [1, [1, [1]]]),
            # test qualifeirs
            ("1-ALPHA", [1, ["alpha"]]), ("1-alpha", [1, ["alpha"]]),
            ("1ALPHA", [1, ["alpha"]]), ("1-alpha", [1, ["alpha"]]),
            ("1-A", [1, ["a"]]), ("1-a", [1, ["a"]]),
            ("1A", [1, ["a"]]), ("1a", [1, ["a"]]),
            ("1-BETA", [1, ["beta"]]), ("1-beta", [1, ["beta"]]),
            ("1-B", [1, ["b"]]), ("1-b", [1, ["b"]]),
            ("1B", [1, ["b"]]), ("1b", [1, ["b"]]),
            ("1-MILESTONE", [1, ["milestone"]]), ("1-milestone", [1, ["milestone"]]),
            ("1-M", [1, ["m"]]), ("1-m", [1, ["m"]]),
            ("1M", [1, ["m"]]), ("1m", [1, ["m"]]),
            ("1-RC", [1, ["rc"]]), ("1-rc", [1, ["rc"]]),
            ("1-SNAPSHOT", [1, ["snapshot"]]), ("1-snapshot", [1, ["snapshot"]]),
            ("1-SP", [1, ["sp"]]), ("1-sp", [1, ["sp"]]),
            ("1-GA", [1]), ("1-ga", [1]),
            ("1-FINAL", [1]), ("1-final", [1]),
            ("1-CR", [1, ["rc"]]), ("1-cr", [1, ["rc"]]),
            # test some transistion
            ("1-alpha1", [1, ["alpha", [1]]]), ("1-alpha2", [1, ["alpha", [2]]]),
            ("1.0alpha1", [1, ["alpha", [1]]]),
            ("1-beta1", [1, ["beta", [1]]]), ("1-beta2", [1, ["beta", [2]]]),
            ("1.0beta1", [1, ["beta", [1]]]),
            ("1-BETA1", [1, ["beta", [1]]]), ("1-BETA2", [1, ["beta", [2]]]),
            ("1.0BETA1", [1, ["beta", [1]]]),
            ("1-milestone1", [1, ["milestone", [1]]]), ("1-milestone2", [1, ["milestone", [2]]]),
            ("1.0milestone1", [1, ["milestone", [1]]]),
            ("1-MILESTONE1", [1, ["milestone", [1]]]), ("1-milestone2", [1, ["milestone", [2]]]),
            ("1.0MILESTONE1", [1, ["milestone", [1]]]),
            ("1-alpha2snapshot", [1, ["alpha", [2, ["snapshot"]]]]),
            )

        for test, expected in testPairs:
            v = Version(test)
            assert v._parsed == expected, \
                "Version(%s) == %s, want %s" % (test, v._parsed, expected)

    def testVersioQualifiers(self):
        versionQualifiers = (
            "1-alpha2snapshot", "1-alpha2", "1-alpha-123", "1-beta-2",
            "1-beta123", "1-m2", "1-m11", "1-rc", "1-cr2", "1-rc123",
            "1-SNAPSHOT", "1", "1-sp", "1-sp2", "1-sp123", "1-abc", "1-def",
            "1-pom-1", "1-1-snapshot", "1-1", "1-2", "1-123",
            )
        for idx, low in enumerate(versionQualifiers[:-1]):
            for high in versionQualifiers[idx+1:]:
                self._assertVersionOrder(low, high)

    def testVersionNumbers(self):
        versionNumbers = (
            "2.0", "2-1", "2.0.a", "2.0.0.a", "2.0.2", "2.0.123", "2.1.0",
            "2.1-a", "2.1b", "2.1-x", "2.1-1", "2.1.0.1", "2.2", "2.123",
            "11.a2", "11.a11", "11.b2", "11.b11", "11.m2", "11.m11", "11",
            "11.a", "11b", "11c", "11m",
            )
        for idx, low in enumerate(versionNumbers[:-1]):
            for high in versionNumbers[idx+1:]:
                self._assertVersionOrder(low, high)

    def testVersionEquality(self):
        self._assertVersionEqual("1", "1")
        self._assertVersionEqual("1", "1.0")
        self._assertVersionEqual("1", "1.0.0")
        self._assertVersionEqual("1.0", "1.0.0")
        self._assertVersionEqual("1", "1-0")
        self._assertVersionEqual("1", "1.0-0")
        self._assertVersionEqual("1.0", "1.0-0")
        # no separator between number and character
        self._assertVersionEqual("1a", "1-a")
        self._assertVersionEqual("1a", "1.0-a")
        self._assertVersionEqual("1a", "1.0.0-a")
        self._assertVersionEqual("1.0a", "1-a")
        self._assertVersionEqual("1.0.0a", "1-a")
        self._assertVersionEqual("1x", "1-x")
        self._assertVersionEqual("1x", "1.0-x")
        self._assertVersionEqual("1x", "1.0.0-x")
        self._assertVersionEqual("1.0x", "1-x")
        self._assertVersionEqual("1.0.0x", "1-x")

        # aliases
        self._assertVersionEqual("1ga", "1")
        self._assertVersionEqual("1final", "1")
        self._assertVersionEqual("1cr", "1rc")

        # special "aliases" a, b and m for alpha, beta and milestone
        self._assertVersionEqual("1a1", "1-alpha-1")
        self._assertVersionEqual("1b2", "1-beta-2")
        self._assertVersionEqual("1m3", "1-milestone-3")

        # case insensitive
        self._assertVersionEqual("1X", "1x")
        self._assertVersionEqual("1A", "1a")
        self._assertVersionEqual("1B", "1b")
        self._assertVersionEqual("1M", "1m")
        self._assertVersionEqual("1Ga", "1")
        self._assertVersionEqual("1GA", "1")
        self._assertVersionEqual("1Final", "1")
        self._assertVersionEqual("1FinaL", "1")
        self._assertVersionEqual("1FINAL", "1")
        self._assertVersionEqual("1Cr", "1Rc")
        self._assertVersionEqual("1cR", "1rC")
        self._assertVersionEqual("1m3", "1Milestone3")
        self._assertVersionEqual("1m3", "1MileStone3")
        self._assertVersionEqual("1m3", "1MILESTONE3")

    def testVersionCompare(self):
        self._assertVersionOrder("1", "2")
        self._assertVersionOrder("1.5", "2")
        self._assertVersionOrder("1", "2.5")
        self._assertVersionOrder("1.0", "1.1")
        self._assertVersionOrder("1.1", "1.2")
        self._assertVersionOrder("1.0.0", "1.1")
        self._assertVersionOrder("1.0.1", "1.1")
        self._assertVersionOrder("1.1", "1.2.0")
        self._assertVersionOrder("1.0-alpha-1", "1.0")
        self._assertVersionOrder("1.0-alpha-1", "1.0-alpha-2")
        self._assertVersionOrder("1.0-alpha-1", "1.0-beta-1")
        self._assertVersionOrder("1.0-beta-1", "1.0-SNAPSHOT")
        self._assertVersionOrder("1.0-SNAPSHOT", "1.0")
        self._assertVersionOrder("1.0-alpha-1-SNAPSHOT", "1.0-alpha-1")
        self._assertVersionOrder("1.0", "1.0-1")
        self._assertVersionOrder("1.0-1", "1.0-2")
        self._assertVersionOrder("1.0.0", "1.0-1")
        self._assertVersionOrder("2.0-1", "2.0.1")
        self._assertVersionOrder("2.0.1-klm", "2.0.1-lmn")
        self._assertVersionOrder("2.0.1", "2.0.1-xyz")
        self._assertVersionOrder("2.0.1", "2.0.1-123")
        self._assertVersionOrder("2.0.1-xyz", "2.0.1-123")
