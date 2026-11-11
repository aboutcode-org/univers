#
# Copyright (c) nexB Inc. and others
# Copyright (c) SAS Institute Inc.
# SPDX-License-Identifier: Apache-2.0
# this has been significantly modified from the original
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

import json
from pathlib import Path

import pytest

from tests import SchemaDrivenVersTest
from univers.versions import RpmVersion

TEST_DATA = Path(__file__).parent / "data" / "schema" / "rpm_version_cmp.json"


class RpmVersionComp(SchemaDrivenVersTest):
    def equality(self):
        """Compare version1 and version2 are equal."""
        return RpmVersion(self.input_version1) == RpmVersion(self.input_version2)

    def comparison(self):
        """Sort versions and return them in the correct order."""
        return [v.string for v in sorted(map(RpmVersion, self.input["versions"]))]


@pytest.mark.parametrize("test_case", json.load(open(TEST_DATA, encoding="utf-8")))
def test_rpm_vers_cmp(test_case):
    rvc = RpmVersionComp.from_data(data=test_case)
    rvc.assert_result()
