# Debian packaging tools: Automated tests.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 1, 2015
# URL: https://github.com/xolox/python-deb-pkg-tools

# Standard library modules.
import functools
import logging
import os
import random
import re
import shutil
import sys
import tempfile
import textwrap
import unittest

# External dependencies.
import coloredlogs
from debian.deb822 import Deb822
from executor import execute

# Modules included in our package.
from deb_pkg_tools import version
from deb_pkg_tools.cache import PackageCache
from deb_pkg_tools.checks import check_duplicate_files, check_version_conflicts, DuplicateFilesFound, VersionConflictFound
from deb_pkg_tools.cli import main
from deb_pkg_tools.compat import StringIO, unicode
from deb_pkg_tools.control import (deb822_from_string, load_control_file,
                                   merge_control_fields, parse_control_fields,
                                   unparse_control_fields)
from deb_pkg_tools.deps import VersionedRelationship, parse_depends, Relationship, RelationshipSet
from deb_pkg_tools.gpg import GPGKey
from deb_pkg_tools.package import collect_related_packages, copy_package_files, find_latest_version, find_package_archives, group_by_latest_versions, inspect_package, parse_filename
from deb_pkg_tools.printer import CustomPrettyPrinter
from deb_pkg_tools.repo import apt_supports_trusted_option, update_repository
from deb_pkg_tools.utils import find_debian_architecture

# Initialize a logger.
logger = logging.getLogger(__name__)

# Improvised slow test marker.
SKIP_SLOW_TESTS = 'SKIP_SLOW_TESTS' in os.environ

# Configuration defaults.
TEST_PACKAGE_NAME = 'deb-pkg-tools-demo-package'
TEST_PACKAGE_FIELDS = Deb822(dict(Architecture='all',
                                  Description='Nothing to see here, move along',
                                  Maintainer='Peter Odding <peter@peterodding.com>',
                                  Package=TEST_PACKAGE_NAME,
                                  Version='0.1',
                                  Section='misc',
                                  Priority='optional'))
TEST_REPO_ORIGIN = 'DebPkgToolsTestCase'
TEST_REPO_DESCRIPTION = 'Description of test repository'

class DebPkgToolsTestCase(unittest.TestCase):

    def setUp(self):
        coloredlogs.install()
        coloredlogs.set_level(logging.DEBUG)
        self.db_directory = tempfile.mkdtemp()
        self.load_package_cache()
        os.environ['DPT_FORCE_ENTROPY'] = 'yes'

    def load_package_cache(self):
        self.package_cache = PackageCache(os.path.join(self.db_directory, 'package-cache.sqlite3'))

    def tearDown(self):
        self.package_cache.collect_garbage(force=True)
        shutil.rmtree(self.db_directory)
        os.environ.pop('DPT_FORCE_ENTROPY')

    def test_package_cache_error_handling(self):
        self.assertRaises(KeyError, self.package_cache.__getitem__, '/some/random/non-existing/path')

    def test_file_copying(self):
        with Context() as finalizers:
            source_directory = finalizers.mkdtemp()
            target_directory = finalizers.mkdtemp()
            touch(os.path.join(source_directory, '42'))
            copy_package_files(source_directory, target_directory, hard_links=True)
            self.assertEqual(os.stat(os.path.join(source_directory, '42')).st_ino,
                             os.stat(os.path.join(target_directory, '42')).st_ino)

    def test_package_cache_invalidation(self):
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            package_file = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-1', Version='1'))
            for i in range(5):
                fields, contents = inspect_package(package_file, cache=self.package_cache)
                if i % 2 == 0:
                    os.utime(package_file, None)
                else:
                    self.load_package_cache()

    def test_architecture_determination(self):
        valid_architectures = execute('dpkg-architecture', '-L', capture=True).splitlines()
        self.assertTrue(find_debian_architecture() in valid_architectures)

    def test_find_latest_version(self):
        good = ['name_1.0_all.deb', 'name_0.5_all.deb']
        self.assertEqual(os.path.basename(find_latest_version(good).filename), 'name_1.0_all.deb')
        bad= ['one_1.0_all.deb', 'two_0.5_all.deb']
        self.assertRaises(ValueError, find_latest_version, bad)

    def test_group_by_latest_versions(self):
        packages = ['one_1.0_all.deb', 'one_0.5_all.deb', 'two_1.5_all.deb', 'two_0.1_all.deb']
        self.assertEqual(sorted(os.path.basename(a.filename) for a in group_by_latest_versions(packages).values()),
                         sorted(['one_1.0_all.deb', 'two_1.5_all.deb']))

    def test_control_field_parsing(self):
        deb822_package = Deb822(['Package: python-py2deb',
                                 'Depends: python-deb-pkg-tools, python-pip, python-pip-accel',
                                 'Installed-Size: 42'])
        parsed_info = parse_control_fields(deb822_package)
        self.assertEqual(parsed_info,
                         {'Package': 'python-py2deb',
                          'Depends': RelationshipSet(
                              Relationship(name=u'python-deb-pkg-tools'),
                              Relationship(name=u'python-pip'),
                              Relationship(name=u'python-pip-accel')),
                          'Installed-Size': 42})
        # Test backwards compatibility with the old interface where `Depends'
        # like fields were represented as a list of strings (shallow parsed).
        parsed_info['Depends'] = [unicode(r) for r in parsed_info['Depends']]
        self.assertEqual(unparse_control_fields(parsed_info), deb822_package)
        # Test compatibility with fields like `Depends' containing a string.
        parsed_info['Depends'] = deb822_package['Depends']
        self.assertEqual(unparse_control_fields(parsed_info), deb822_package)

    def test_control_field_merging(self):
        defaults = Deb822(['Package: python-py2deb',
                           'Depends: python-deb-pkg-tools',
                           'Architecture: all'])
        # The field names of the dictionary with overrides are lower case on
        # purpose; control file merging should work properly regardless of
        # field name casing.
        overrides = Deb822(dict(version='1.0',
                                depends='python-pip, python-pip-accel',
                                architecture='amd64'))
        self.assertEqual(merge_control_fields(defaults, overrides),
                         Deb822(['Package: python-py2deb',
                                 'Version: 1.0',
                                 'Depends: python-deb-pkg-tools, python-pip, python-pip-accel',
                                 'Architecture: amd64']))

    def test_control_file_patching_and_loading(self):
        deb822_package = Deb822(['Package: unpatched-example',
                                 'Depends: some-dependency'])
        with Context() as finalizers:
            control_file = tempfile.mktemp()
            finalizers.register(os.unlink, control_file)
            with open(control_file, 'wb') as handle:
                deb822_package.dump(handle)
            call('--patch=%s' % control_file,
                 '--set=Package: patched-example',
                 '--set=Depends: another-dependency')
            patched_fields = load_control_file(control_file)
            self.assertEqual(patched_fields['Package'], 'patched-example')
            self.assertEqual(str(patched_fields['Depends']), 'another-dependency, some-dependency')

    def test_version_comparison(self):
        self.version_comparison_helper()
        if version.have_python_apt:
            version.have_python_apt = False
            self.version_comparison_helper()
            self.assertRaises(NotImplementedError, version.compare_versions_with_python_apt, '0.1', '<<', '0.2')
            version.have_python_apt = True

    def version_comparison_helper(self):
        # V() shortcut for deb_pkg_tools.version.Version().
        V = version.Version
        # Check version sorting implemented on top of `=' and `<<' comparisons.
        expected_order = ['0.1', '0.5', '1.0', '2.0', '3.0', '1:0.4', '2:0.3']
        self.assertNotEqual(list(sorted(expected_order)), expected_order)
        self.assertEqual(list(sorted(map(V, expected_order))), expected_order)
        # Check each individual operator (to make sure the two implementations
        # agree). We use the Version() class for this so that we test both
        # compare_versions() and the Version() wrapper.
        # Test `>'.
        self.assertTrue(V('1.0') > V('0.5')) # usual semantics
        self.assertTrue(V('1:0.5') > V('2.0')) # unusual semantics
        self.assertFalse(V('0.5') > V('2.0')) # sanity check
        # Test `>='.
        self.assertTrue(V('0.75') >= V('0.5')) # usual semantics
        self.assertTrue(V('0.50') >= V('0.5')) # usual semantics
        self.assertTrue(V('1:0.5') >= V('5.0')) # unusual semantics
        self.assertFalse(V('0.2') >= V('0.5')) # sanity check
        # Test `<'.
        self.assertTrue(V('0.5') < V('1.0')) # usual semantics
        self.assertTrue(V('2.0') < V('1:0.5')) # unusual semantics
        self.assertFalse(V('2.0') < V('0.5')) # sanity check
        # Test `<='.
        self.assertTrue(V('0.5') <= V('0.75')) # usual semantics
        self.assertTrue(V('0.5') <= V('0.50')) # usual semantics
        self.assertTrue(V('5.0') <= V('1:0.5')) # unusual semantics
        self.assertFalse(V('0.5') <= V('0.2')) # sanity check
        # Test `=='.
        self.assertTrue(V('42') == V('42')) # usual semantics
        self.assertTrue(V('0.5') == V('0:0.5')) # unusual semantics
        self.assertFalse(V('0.5') == V('1.0')) # sanity check
        # Test `!='.
        self.assertTrue(V('1') != V('0')) # usual semantics
        self.assertFalse(V('0.5') != V('0:0.5')) # unusual semantics

    def test_relationship_parsing(self):
        # Happy path (no parsing errors).
        relationship_set = parse_depends('foo, bar (>= 1) | baz')
        self.assertEqual(relationship_set.relationships[0].name, 'foo')
        self.assertEqual(relationship_set.relationships[1].relationships[0].name, 'bar')
        self.assertEqual(relationship_set.relationships[1].relationships[0].operator, '>=')
        self.assertEqual(relationship_set.relationships[1].relationships[0].version, '1')
        self.assertEqual(relationship_set.relationships[1].relationships[1].name, 'baz')
        self.assertEqual(parse_depends('foo (=1.0)'), RelationshipSet(VersionedRelationship(name='foo', operator='=', version='1.0')))
        # Unhappy path (parsing errors).
        self.assertRaises(ValueError, parse_depends, 'foo (bar) (baz)')
        self.assertRaises(ValueError, parse_depends, 'foo (bar baz qux)')

    def test_relationship_unparsing(self):
        relationship_set = parse_depends('foo, bar(>=1)|baz')
        self.assertEqual(unicode(relationship_set), 'foo, bar (>= 1) | baz')
        self.assertEqual(compact(repr(relationship_set)), "RelationshipSet(Relationship(name='foo'), AlternativeRelationship(VersionedRelationship(name='bar', operator='>=', version='1'), Relationship(name='baz')))")

    def test_relationship_evaluation(self):
        # Relationships without versions.
        relationship_set = parse_depends('python')
        self.assertTrue(relationship_set.matches('python'))
        self.assertFalse(relationship_set.matches('python2.7'))
        self.assertEqual(list(relationship_set.names), ['python'])
        # Alternatives (OR) without versions.
        relationship_set = parse_depends('python2.6 | python2.7')
        self.assertFalse(relationship_set.matches('python2.5'))
        self.assertTrue(relationship_set.matches('python2.6'))
        self.assertTrue(relationship_set.matches('python2.7'))
        self.assertFalse(relationship_set.matches('python3.0'))
        self.assertEqual(sorted(relationship_set.names), ['python2.6', 'python2.7'])
        # Combinations (AND) with versions.
        relationship_set = parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
        self.assertFalse(relationship_set.matches('python', '2.5'))
        self.assertTrue(relationship_set.matches('python', '2.6'))
        self.assertTrue(relationship_set.matches('python', '2.7'))
        self.assertFalse(relationship_set.matches('python', '3.0'))
        self.assertTrue(relationship_set.matches('python', '3.4'))
        self.assertEqual(list(relationship_set.names), ['python'])
        # Testing for matches without providing a version is valid (should not
        # raise an error) but will never match a relationship with a version.
        relationship_set = parse_depends('python (>= 2.6), python (<< 3)')
        self.assertTrue(relationship_set.matches('python', '2.7'))
        self.assertFalse(relationship_set.matches('python'))
        self.assertEqual(list(relationship_set.names), ['python'])
        # Distinguishing between packages whose name was matched but whose
        # version didn't match vs packages whose name wasn't matched.
        relationship_set = parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
        self.assertEqual(relationship_set.matches('python', '2.7'), True) # name and version match
        self.assertEqual(relationship_set.matches('python', '2.5'), False) # name matched, version didn't
        self.assertEqual(relationship_set.matches('python2.6'), None) # name didn't match
        self.assertEqual(relationship_set.matches('python', '3.0'), False) # name in alternative matched, version didn't
        self.assertEqual(list(relationship_set.names), ['python'])

    def test_custom_pretty_printer(self):
        printer = CustomPrettyPrinter()
        # Test pretty printing of debian.deb822.Deb822 objects.
        self.assertEqual(remove_unicode_prefixes(printer.pformat(deb822_from_string('''
            Package: pretty-printed-control-fields
            Version: 1.0
            Architecture: all
        '''))), remove_unicode_prefixes(dedent('''
            {'Architecture': u'all',
             'Package': u'pretty-printed-control-fields',
             'Version': u'1.0'}
        ''')))
        # Test pretty printing of RelationshipSet objects.
        depends_line = 'python-deb-pkg-tools, python-pip, python-pip-accel'
        self.assertEqual(printer.pformat(parse_depends(depends_line)), dedent('''
            RelationshipSet(Relationship(name='python-deb-pkg-tools'),
                            Relationship(name='python-pip'),
                            Relationship(name='python-pip-accel'))
        '''))

    def test_filename_parsing(self):
        # Test the happy path.
        filename = '/var/cache/apt/archives/python2.7_2.7.3-0ubuntu3.4_amd64.deb'
        components = parse_filename(filename)
        self.assertEqual(components.filename, filename)
        self.assertEqual(components.name, 'python2.7')
        self.assertEqual(components.version, '2.7.3-0ubuntu3.4')
        self.assertEqual(components.architecture, 'amd64')
        # Test the unhappy paths.
        self.assertRaises(ValueError, parse_filename, 'python2.7_2.7.3-0ubuntu3.4_amd64.not-a-deb')
        self.assertRaises(ValueError, parse_filename, 'python2.7.deb')

    def test_package_building(self, repository=None, overrides={}, contents={}):
        with Context() as finalizers:
            build_directory = finalizers.mkdtemp()
            control_fields = merge_control_fields(TEST_PACKAGE_FIELDS, overrides)
            # Create the package template.
            os.mkdir(os.path.join(build_directory, 'DEBIAN'))
            with open(os.path.join(build_directory, 'DEBIAN', 'control'), 'wb') as handle:
                control_fields.dump(handle)
            if contents:
                for filename, data in contents.items():
                    filename = os.path.join(build_directory, filename)
                    directory = os.path.dirname(filename)
                    if not os.path.isdir(directory):
                        os.makedirs(directory)
                    with open(filename, 'w') as handle:
                        handle.write(data)
            else:
                with open(os.path.join(build_directory, 'DEBIAN', 'conffiles'), 'wb') as handle:
                    handle.write(b'/etc/file1\n')
                    handle.write(b'/etc/file2\n')
                # Create the directory with configuration files.
                os.mkdir(os.path.join(build_directory, 'etc'))
                touch(os.path.join(build_directory, 'etc', 'file1'))
                touch(os.path.join(build_directory, 'etc', 'file3'))
                # Create a directory that should be cleaned up by clean_package_tree().
                os.makedirs(os.path.join(build_directory, 'tmp', '.git'))
                # Create a file that should be cleaned up by clean_package_tree().
                with open(os.path.join(build_directory, 'tmp', '.gitignore'), 'w') as handle:
                    handle.write('\n')
            # Build the package (without any contents :-).
            call('--build', build_directory)
            package_file = os.path.join(tempfile.gettempdir(),
                                        '%s_%s_%s.deb' % (control_fields['Package'],
                                                          control_fields['Version'],
                                                          control_fields['Architecture']))
            self.assertTrue(os.path.isfile(package_file))
            if repository:
                shutil.move(package_file, repository)
                return os.path.join(repository, os.path.basename(package_file))
            else:
                finalizers.register(os.unlink, package_file)
                # Verify the package metadata.
                fields, contents = inspect_package(package_file)
                for name in TEST_PACKAGE_FIELDS:
                    self.assertEqual(fields[name], TEST_PACKAGE_FIELDS[name])
                # Verify that the package contains the `/' and `/tmp'
                # directories (since it doesn't contain any actual files).
                self.assertEqual(contents['/'].permissions[0], 'd')
                self.assertEqual(contents['/'].permissions[1:], 'rwxr-xr-x')
                self.assertEqual(contents['/'].owner, 'root')
                self.assertEqual(contents['/'].group, 'root')
                self.assertEqual(contents['/tmp/'].permissions[0], 'd')
                self.assertEqual(contents['/tmp/'].owner, 'root')
                self.assertEqual(contents['/tmp/'].group, 'root')
                # Verify that clean_package_tree() cleaned up properly
                # (`/tmp/.git' and `/tmp/.gitignore' have been cleaned up).
                self.assertFalse('/tmp/.git/' in contents)
                self.assertFalse('/tmp/.gitignore' in contents)
                return package_file

    def test_command_line_interface(self):
        if not SKIP_SLOW_TESTS:
            with Context() as finalizers:
                directory = finalizers.mkdtemp()
                # Test `deb-pkg-tools --inspect PKG'.
                package_file = self.test_package_building(directory)
                lines = call('--verbose', '--inspect', package_file).splitlines()
                for field, value in TEST_PACKAGE_FIELDS.items():
                    self.assertEqual(match('^ - %s: (.+)$' % field, lines), value)
                # Test `deb-pkg-tools --with-repo=DIR CMD' (we simply check whether
                # apt-cache sees the package).
                if os.getuid() == 0:
                    call('--with-repo=%s' % directory, 'apt-cache show %s' % TEST_PACKAGE_NAME)
                # Test `deb-pkg-tools --update=DIR' with a non-existing directory.
                self.assertRaises(SystemExit, call, '--update', '/a/directory/that/will/never/exist')

    def test_check_package(self):
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            root_package, conflicting_package = self.create_version_conflict(directory)
            # This *should* raise SystemExit.
            self.assertRaises(SystemExit, call, '--check', root_package)
            # Test for lack of duplicate files.
            os.unlink(conflicting_package)
            # This should *not* raise SystemExit.
            call('--check', root_package)

    def test_version_conflicts_check(self):
        with Context() as finalizers:
            # Check that version conflicts raise an exception.
            directory = finalizers.mkdtemp()
            root_package, conflicting_package = self.create_version_conflict(directory)
            packages_to_scan = collect_related_packages(root_package)
            # Test the duplicate files check.
            self.assertRaises(VersionConflictFound, check_version_conflicts, packages_to_scan, self.package_cache)
            # Test for lack of duplicate files.
            os.unlink(conflicting_package)
            self.assertEqual(check_version_conflicts(packages_to_scan, cache=self.package_cache), None)

    def create_version_conflict(self, directory):
        root_package = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-1', Depends='deb-pkg-tools-package-2 (=1)'))
        self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-2', Version='1'))
        conflicting_package = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-2', Version='2'))
        return root_package, conflicting_package

    def test_duplicates_check(self):
        with Context() as finalizers:
            # Check that duplicate files raise an exception.
            directory = finalizers.mkdtemp()
            # Build a package containing some files.
            self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-1', Version='1'))
            # Build an unrelated package containing the same files.
            self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-2'))
            # Build two versions of one package.
            duplicate_contents = {'foo/bar': 'some random file'}
            self.test_package_building(directory,
                                       overrides=dict(Package='deb-pkg-tools-package-3', Version='1'),
                                       contents=duplicate_contents)
            self.test_package_building(directory,
                                       overrides=dict(Package='deb-pkg-tools-package-3', Version='2'),
                                       contents=duplicate_contents)
            # Build two packages related by their `Conflicts' and `Provides' fields.
            virtual_package = 'deb-pkg-tools-virtual-package'
            duplicate_contents = {'foo/baz': 'another random file'}
            self.test_package_building(directory,
                                       overrides=dict(Package='deb-pkg-tools-package-4',
                                                      Conflicts=virtual_package,
                                                      Provides=virtual_package),
                                       contents=duplicate_contents)
            self.test_package_building(directory,
                                       overrides=dict(Package='deb-pkg-tools-package-5',
                                                      Conflicts=virtual_package,
                                                      Provides=virtual_package),
                                       contents=duplicate_contents)
            # Test the duplicate files check.
            package_archives = find_package_archives(directory)
            self.assertRaises(DuplicateFilesFound, check_duplicate_files, package_archives, cache=self.package_cache)
            # Verify that invalid arguments are checked.
            self.assertRaises(ValueError, check_duplicate_files, [])

    def test_collect_packages(self):
        with Context() as finalizers:
            source_directory = finalizers.mkdtemp()
            target_directory = finalizers.mkdtemp()
            package1 = self.test_package_building(source_directory, overrides=dict(Package='deb-pkg-tools-package-1', Depends='deb-pkg-tools-package-2'))
            package2 = self.test_package_building(source_directory, overrides=dict(Package='deb-pkg-tools-package-2', Depends='deb-pkg-tools-package-3'))
            package3 = self.test_package_building(source_directory, overrides=dict(Package='deb-pkg-tools-package-3'))
            call('--yes', '--collect=%s' % target_directory, package1)
            self.assertEqual(sorted(os.listdir(target_directory)), sorted(map(os.path.basename, [package1, package2, package3])))

    def test_collect_packages_interactive(self):
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            package1 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-1', Depends='deb-pkg-tools-package-2'))
            package2 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-2', Depends='deb-pkg-tools-package-3'))
            package3_1 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-3', Version='0.1'))
            package3_2 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-3', Version='0.2'))
            related_packages = [p.filename for p in collect_related_packages(package1, cache=self.package_cache)]
            # Make sure deb-pkg-tools-package-2 was collected.
            assert package2 in related_packages
            # Make sure deb-pkg-tools-package-3 version 0.1 wasn't collected.
            assert package3_1 not in related_packages
            # Make sure deb-pkg-tools-package-3 version 0.2 was collected.
            assert package3_2 in related_packages

    def test_collect_packages_preference_for_newer_versions(self):
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            package1 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-1', Depends='deb-pkg-tools-package-2'))
            package2_1 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-2', Version='1', Depends='deb-pkg-tools-package-3 (= 1)'))
            package2_2 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-2', Version='2', Depends='deb-pkg-tools-package-3 (= 2)'))
            package3_1 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-3', Version='1'))
            package3_2 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-3', Version='2'))
            related_packages = [p.filename for p in collect_related_packages(package1, cache=self.package_cache)]
            # Make sure deb-pkg-tools-package-2 version 1 wasn't collected.
            assert package2_1 not in related_packages
            # Make sure deb-pkg-tools-package-2 version 2 was collected.
            assert package2_2 in related_packages
            # Make sure deb-pkg-tools-package-3 version 1 wasn't collected.
            assert package3_1 not in related_packages
            # Make sure deb-pkg-tools-package-3 version 2 was collected.
            assert package3_2 in related_packages

    def test_collect_packages_with_conflict_resolution(self):
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            # The following names are a bit confusing, this is to enforce implicit sorting on file system level (exposing an otherwise unnoticed bug).
            package_a = self.test_package_building(directory, overrides=dict(Package='package-a', Depends='package-b, package-c'))
            package_b = self.test_package_building(directory, overrides=dict(Package='package-b', Depends='package-d'))
            package_c = self.test_package_building(directory, overrides=dict(Package='package-c', Depends='package-d (= 1)'))
            package_d1 = self.test_package_building(directory, overrides=dict(Package='package-d', Version='1'))
            package_d2 = self.test_package_building(directory, overrides=dict(Package='package-d', Version='2'))
            related_packages = [p.filename for p in collect_related_packages(package_a, cache=self.package_cache)]
            # Make sure package-b was collected.
            assert package_b in related_packages
            # Make sure package-c was collected.
            assert package_c in related_packages
            # Make sure package-d1 was collected.
            assert package_d1 in related_packages
            # Make sure package-d2 wasn't collected.
            assert package_d2 not in related_packages

    def test_repository_creation(self, preserve=False):
        if not SKIP_SLOW_TESTS:
            with Context() as finalizers:
                config_dir = tempfile.mkdtemp()
                repo_dir = tempfile.mkdtemp()
                if not preserve:
                    finalizers.register(shutil.rmtree, config_dir)
                    finalizers.register(shutil.rmtree, repo_dir)
                from deb_pkg_tools import config
                config.user_config_directory = config_dir
                with open(os.path.join(config_dir, config.repo_config_file), 'w') as handle:
                    handle.write('[test]\n')
                    handle.write('directory = %s\n' % repo_dir)
                    handle.write('release-origin = %s\n' % TEST_REPO_ORIGIN)
                self.test_package_building(repo_dir)
                update_repository(repo_dir, release_fields=dict(description=TEST_REPO_DESCRIPTION), cache=self.package_cache)
                self.assertTrue(os.path.isfile(os.path.join(repo_dir, 'Packages')))
                self.assertTrue(os.path.isfile(os.path.join(repo_dir, 'Packages.gz')))
                self.assertTrue(os.path.isfile(os.path.join(repo_dir, 'Release')))
                with open(os.path.join(repo_dir, 'Release')) as handle:
                    fields = Deb822(handle)
                    self.assertEqual(fields['Origin'], TEST_REPO_ORIGIN)
                    self.assertEqual(fields['Description'], TEST_REPO_DESCRIPTION)
                if not apt_supports_trusted_option():
                    self.assertTrue(os.path.isfile(os.path.join(repo_dir, 'Release.gpg')))
                return repo_dir

    def test_repository_activation(self):
        if not SKIP_SLOW_TESTS and os.getuid() == 0:
            repository = self.test_repository_creation(preserve=True)
            call('--activate-repo=%s' % repository)
            try:
                handle = os.popen('apt-cache show %s' % TEST_PACKAGE_NAME)
                fields = Deb822(handle)
                self.assertEqual(fields['Package'], TEST_PACKAGE_NAME)
            finally:
                call('--deactivate-repo=%s' % repository)
            # XXX If we skipped the GPG key handling because apt supports the
            # [trusted=yes] option, re-run the test *including* GPG key
            # handling (we want this to be tested...).
            import deb_pkg_tools
            if deb_pkg_tools.repo.apt_supports_trusted_option():
                deb_pkg_tools.repo.trusted_option_supported = False
                self.test_repository_activation()

    def test_gpg_key_generation(self):
        if not SKIP_SLOW_TESTS:
            with Context() as finalizers:
                working_directory = finalizers.mkdtemp()
                secret_key_file = os.path.join(working_directory, 'subdirectory', 'test.sec')
                public_key_file = os.path.join(working_directory, 'subdirectory', 'test.pub')
                # Generate a named GPG key on the spot.
                GPGKey(name="named-test-key",
                       description="GPG key pair generated for unit tests (named key)",
                       secret_key_file=secret_key_file,
                       public_key_file=public_key_file)
                # Generate a default GPG key on the spot.
                default_key = GPGKey(name="default-test-key",
                                     description="GPG key pair generated for unit tests (default key)")
                self.assertEqual(os.path.basename(default_key.secret_key_file), 'secring.gpg')
                self.assertEqual(os.path.basename(default_key.public_key_file), 'pubring.gpg')
                # Test error handling related to GPG keys.
                self.assertRaises(Exception, GPGKey, secret_key_file=secret_key_file)
                self.assertRaises(Exception, GPGKey, public_key_file=public_key_file)
                missing_secret_key_file = '/tmp/deb-pkg-tools-%i.sec' % random.randint(1, 1000)
                missing_public_key_file = '/tmp/deb-pkg-tools-%i.pub' % random.randint(1, 1000)
                self.assertRaises(Exception, GPGKey, key_id='12345', secret_key_file=secret_key_file, public_key_file=missing_public_key_file)
                self.assertRaises(Exception, GPGKey, key_id='12345', secret_key_file=missing_secret_key_file, public_key_file=public_key_file)
                os.unlink(secret_key_file)
                self.assertRaises(Exception, GPGKey, name="test-key", description="Whatever", secret_key_file=secret_key_file, public_key_file=public_key_file)
                touch(secret_key_file)
                os.unlink(public_key_file)
                self.assertRaises(Exception, GPGKey, name="test-key", description="Whatever", secret_key_file=secret_key_file, public_key_file=public_key_file)
                os.unlink(secret_key_file)
                self.assertRaises(Exception, GPGKey, secret_key_file=secret_key_file, public_key_file=public_key_file)

def touch(filename, contents='\n'):
    with open(filename, 'w') as handle:
        handle.write(contents)

def call(*arguments):
    saved_stdout = sys.stdout
    saved_argv = sys.argv
    try:
        sys.stdout = StringIO()
        sys.argv = [sys.argv[0]] + list(arguments)
        main()
        return sys.stdout.getvalue()
    finally:
        sys.stdout = saved_stdout
        sys.argv = saved_argv

def match(pattern, lines):
    for line in lines:
        m = re.match(pattern, line)
        if m:
            return m.group(1)

def dedent(string):
    return textwrap.dedent(string).strip()

def compact(string):
    """
    Compact all whitespace sequences to single spaces and strip all leading and
    trailing whitespace.
    """
    return ' '.join(string.split())

def remove_unicode_prefixes(expression):
    """
    Enable string comparison between :py:func:`repr()` output on Python 2.x
    (where Unicode strings have the ``u`` prefix) and Python 3.x (where Unicode
    strings are the default and no prefix is emitted by :py:func:`repr()`).
    """
    return re.sub(r'\bu([\'"])', r'\1', expression)

class Context(object):

    def __init__(self):
        self.finalizers = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        for finalizer in reversed(self.finalizers):
            finalizer()
        self.finalizers = []

    def register(self, *args, **kw):
        self.finalizers.append(functools.partial(*args, **kw))

    def mkdtemp(self, *args, **kw):
        directory = tempfile.mkdtemp(*args, **kw)
        self.register(shutil.rmtree, directory)
        return directory

# vim: ts=4 sw=4 et
