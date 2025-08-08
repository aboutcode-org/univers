#
# Copyright (c) Peter Odding <peter@peterodding.com>
# URL: https://github.com/xolox/python-deb-pkg-tools
# SPDX-License-Identifier: MIT
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.


import json
from pathlib import Path

import pytest

from tests import SchemaDrivenVersTest
from univers.debian import Version

TEST_DATA = Path(__file__).parent / "data" / "schema" / "deb_version_python_pkg_test.json"


class PythonDebPkgToolsVersionComp(SchemaDrivenVersTest):
    def equality(self):
        """Compare version1 and version2 are equal."""
        return Version.from_string(self.input_version1) == Version.from_string(self.input_version2)

    def comparison(self):
        """Sort versions and return them in the correct order."""
        return [str(v) for v in sorted(map(Version.from_string, self.input["versions"]))]


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA)))
def test_python_deb_pkg_tools_version(test_case):
    avc = PythonDebPkgToolsVersionComp.from_data(data=test_case)
    avc.assert_result()
