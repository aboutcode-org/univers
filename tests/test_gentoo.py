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


def test_gentoo_slots_and_wildcards():
    # Issue #182 reported versions
    assert GentooVersion.is_valid("1.3*")
    assert GentooVersion.is_valid("3.24.48:3")
    assert GentooVersion.is_valid("6.9.3:6")
    assert GentooVersion.is_valid("7.3*")
    assert GentooVersion.is_valid("7.4*")

    v_slot = GentooVersion("3.24.48:3")
    assert v_slot.slot == "3"
    assert not v_slot.is_wildcard
    assert v_slot == GentooVersion("3.24.48:3")
    assert v_slot == GentooVersion("3.24.48")
    assert v_slot == GentooVersion("3.24.48:10")
    assert v_slot < GentooVersion("3.24.49:3")
    assert v_slot > GentooVersion("3.24.47:3")

    v_slot6 = GentooVersion("6.9.3:6")
    assert v_slot6.slot == "6"

    # Sub-slot and slot operators
    assert GentooVersion.is_valid("2.4.52:0/2.4")
    assert GentooVersion("2.4.52:0/2.4").slot == "0/2.4"
    assert GentooVersion.is_valid("3.0:3=")
    assert GentooVersion("3.0:3=").slot == "3="

    # Wildcards
    v_wild = GentooVersion("1.3*")
    assert v_wild.is_wildcard
    assert v_wild.slot is None
    assert v_wild == GentooVersion("1.3*")
    assert v_wild == GentooVersion("1.3")
    assert v_wild == GentooVersion("1.3.1")
    assert v_wild == GentooVersion("1.3a")
    assert v_wild == GentooVersion("1.3_alpha4")
    assert v_wild == GentooVersion("1.3-r1")
    assert v_wild != GentooVersion("1.30")
    assert v_wild != GentooVersion("1.4")
    assert v_wild < GentooVersion("1.4")
    assert v_wild > GentooVersion("1.2")
    assert GentooVersion("7.3*") < GentooVersion("7.4*")

    # Constraint satisfaction and round-tripping through EbuildVersionRange
    from univers.version_constraint import VersionConstraint
    from univers.version_range import EbuildVersionRange
    from univers.version_range import VersionRange

    c_gt = VersionConstraint(comparator=">", version=GentooVersion("3.24.47:3"))
    assert GentooVersion("3.24.48:3") in c_gt
    assert GentooVersion("3.24.48") in c_gt
    assert GentooVersion("3.24.49") in c_gt
    assert GentooVersion("3.24.47") not in c_gt

    c_eq = VersionConstraint(comparator="=", version=GentooVersion("1.3*"))
    assert GentooVersion("1.3*") in c_eq
    assert GentooVersion("1.3") in c_eq
    assert GentooVersion("1.3.1") in c_eq
    assert GentooVersion("1.3a") in c_eq
    assert GentooVersion("1.3_alpha4") in c_eq
    assert GentooVersion("1.3-r1") in c_eq
    assert GentooVersion("1.30") not in c_eq
    assert GentooVersion("1.4") not in c_eq

    vr = EbuildVersionRange(constraints=[c_eq, c_gt])
    vr_str = str(vr)
    assert vr_str == "vers:ebuild/1.3*|>3.24.47:3"
    assert VersionRange.from_string(vr_str) == vr
    assert GentooVersion("1.3.1") in vr
    assert GentooVersion("1.30") not in vr

    # Invalid formats
    assert not GentooVersion.is_valid("*")
    assert not GentooVersion.is_valid("1.3**")
    assert not GentooVersion.is_valid(":3")
    assert not GentooVersion.is_valid("1:")
    assert not GentooVersion.is_valid("3.24.48:")
    assert not GentooVersion.is_valid("3.24.48:invalid!slot")
