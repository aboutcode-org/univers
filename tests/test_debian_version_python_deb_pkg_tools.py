#
# Copyright (c) Peter Odding <peter@peterodding.com>
# URL: https://github.com/xolox/python-deb-pkg-tools
# SPDX-License-Identifier: MIT
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.


from unittest import TestCase

from univers.debian import Version


class DebPkgToolsTestCase(TestCase):
    def test_version_sorting(self):
        # Check version sorting implemented on top of `=' and `<<' comparisons.
        expected_order = ["0.1", "0.5", "1.0", "2.0", "3.0", "1:0.4", "2:0.3"]
        assert list(sorted(expected_order)) != expected_order
        result = [str(v) for v in sorted(map(Version.from_string, expected_order))]
        assert result == expected_order

    def test_version_comparison(self):
        assert Version.from_string("1.0") > Version.from_string("0.5")
        assert Version.from_string("1:0.5") > Version.from_string("2.0")
        assert not Version.from_string("0.5") > Version.from_string("2.0")

        assert Version.from_string("0.75") >= Version.from_string("0.5")
        assert Version.from_string("0.50") >= Version.from_string("0.5")
        assert Version.from_string("1:0.5") >= Version.from_string("5.0")
        assert not Version.from_string("0.2") >= Version.from_string("0.5")

        assert Version.from_string("0.5") < Version.from_string("1.0")
        assert Version.from_string("2.0") < Version.from_string("1:0.5")
        assert not Version.from_string("2.0") < Version.from_string("0.5")

        assert Version.from_string("0.5") <= Version.from_string("0.75")
        assert Version.from_string("0.5") <= Version.from_string("0.50")
        assert Version.from_string("5.0") <= Version.from_string("1:0.5")
        assert not Version.from_string("0.5") <= Version.from_string("0.2")

        assert Version.from_string("42") == Version.from_string("42")
        assert Version.from_string("0.5") == Version.from_string("0:0.5")
        assert not Version.from_string("0.5") == Version.from_string("1.0")

        assert Version.from_string("1") != Version.from_string("0")
        assert not Version.from_string("0.5") != Version.from_string("0:0.5")

        assert Version.from_string("1.3~rc2") < Version.from_string("1.3")
