#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from unittest import TestCase
from packaging import version

from univers import versions


class TestPYPIVersion(TestCase):
    def test_constructor(self):
        pypi_version = versions.PYPIVersion("2.4.5")
        assert pypi_version.value == version.Version("2.4.5")
        assert pypi_version.scheme == "pypi"

        self.assertRaises(versions.InvalidVersion, versions.PYPIVersion, "2.//////")

    # comparison is already tested at https://github.com/pypa/packaging/blob/main/tests/test_version.py
