# Copyright (c) 2009-2020 by Pacman Development Team
# Copyright (c) 2008 by Dan McGee <dan@archlinux.org>
# SPDX-License-Identifier: Apache-2.0
# this has been significantly modified from the original
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import json
from pathlib import Path

import pytest

from tests import SchemaDrivenVersTest
from univers.versions import ArchLinuxVersion

TEST_DATA = Path(__file__).parent / "data" / "schema" / "alpm_version_cmp.json"


class ArchLinuxVersionComp(SchemaDrivenVersTest):
    def equality(self):
        """Compare version1 and version2 are equal."""
        return ArchLinuxVersion(self.input_version1) == ArchLinuxVersion(self.input_version2)

    def comparison(self):
        """Sort versions and return them in the correct order."""
        return [v.string for v in sorted(map(ArchLinuxVersion, self.input["versions"]))]


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA)))
def test_archlinux_vers_cmp(test_case):
    avc = ArchLinuxVersionComp.from_data(data=test_case)
    avc.assert_result()
