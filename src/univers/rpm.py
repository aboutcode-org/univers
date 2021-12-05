# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
from typing import NamedTuple


class RpmVersion(NamedTuple):
    epoch: int
    version: str
    release: str


# This comprises a pure python implementation of rpm version comparison. The
# purpose for this is so that the antlir library does not have a dependency
# on a C library that is (for the most part) only distributed as part of rpm
# based distros. Depending on a C library complicates dependency management
# significantly in the OSS space due to the complexity of handling 3rd party C
# libraries with buck. Having this pure python implementation also eases future
# rpm usage/handling for both non-rpm based distros and different arch types.
#
# This implementation is adapted from both this blog post:
#  https://blog.jasonantman.com/2014/07/how-yum-and-rpm-compare-versions/
# and this Apache 2 licensed implementation:
#   https://github.com/sassoftware/python-rpm-vercmp/blob/master/rpm_vercmp/vercmp.py
#
# There are extensive test cases in the `test_rpm_metadata.py` test case that
# cover a wide variety of normal and weird version comparsions.
def compare_rpm_versions(a: RpmVersion, b: RpmVersion) -> int:
    """
    Returns:
        1 if the version of a is newer than b
        0 if the versions match
        -1 if the version of a is older than b
    """

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
