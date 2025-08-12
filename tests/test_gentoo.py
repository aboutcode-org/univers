# test_vercmp.py -- Portage Unit Testing Functionality
# Copyright 2006 Gentoo Foundation
# SPDX-License-Identifier: GPL-2.0-only
# this has been significantly modified from the original
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.


import json
from pathlib import Path

import pytest

from tests import SchemaDrivenVersTest
from univers.versions import GentooVersion

TEST_DATA = Path(__file__).parent / "data" / "schema" / "gentoo_version_cmp.json"


class GentooVersionComp(SchemaDrivenVersTest):
    def equality(self):
        """Compare version1 and version2 are equal."""
        return GentooVersion(self.input_version1) == GentooVersion(self.input_version2)

    def comparison(self):
        """Sort versions and return them in the correct order."""
        return [str(v) for v in sorted(map(GentooVersion, self.input["versions"]))]


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA)))
def test_gentoo_vers_cmp(test_case):
    avc = GentooVersionComp.from_data(data=test_case)
    avc.assert_result()
