#
# Copyright (c) nexB Inc. and others.
# Copyright (c) Eelco Dolstra and the Nix contributors.
#
# SPDX-License-Identifier: Apache-2.0 AND LGPL-2.1-or-later
#
# Visit https://aboutcode.org and https://github.com/aboutcode-org/univers for support and download.

"""
Python port of Nix's ``builtins.compareVersions``.
https://nix.dev/manual/nix/latest/language/builtins.html#builtins-compareVersions

The reference implementation is ``compareVersions`` and ``componentsLT`` in
https://github.com/NixOS/nix/blob/534f199c9a34ace17d4db26fa3d377ee904bdf03/src/libstore/names.cc
and this port reproduces it exactly:

- Any string is a comparable version, so versions are totally ordered.
- The component "pre" sorts before every other component, including the empty
  one, so "2.3pre1" sorts before "2.3". No other pre-release marker is special.
- Numeric components are parsed as C ``int``, so a run of digits whose value
  exceeds 2**31 - 1 is treated as a non-numeric component and sorts before any
  numeric component.
"""

from itertools import zip_longest

_SEPARATORS = ".-"

# Nix parses numeric components as C integers, so larger values compare as strings.
_INT_MAX = 2**31 - 1


def _is_digit(char):
    # Nix only considers ASCII characters digits, Python is more lenient.
    return "0" <= char <= "9"


def _parse_int(component):
    if not component or not all(_is_digit(char) for char in component):
        return None
    value = int(component)
    return value if value <= _INT_MAX else None


def _components(version):
    """
    Split a version string into maximal runs of digits or non-digits.
    Dots and dashes are separators and belong to no component.
    """
    components = []
    pos = 0
    end = len(version)
    while pos < end:
        while pos < end and version[pos] in _SEPARATORS:
            pos += 1
        if pos == end:
            break
        start = pos
        if _is_digit(version[pos]):
            while pos < end and _is_digit(version[pos]):
                pos += 1
        else:
            while pos < end and not _is_digit(version[pos]) and version[pos] not in _SEPARATORS:
                pos += 1
        components.append(version[start:pos])
    return components


def _components_lt(c1, c2):
    n1 = _parse_int(c1)
    n2 = _parse_int(c2)

    if n1 is not None and n2 is not None:
        return n1 < n2
    elif c1 == "" and n2 is not None:
        return True
    elif c1 == "pre" and c2 != "pre":
        return True
    elif c2 == "pre":
        return False
    # Assume that `2.3a` < `2.3.1`.
    elif n2 is not None:
        return True
    elif n1 is not None:
        return False
    else:
        return c1 < c2


def compare_versions(version1, version2):
    """
    Compare two version strings as ``builtins.compareVersions`` does.
    Return -1 if ``version1`` is older than ``version2``, 0 if they are
    equivalent, 1 if newer.
    """
    for c1, c2 in zip_longest(_components(version1), _components(version2), fillvalue=""):
        if _components_lt(c1, c2):
            return -1
        if _components_lt(c2, c1):
            return 1
    return 0
