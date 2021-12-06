#
# Copyright (c) Facebook, Inc. and its affiliates.
# Copyright (c) SAS Institute Inc.
#
# SPDX-License-Identifier: MIT AND Apache-2.0
#
import re
from typing import NamedTuple
from typing import Union


class RpmVersion(NamedTuple):
    epoch: int
    version: str
    release: str

    @classmethod
    def from_string(cls, s):
        e, v, r = from_evr(s)
        return cls(e, v, r)


def from_evr(s):
    """
    Return an (E, V, R) tuple given a string by splitting
    [e:]version-release into the three possible subcomponents.
    Default epoch to 0, version and release to empty string if not specified.

    >>> assert from_evr("1:11.13.2.0-1") == (1, "11.13.2.0", "1")
    >>> assert from_evr("11.13.2.0-1") == (0, "11.13.2.0", "1")
    """
    if ":" in s:
        e, _, vr = s.partition(":")
    else:
        e = "0"
        vr = s

    e = int(e)

    if "-" in vr:
        v, _, r = vr.partition("-")
    else:
        v = vr
        r = ""
    return e, v, r


def compare_rpm_versions(a: Union[RpmVersion, str], b: Union[RpmVersion, str]) -> int:
    """
    Compare to RPM versions ``a`` and ``b`` and return:
    -  1 if the version of a is newer than b
    -  0 if the versions match
    -  -1 if the version of a is older than b

    These are the legacy "cmp()" function semantics.

    This implementation is adapted from both this blog post:
    https://blog.jasonantman.com/2014/07/how-yum-and-rpm-compare-versions/
    and this Apache 2 licensed implementation:
    https://github.com/sassoftware/python-rpm-vercmp/blob/master/rpm_vercmp/vercmp.py

    For example::
    >>> assert compare_rpm_versions("1.0", "1.1") == -1
    >>> assert compare_rpm_versions("1.1", "1.0") == 1
    >>> assert compare_rpm_versions("11.13.2-1", "11.13.2.0-1") == -1
    >>> assert compare_rpm_versions("11.13.2.0-1", "11.13.2-1") == 1
    """
    if isinstance(a, str):
        a = RpmVersion.from_string(a)
    if isinstance(b, str):
        b = RpmVersion.from_string(b)
    # First compare the epoch, if set.  If the epoch's are not the same, then
    # the higher one wins no matter what the rest of the EVR is.
    if a.epoch != b.epoch:
        if a.epoch > b.epoch:
            return 1  # a > b
        else:
            return -1  # a < b

    # Epoch is the same, if version + release are the same we have a match
    if (a.version == b.version) and (a.release == b.release):
        return 0  # a == b

    # Compare version first, if version is equal then compare release
    compare_res = vercmp(a.version, b.version)
    if compare_res != 0:  # a > b || a < b
        return compare_res
    else:
        return vercmp(a.release, b.release)


class Vercmp:
    R_NONALNUMTILDE_CARET = re.compile(br"^([^a-zA-Z0-9~\^]*)(.*)$")
    R_NUM = re.compile(br"^([\d]+)(.*)$")
    R_ALPHA = re.compile(br"^([a-zA-Z]+)(.*)$")

    @classmethod
    def compare(cls, first, second):
        # Rpm versions can only be ascii, anything else is just ignored
        first = first.encode("ascii", "ignore")
        second = second.encode("ascii", "ignore")

        if first == second:
            return 0

        while first or second:
            m1 = cls.R_NONALNUMTILDE_CARET.match(first)
            m2 = cls.R_NONALNUMTILDE_CARET.match(second)
            m1_head, first = m1.group(1), m1.group(2)
            m2_head, second = m2.group(1), m2.group(2)
            if m1_head or m2_head:
                # Ignore junk at the beginning
                continue

            # handle the tilde separator, it sorts before everything else
            if first.startswith(b"~"):
                if not second.startswith(b"~"):
                    return -1
                first, second = first[1:], second[1:]
                continue
            if second.startswith(b"~"):
                return 1

            # Now look at the caret, which is like the tilde but pointier.
            if first.startswith(b"^"):
                # first has a caret but second has ended
                if not second:
                    return 1  # first > second

                # first has a caret but second continues on
                elif not second.startswith(b"^"):
                    return -1  # first < second

                # strip the ^ and start again
                first, second = first[1:], second[1:]
                continue

            # Caret means the version is less... Unless the other version
            # has ended, then do the exact opposite.
            if second.startswith(b"^"):
                return -1 if not first else 1

            # We've run out of characters to compare.
            # Note: we have to do this after we compare the ~ and ^ madness
            # because ~'s and ^'s take precedance.
            # If we ran to the end of either, we are finished with the loop
            if not first or not second:
                break

            # grab first completely alpha or completely numeric segment
            m1 = cls.R_NUM.match(first)
            if m1:
                m2 = cls.R_NUM.match(second)
                if not m2:
                    # numeric segments are always newer than alpha segments
                    return 1
                isnum = True
            else:
                m1 = cls.R_ALPHA.match(first)
                m2 = cls.R_ALPHA.match(second)
                if not m2:
                    return -1
                isnum = False

            m1_head, first = m1.group(1), m1.group(2)
            m2_head, second = m2.group(1), m2.group(2)

            if isnum:
                # throw away any leading zeros - it's a number, right?
                m1_head = m1_head.lstrip(b"0")
                m2_head = m2_head.lstrip(b"0")

                # whichever number has more digits wins
                m1hlen = len(m1_head)
                m2hlen = len(m2_head)
                if m1hlen < m2hlen:
                    return -1
                if m1hlen > m2hlen:
                    return 1

            # Same number of chars
            if m1_head < m2_head:
                return -1
            if m1_head > m2_head:
                return 1
            # Both segments equal
            continue

        m1len = len(first)
        m2len = len(second)
        if m1len == m2len == 0:
            return 0
        if m1len != 0:
            return 1
        return -1


def vercmp(first, second):
    return Vercmp.compare(first, second)
