"""gentoo ebuild specific base package class"""

import re

suffix_regexp = re.compile("^(alpha|beta|rc|pre|p)(\\d*)$")

revision_regexp = re.compile(".*(-r\d+)")

suffix_value = {"pre": -2, "p": 1, "alpha": -4, "beta": -3, "rc": -1}

# while the package section looks fugly, there is a reason for it-
# to prevent version chunks from showing up in the package


def cmp(a, b):
    return bool(a > b) - bool(a < b)


def parse_version_and_revision(version_string):
    revision = 0
    version = version_string
    match = revision_regexp.search(version_string)
    if match:
        revision = int(match.group(1)[2:])
        version = version_string[: match.span(1)[0]]

    return version, revision


def vercmp(ver1, ver2):
    ver1, rev1 = parse_version_and_revision(ver1)
    ver2, rev2 = parse_version_and_revision(ver2)

    # If the versions are the same, comparing revisions will suffice.
    if ver1 == ver2:
        # revisions are equal if 0 or None (versionless cpv)
        if not rev1 and not rev2:
            return 0
        return cmp(rev1, rev2)

    # Split up the versions into dotted strings and lists of suffixes.
    parts1 = ver1.split("_")
    parts2 = ver2.split("_")

    # If the dotted strings are equal, we can skip doing a detailed comparison.
    if parts1[0] != parts2[0]:

        # First split up the dotted strings into their components.
        ver_parts1 = parts1[0].split(".")
        ver_parts2 = parts2[0].split(".")

        # Pull out any letter suffix on the final components and keep
        # them for later.
        letters = []
        for ver_parts in (ver_parts1, ver_parts2):
            if ver_parts[-1][-1].isalpha():
                letters.append(ord(ver_parts[-1][-1]))
                ver_parts[-1] = ver_parts[-1][:-1]
            else:
                # Using -1 simplifies comparisons later
                letters.append(-1)

        # OPT: Pull length calculation out of the loop
        ver_parts1_len = len(ver_parts1)
        ver_parts2_len = len(ver_parts2)

        # Iterate through the components
        for v1, v2 in zip(ver_parts1, ver_parts2):

            # If the string components are equal, the numerical
            # components will be equal too.
            if v1 == v2:
                continue

            # If one of the components begins with a "0" then they
            # are compared as floats so that 1.1 > 1.02; else ints.
            if v1[0] != "0" and v2[0] != "0":
                v1 = int(v1)
                v2 = int(v2)
            else:
                # handle the 0.060 == 0.060 case.
                v1 = v1.rstrip("0")
                v2 = v2.rstrip("0")

            # If they are not equal, the higher value wins.
            c = cmp(v1, v2)
            if c:
                return c

        if ver_parts1_len > ver_parts2_len:
            return 1
        elif ver_parts2_len > ver_parts1_len:
            return -1

        # The dotted components were equal. Let's compare any single
        # letter suffixes.
        if letters[0] != letters[1]:
            return cmp(letters[0], letters[1])

    # The dotted components were equal, so remove them from our lists
    # leaving only suffixes.
    del parts1[0]
    del parts2[0]

    # OPT: Pull length calculation out of the loop
    parts1_len = len(parts1)
    parts2_len = len(parts2)

    # Iterate through the suffixes
    for x in range(max(parts1_len, parts2_len)):

        # If we're at the end of one of our lists, we need to use
        # the next suffix from the other list to decide who wins.
        if x == parts1_len:
            match = suffix_regexp.match(parts2[x])
            val = suffix_value[match.group(1)]
            if val:
                return cmp(0, val)
            return cmp(0, int("0" + match.group(2)))
        if x == parts2_len:
            match = suffix_regexp.match(parts1[x])
            val = suffix_value[match.group(1)]
            if val:
                return cmp(val, 0)
            return cmp(int("0" + match.group(2)), 0)

        # If the string values are equal, no need to parse them.
        # Continue on to the next.
        if parts1[x] == parts2[x]:
            continue

        # Match against our regular expression to make a split between
        # "beta" and "1" in "beta1"
        match1 = suffix_regexp.match(parts1[x])
        match2 = suffix_regexp.match(parts2[x])

        # If our int'ified suffix names are different, use that as the basis
        # for comparison.
        c = cmp(suffix_value[match1.group(1)], suffix_value[match2.group(1)])
        if c:
            return c

        # Otherwise use the digit as the basis for comparison.
        c = cmp(int("0" + match1.group(2)), int("0" + match2.group(2)))
        if c:
            return c

    # Our versions had different strings but ended up being equal.
    # The revision holds the final difference.
    return cmp(rev1, rev2)
