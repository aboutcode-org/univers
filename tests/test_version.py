#
# Copyright [2017] The Climate Corporation (https://climate.com)
# https://github.com/TheClimateCorporation/python-dpkg
# original author: Nathan J. Meh

# Copyright (c) nexB Inc. and others.
# http://nexb.com and https://github.com/nexB/debut/

# SPDX-License-Identifier: Apache-2.0

from __future__ import absolute_import
from __future__ import unicode_literals

from unittest import TestCase

from debut import version


"""
Parse, compare and sort Debian package versions.

This has been substantially modified from python-dpkg to extract the version
comparison code.
"""


class DebianVersionTest(TestCase):

    def test_get_epoch(self):
        self.assertEqual(version.get_epoch('0'), (0, '0'))
        self.assertEqual(version.get_epoch('0:0'), (0, '0'))
        self.assertEqual(version.get_epoch('1:0'), (1, '0'))
        self.assertRaises(Exception, version.get_epoch, '1a:0')

    def test_get_upstream(self):
        self.assertEqual(version.get_upstream('00'), ('00', '0'))
        self.assertEqual(version.get_upstream('foo'), ('foo', '0'))
        self.assertEqual(version.get_upstream('foo-bar'), ('foo', 'bar'))
        self.assertEqual(version.get_upstream('foo-bar-baz'), ('foo-bar', 'baz'))

    def test_split_full_version(self):
        self.assertEqual(version.get_evr('00'), (0, '00', '0'))
        self.assertEqual(version.get_evr('00-00'), (0, '00', '00'))
        self.assertEqual(version.get_evr('0:0'), (0, '0', '0'))
        self.assertEqual(version.get_evr('0:0-0'), (0, '0', '0'))
        self.assertEqual(version.get_evr('0:0.0'), (0, '0.0', '0'))
        self.assertEqual(version.get_evr('0:0.0-0'), (0, '0.0', '0'))
        self.assertEqual(version.get_evr('0:0.0-00'), (0, '0.0', '00'))

    def test_get_alpha(self):
        self.assertEqual(version.get_alphas(''), ('', ''))
        self.assertEqual(version.get_alphas('0'), ('', '0'))
        self.assertEqual(version.get_alphas('00'), ('', '00'))
        self.assertEqual(version.get_alphas('0a'), ('', '0a'))
        self.assertEqual(version.get_alphas('a'), ('a', ''))
        self.assertEqual(version.get_alphas('a0'), ('a', '0'))

    def test_get_digits(self):
        self.assertEqual(version.get_digits('00'), (0, ''))
        self.assertEqual(version.get_digits('0'), (0, ''))
        self.assertEqual(version.get_digits('0a'), (0, 'a'))
        self.assertEqual(version.get_digits('a'), (0, 'a'))
        self.assertEqual(version.get_digits('a0'), (0, 'a0'))

    def test_listify(self):
        self.assertEqual(version.listify('0'), ['', 0])
        self.assertEqual(version.listify('00'), ['', 0])
        self.assertEqual(version.listify('0a'), ['', 0, 'a', 0])
        self.assertEqual(version.listify('a0'), ['a', 0])
        self.assertEqual(version.listify('a00'), ['a', 0])
        self.assertEqual(version.listify('a'), ['a', 0])

    def test_compare_strings(self):
        self.assertEqual(version.compare_strings('~', '.'), -1)
        self.assertEqual(version.compare_strings('~', 'a'), -1)
        self.assertEqual(version.compare_strings('a', '.'), -1)
        self.assertEqual(version.compare_strings('a', '~'), 1)
        self.assertEqual(version.compare_strings('.', '~'), 1)
        self.assertEqual(version.compare_strings('.', 'a'), 1)
        self.assertEqual(version.compare_strings('.', '.'), 0)
        self.assertEqual(version.compare_strings('0', '0'), 0)
        self.assertEqual(version.compare_strings('a', 'a'), 0)

        # taken from
        # http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Version
        result = sorted(['a', '', '~', '~~a', '~~'], key=version.compare_strings_key)
        expected = ['~~', '~~a', '~', '', 'a']
        self.assertEqual(expected, result)

    def test_compare_revisions(self):
        # note that these are testing a single revision string, not the full
        # upstream+debian version.  IOW, "0.0.9-foo" is an upstream or debian
        # revision onto itself, not an upstream of 0.0.9 and a debian of foo.

        # equals
        self.assertEqual(version.compare_revisions('0', '0'), 0)
        self.assertEqual(version.compare_revisions('0', '00'), 0)
        self.assertEqual(version.compare_revisions('00.0.9', '0.0.9'), 0)
        self.assertEqual(version.compare_revisions('0.00.9-foo', '0.0.9-foo'), 0)
        self.assertEqual(version.compare_revisions('0.0.9-1.00foo', '0.0.9-1.0foo'), 0)

        # less than
        self.assertEqual(version.compare_revisions('0.0.9', '0.0.10'), -1)
        self.assertEqual(version.compare_revisions('0.0.9-foo', '0.0.10-foo'), -1)
        self.assertEqual(version.compare_revisions('0.0.9-foo', '0.0.10-goo'), -1)
        self.assertEqual(version.compare_revisions('0.0.9-foo', '0.0.9-goo'), -1)
        self.assertEqual(version.compare_revisions('0.0.10-foo', '0.0.10-goo'), -1)
        self.assertEqual(version.compare_revisions('0.0.9-1.0foo', '0.0.9-1.1foo'), -1)

        # greater than
        self.assertEqual(version.compare_revisions('0.0.10', '0.0.9'), 1)
        self.assertEqual(version.compare_revisions('0.0.10-foo', '0.0.9-foo'), 1)
        self.assertEqual(version.compare_revisions('0.0.10-foo', '0.0.9-goo'), 1)
        self.assertEqual(version.compare_revisions('0.0.9-1.0foo', '0.0.9-1.0bar'), 1)

    def test_compare_versions(self):
        # "This [the epoch] is a single (generally small) unsigned integer.
        # It may be omitted, in which case zero is assumed."
        self.assertEqual(version.compare_versions('0.0.0', '0:0.0.0'), 0)
        self.assertEqual(version.compare_versions('0:0.0.0-foo', '0.0.0-foo'), 0)
        self.assertEqual(version.compare_versions('0.0.0-a', '0:0.0.0-a'), 0)

        # "The absence of a debian_revision is equivalent to a debian_revision
        # of 0."
        self.assertEqual(version.compare_versions('0.0.0', '0.0.0-0'), 0)
        # tricksy:
        self.assertEqual(version.compare_versions('0.0.0', '0.0.0-00'), 0)

        # combining the above
        self.assertEqual(version.compare_versions('0.0.0-0', '0:0.0.0'), 0)

        # explicitly equal
        self.assertEqual(version.compare_versions('0.0.0', '0.0.0'), 0)
        self.assertEqual(version.compare_versions('1:0.0.0', '1:0.0.0'), 0)
        self.assertEqual(version.compare_versions('0.0.0-10', '0.0.0-10'), 0)
        self.assertEqual(version.compare_versions('2:0.0.0-1', '2:0.0.0-1'), 0)
        self.assertEqual(version.compare_versions('0:a.0.0-foo', '0:a.0.0-foo'), 0)

        # less than
        self.assertEqual(version.compare_versions('0.0.0-0', '0:0.0.1'), -1)
        self.assertEqual(version.compare_versions('0.0.0-0', '0:0.0.0-a'), -1)
        self.assertEqual(version.compare_versions('0.0.0-0', '0:0.0.0-1'), -1)
        self.assertEqual(version.compare_versions('0.0.9', '0.0.10'), -1)
        self.assertEqual(version.compare_versions('0.9.0', '0.10.0'), -1)
        self.assertEqual(version.compare_versions('9.0.0', '10.0.0'), -1)

        # greater than
        self.assertEqual(version.compare_versions('0.0.1-0', '0:0.0.0'), 1)
        self.assertEqual(version.compare_versions('0.0.0-a', '0:0.0.0-1'), 1)
        self.assertEqual(version.compare_versions('0.0.0-a', '0:0.0.0-0'), 1)
        self.assertEqual(version.compare_versions('0.0.9', '0.0.1'), 1)
        self.assertEqual(version.compare_versions('0.9.0', '0.1.0'), 1)
        self.assertEqual(version.compare_versions('9.0.0', '1.0.0'), 1)

        # unicode
        self.assertEqual(version.compare_versions(u'2:0.0.44-1', u'2:0.0.44-nobin'), -1)
        self.assertEqual(version.compare_versions(u'2:0.0.44-nobin', u'2:0.0.44-1'), 1)
        self.assertEqual(version.compare_versions(u'2:0.0.44-1', u'2:0.0.44-1'), 0)
