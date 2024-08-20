#
# Copyright (c) nexB Inc. and others.
# SPDX-License-Identifier: Apache-2.0
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

from unittest import TestCase

from packaging import version as packaging_version

from univers.versions import InvalidVersion
from univers.versions import PypiVersion

# version comparison is already tested at:
# https://github.com/pypa/packaging/blob/main/tests/test_version.py


class TestPYPIVersion(TestCase):
    def test_constructor(self):
        pypi_version = PypiVersion("2.4.5")
        assert pypi_version.value == packaging_version.Version("2.4.5")
        self.assertRaises(InvalidVersion, PypiVersion, "2.//////")

    def test_compare(self):
        pypi_version = PypiVersion("2.4.5")
        assert pypi_version == PypiVersion("2.4.5")
        assert pypi_version != PypiVersion("2.4.6")
        assert pypi_version > PypiVersion("2.4.4")
        assert pypi_version >= PypiVersion("2.4.4")
        assert pypi_version < PypiVersion("2.4.6")
        assert pypi_version <= PypiVersion("2.4.6")
        assert PypiVersion("2.4") == PypiVersion("2.4.0")
