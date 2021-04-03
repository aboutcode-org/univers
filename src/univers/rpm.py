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
#

from __future__ import print_function
from __future__ import unicode_literals
import re


class Vercmp(object):
    R_NONALNUMTILDE = re.compile(br"^([^a-zA-Z0-9~]*)(.*)$")
    R_NUM = re.compile(br"^([\d]+)(.*)$")
    R_ALPHA = re.compile(br"^([a-zA-Z]+)(.*)$")

    @classmethod
    def compare(cls, first, second):
        first = first.encode("ascii", "ignore")
        second = second.encode("ascii", "ignore")
        while first or second:
            m1 = cls.R_NONALNUMTILDE.match(first)
            m2 = cls.R_NONALNUMTILDE.match(second)
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
                isnum = False

            if not m1:
                # this cannot happen, as we previously tested to make sure that
                # the first string has a non-null segment
                return -1  # arbitrary
            if not m2:
                return 1 if isnum else -1

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
