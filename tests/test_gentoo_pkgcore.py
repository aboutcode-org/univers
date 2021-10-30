#
# Copyright (c) 2006-2019, pkgcore contributors
# SPDX-License-Identifier: BSD-3-Clause
# Version comparison utility extracted from pkgcore and further stripped down.
#
# Visit https://aboutcode.org and https://github.com/nexB/univers for support and download.

from random import shuffle

from univers.gentoo import parse_version_and_revision
from univers.gentoo import vercmp


def generate_misc_sufs():
    simple_good_sufs = ["_alpha", "_beta", "_pre", "_p"]
    suf_nums = list(range(100))
    shuffle(suf_nums)

    good_sufs = simple_good_sufs + [f"{x}{suf_nums.pop()}" for x in simple_good_sufs]

    l = len(good_sufs)
    good_sufs = good_sufs + [good_sufs[x] + good_sufs[l - x - 1] for x in range(l)]

    bad_sufs = ["_a", "_9", "_"] + [x + " " for x in simple_good_sufs]
    return good_sufs, bad_sufs


good_vers = ("1", "2.3.4", "2.3.4a", "02.3", "2.03", "3d", "3D")

good_sufs, bad_sufs = generate_misc_sufs()
good_revs = ("-r1", "-r300", "-r0", "", "-r1000000000000000000")


def older(v1, v2):
    return vercmp(v1, v2) < 0


def newer(v1, v2):
    return vercmp(v1, v2) > 0


def equal(v1, v2):
    return vercmp(v1, v2) == 0


class TestCPV:
    def test_parse_version_and_revision_rev(self):

        for x in (10, 18, 19, 36, 100):
            _ver, rev = parse_version_and_revision(f"1-r0{'0' * x}")
            assert rev == 0

            _ver, rev = parse_version_and_revision(f"1-r1{'0' * x}1")
            assert int(rev) == int(f"1{'0' * x}1")

    def test_parse_version_and_revisions(self):
        for ver in good_vers:
            v_r = parse_version_and_revision(ver)
            assert v_r == (ver, 0)
            for rev in good_revs:
                version = f"{ver}{rev}"
                try:
                    v_r = parse_version_and_revision(version)
                    expected_rev = rev.lstrip("-r")
                    expected_rev = expected_rev and int(expected_rev) or 0
                    assert v_r == (ver, expected_rev), f"Failed to parse: {version}"
                except Exception as e:
                    raise Exception(f"Failed to parse: {version!r}") from e

                for suf in good_sufs:
                    version = f"{ver}{suf}{rev}"
                    v_r = parse_version_and_revision(version)
                    assert v_r == (f"{ver}{suf}", expected_rev)

    def test_cmp(self):
        assert older("0.1", "0.2")

    def test_cmp1(self):
        base = "0.7.1"
        base = equal(base, base)
        for rev in ("", "-r1"):
            last = None
            for suf in ["_alpha", "_beta", "_pre", "", "_p"]:
                if suf == "":
                    sufs = [suf]
                else:
                    sufs = [suf, f"{suf}4"]
                for x in sufs:
                    cur = f"{base}{x}{rev}"
                    assert equal(cur, f"{base}{x}{rev}")
                    if last is not None:
                        assert newer(cur, last)

    def test_cmp2(self):
        assert newer("6a", "6")
        assert newer("6a-r1", "6a")
        assert newer("6.0", "6")
        assert newer("6.0.0", "6.0b")
        assert newer("6.02", "6.0.0")

    def test_cmp_float(self):
        # float comparison rules.
        assert newer("6.2", "6.054")
        assert equal("6", "6")
        assert newer("6.0_alpha0_p1", "6.0_alpha")
        assert equal("6.0_alpha", "6.0_alpha0")
        assert newer("6.1", "6.09")
        assert newer("6.0.1", "6.0")
        assert newer("12.2.5", "12.2b")

    def test_cmp_287848(self):
        # test for gentoo bug 287848
        assert newer("12.2.5", "12.2b")
        assert newer("12.2.5-r1", "12.2b")

    def test_cmp_equiv(self):
        # equivalent versions
        assert equal("6.01.0", "6.010.0")
        assert equal("6.0.1", "6.000.1")

    def test_cmp_equiv_rev(self):
        # equivalent revisions
        assert equal("6.01.0", "6.01.0-r0")
        assert equal("6.01.0-r0", "6.01.0-r00")
        assert equal("6.01.0-r1", "6.01.0-r001")

        for v1, v2 in (
            ("1.001000000000000000001", "1.001000000000000000002"),
            ("1.00100000000", "1.0010000000000000001"),
            ("1.01", "1.1"),
        ):
            assert newer(f"{v2}", f"{v1}")

        for x in (18, 36, 100):
            s = "0" * x
            assert newer(f"10{s}1", f"1{s}1")

        for x in (18, 36, 100):
            s = "0" * x
            assert newer(f"1-r10{s}1", f"1-r1{s}1")

        assert newer("1.60_p2010081516093", "1.60_p2009072801401")

        assert newer("1.60_p20100815160931", "1.60_p20090728014017")

        assert newer("1.60_p20100815160931", "1.60_p20090728014017-r1")

        # Regression test: python does comparison slightly differently
        # if the classes do not match exactly (it prefers rich
        # comparison over __cmp__).

        assert not equal("6.0_alpha0_p1", "6.0_alpha")
        assert equal("6.0_alpha0", "6.0_alpha")

        assert not equal("6.0", "")
        assert equal("6.0", "6.0-r0")

    def test_r0_revisions_with_single_0(self):
        ver, rev = parse_version_and_revision("1.0-r0")
        assert ver == "1.0"
        assert rev == 0

    def test_r0_revisions_with_multiple_0(self):
        ver, rev = parse_version_and_revision("1.0-r000")
        assert ver == "1.0"
        assert rev == 0

    def test_r0_revisions_with_single_0_prefix(self):
        ver, rev = parse_version_and_revision("1.0-r01")
        assert ver == "1.0"
        assert rev == 1

    def test_r0_revisions_with_multiple_0_prefix(self):
        ver, rev = parse_version_and_revision("11.0-r0001")
        assert ver == "11.0"
        assert rev == 1
