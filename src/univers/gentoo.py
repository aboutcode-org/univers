# versions.py -- core Portage functionality
# Copyright 1998-2016 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

import re

_v = r"(\d+)((\.\d+)*)([a-z]?)((_(pre|p|beta|alpha|rc)\d*)*)"
_rev = r"\d+"
_vr = _v + "(-r(" + _rev + "))?"

ver_regexp = re.compile("^" + _vr + "$")
suffix_regexp = re.compile("^(alpha|beta|rc|pre|p)(\\d*)$")
suffix_value = {"pre": -2, "p": 0, "alpha": -4, "beta": -3, "rc": -1}


def vercmp(ver1, ver2, silent=1):
    """
    Compare two versions
    Example usage:
            >>> from univers.gentoo import vercmp
            >>> vercmp('1.0-r1','1.2-r3')
            -1
            >>> vercmp('1.3','1.2-r3')
            1
            >>> vercmp('1.0_p3','1.0_p3')
            0

    @param pkg1: version to compare with (see ver_regexp in portage.versions.py)
    @type pkg1: string (example: "2.1.2-r3")
    @param pkg2: version to compare againts (see ver_regexp in portage.versions.py)
    @type pkg2: string (example: "2.1.2_rc5")
    @rtype: None or float
    @return:
    1. positive if ver1 is greater than ver2
    2. negative if ver1 is less than ver2
    3. 0 if ver1 equals ver2
    4. None if ver1 or ver2 are invalid (see ver_regexp in portage.versions.py)
    """

    if ver1 == ver2:
        return 0

    match1 = ver_regexp.match(ver1)
    match2 = ver_regexp.match(ver2)

    # checking that the versions are valid
    if not match1 or not match1.groups():
        if not silent:
            print(("!!! syntax error in version: %s") % ver1)
        return None
    if not match2 or not match2.groups():
        if not silent:
            print(("!!! syntax error in version: %s") % ver2)
        return None

    # building lists of the version parts before the suffix
    # first part is simple
    list1 = [int(match1.group(1))]
    list2 = [int(match2.group(1))]

    # this part would greatly benefit from a fixed-length version pattern
    if match1.group(2) or match2.group(2):
        vlist1 = match1.group(2)[1:].split(".")
        vlist2 = match2.group(2)[1:].split(".")

        for i in range(0, max(len(vlist1), len(vlist2))):
            # Implcit .0 is given a value of -1, so that 1.0.0 > 1.0, since it
            # would be ambiguous if two versions that aren't literally equal
            # are given the same value (in sorting, for example).
            if len(vlist1) <= i or len(vlist1[i]) == 0:
                list1.append(-1)
                list2.append(int(vlist2[i]))
            elif len(vlist2) <= i or len(vlist2[i]) == 0:
                list1.append(int(vlist1[i]))
                list2.append(-1)
            # Let's make life easy and use integers unless we're forced to use floats
            elif vlist1[i][0] != "0" and vlist2[i][0] != "0":
                list1.append(int(vlist1[i]))
                list2.append(int(vlist2[i]))
            # now we have to use floats so 1.02 compares correctly against 1.1
            else:
                # list1.append(float("0."+vlist1[i]))
                # list2.append(float("0."+vlist2[i]))
                # Since python floats have limited range, we multiply both
                # floating point representations by a constant so that they are
                # transformed into whole numbers. This allows the practically
                # infinite range of a python int to be exploited. The
                # multiplication is done by padding both literal strings with
                # zeros as necessary to ensure equal length.
                max_len = max(len(vlist1[i]), len(vlist2[i]))
                list1.append(int(vlist1[i].ljust(max_len, "0")))
                list2.append(int(vlist2[i].ljust(max_len, "0")))

    # and now the final letter
    # NOTE: Behavior changed in r2309 (between portage-2.0.x and portage-2.1).
    # The new behavior is 12.2.5 > 12.2b which, depending on how you look at,
    # may seem counter-intuitive. However, if you really think about it, it
    # seems like it's probably safe to assume that this is the behavior that
    # is intended by anyone who would use versions such as these.
    if len(match1.group(4)):
        list1.append(ord(match1.group(4)))
    if len(match2.group(4)):
        list2.append(ord(match2.group(4)))

    for i in range(0, max(len(list1), len(list2))):
        if len(list1) <= i:
            return -1
        if len(list2) <= i:
            return 1
        if list1[i] != list2[i]:
            a = list1[i]
            b = list2[i]
            rval = (a > b) - (a < b)
            return rval

    # main version is equal, so now compare the _suffix part
    list1 = match1.group(5).split("_")[1:]
    list2 = match2.group(5).split("_")[1:]

    for i in range(0, max(len(list1), len(list2))):
        # Implicit _p0 is given a value of -1, so that 1 < 1_p0
        if len(list1) <= i:
            s1 = ("p", "-1")
        else:
            s1 = suffix_regexp.match(list1[i]).groups()
        if len(list2) <= i:
            s2 = ("p", "-1")
        else:
            s2 = suffix_regexp.match(list2[i]).groups()
        if s1[0] != s2[0]:
            a = suffix_value[s1[0]]
            b = suffix_value[s2[0]]
            rval = (a > b) - (a < b)
            return rval
        if s1[1] != s2[1]:
            # it's possible that the s(1|2)[1] == ''
            # in such a case, fudge it.
            try:
                r1 = int(s1[1])
            except ValueError:
                r1 = 0
            try:
                r2 = int(s2[1])
            except ValueError:
                r2 = 0
            rval = (r1 > r2) - (r1 < r2)
            if rval:
                return rval

    # the suffix part is equal to, so finally check the revision
    if match1.group(9):
        r1 = int(match1.group(9))
    else:
        r1 = 0
    if match2.group(9):
        r2 = int(match2.group(9))
    else:
        r2 = 0
    rval = (r1 > r2) - (r1 < r2)
    return rval
