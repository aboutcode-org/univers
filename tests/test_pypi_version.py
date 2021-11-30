#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from packaging import version as packaging_version
from unittest import TestCase

from univers import versions

# version comparison is already tested at:
# https://github.com/pypa/packaging/blob/main/tests/test_version.py


class TestPYPIVersion(TestCase):
    def test_constructor(self):
        pypi_version = versions.PypiVersion("2.4.5")
        assert pypi_version.value == packaging_version.Version("2.4.5")
        self.assertRaises(versions.InvalidVersion, versions.PypiVersion, "2.//////")
