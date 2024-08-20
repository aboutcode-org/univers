#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

from unittest import TestCase

import semver


class TestPythonSemver(TestCase):
    def test_semver_hash(self):
        # python-semver doesn't consider build while hashing
        vers1 = semver.VersionInfo.parse("1.2.3")
        vers2 = semver.VersionInfo.parse("1.2.3+1")
        assert hash(vers1) == hash(vers2)
