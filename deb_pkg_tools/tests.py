# Debian packaging tools: Automated tests.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 25, 2014
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

# Modules included in our package.
from deb_pkg_tools import version
from deb_pkg_tools.cli import main
from deb_pkg_tools.compat import StringIO, unicode
from deb_pkg_tools.control import (deb822_from_string,
                                   merge_control_fields,
                                   parse_control_fields,
                                   unparse_control_fields)
from deb_pkg_tools.deps import (AlternativeRelationship, VersionedRelationship,
                                parse_depends, Relationship, RelationshipSet)
from deb_pkg_tools.gpg import GPGKey
from deb_pkg_tools.package import collect_related_packages, inspect_package, parse_filename
from deb_pkg_tools.printer import CustomPrettyPrinter
from deb_pkg_tools.repo import apt_supports_trusted_option, update_repository

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

    def test_control_file_patching(self):
        deb822_package = Deb822(['Package: unpatched-example',
                                 'Depends: some-dependency'])
        control_file = tempfile.mktemp()
        try:
            with open(control_file, 'wb') as handle:
                deb822_package.dump(handle)
            call('--patch=%s' % control_file,
                 '--set=Package: patched-example',
                 '--set=Depends: another-dependency')
            with open(control_file) as handle:
                patched_fields = Deb822(handle)
            self.assertEqual(patched_fields['Package'], 'patched-example')
            self.assertEqual(patched_fields['Depends'], 'another-dependency, some-dependency')
        finally:
            os.unlink(control_file)

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
        # Alternatives (OR) without versions.
        relationship_set = parse_depends('python2.6 | python2.7')
        self.assertFalse(relationship_set.matches('python2.5'))
        self.assertTrue(relationship_set.matches('python2.6'))
        self.assertTrue(relationship_set.matches('python2.7'))
        self.assertFalse(relationship_set.matches('python3.0'))
        # Combinations (AND) with versions.
        relationship_set = parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
        self.assertFalse(relationship_set.matches('python', '2.5'))
        self.assertTrue(relationship_set.matches('python', '2.6'))
        self.assertTrue(relationship_set.matches('python', '2.7'))
        self.assertFalse(relationship_set.matches('python', '3.0'))
        self.assertTrue(relationship_set.matches('python', '3.4'))
        # Testing for matches without providing a version is valid (should not
        # raise an error) but will never match a relationship with a version.
        relationship_set = parse_depends('python (>= 2.6), python (<< 3)')
        self.assertTrue(relationship_set.matches('python', '2.7'))
        self.assertFalse(relationship_set.matches('python'))
        # Distinguishing between packages whose name was matched but whose
        # version didn't match vs packages whose name wasn't matched.
        relationship_set = parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
        self.assertEqual(relationship_set.matches('python', '2.7'), True) # name and version match
        self.assertEqual(relationship_set.matches('python', '2.5'), False) # name matched, version didn't
        self.assertEqual(relationship_set.matches('python2.6'), None) # name didn't match
        self.assertEqual(relationship_set.matches('python', '3.0'), False) # name in alternative matched, version didn't

    def test_relationship_sorting(self):
        relationship_set = parse_depends('foo | bar, baz | qux')
        self.assertEqual(relationship_set, RelationshipSet(
            AlternativeRelationship(Relationship(name='baz'), Relationship(name='qux')),
            AlternativeRelationship(Relationship(name='foo'), Relationship(name='bar'))))

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

    def test_package_building(self, repository=None, overrides={}):
        directory = tempfile.mkdtemp()
        destructors = [functools.partial(shutil.rmtree, directory)]
        try:
            control_fields = merge_control_fields(TEST_PACKAGE_FIELDS, overrides)
            # Create the package template.
            os.mkdir(os.path.join(directory, 'DEBIAN'))
            with open(os.path.join(directory, 'DEBIAN', 'control'), 'wb') as handle:
                control_fields.dump(handle)
            with open(os.path.join(directory, 'DEBIAN', 'conffiles'), 'wb') as handle:
                handle.write(b'/etc/file1\n')
                handle.write(b'/etc/file2\n')
            # Create the directory with configuration files.
            os.mkdir(os.path.join(directory, 'etc'))
            touch(os.path.join(directory, 'etc', 'file1'))
            touch(os.path.join(directory, 'etc', 'file3'))
            # Create a directory that should be cleaned up by clean_package_tree().
            os.makedirs(os.path.join(directory, 'tmp', '.git'))
            # Create a file that should be cleaned up by clean_package_tree().
            with open(os.path.join(directory, 'tmp', '.gitignore'), 'w') as handle:
                handle.write('\n')
            # Build the package (without any contents :-).
            call('--build', directory)
            package_file = os.path.join(tempfile.gettempdir(),
                                        '%s_%s_%s.deb' % (control_fields['Package'],
                                                          control_fields['Version'],
                                                          control_fields['Architecture']))
            self.assertTrue(os.path.isfile(package_file))
            if repository:
                shutil.move(package_file, repository)
                return os.path.join(repository, os.path.basename(package_file))
            else:
                destructors.append(functools.partial(os.unlink, package_file))
                # Verify the package metadata.
                fields, contents = inspect_package(package_file)
                for name in TEST_PACKAGE_FIELDS:
                    self.assertEqual(fields[name], TEST_PACKAGE_FIELDS[name])
                # Verify that the package contains the `/' and `/tmp'
                # directories (since it doesn't contain any actual files).
                self.assertEqual(contents['/'].permissions[0], 'd')
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
        finally:
            for partial in destructors:
                partial()

    def test_command_line_interface(self):
        if not SKIP_SLOW_TESTS:
            directory = tempfile.mkdtemp()
            destructors = [functools.partial(shutil.rmtree, directory)]
            try:
                # Test `deb-pkg-tools --inspect PKG'.
                package_file = self.test_package_building(directory)
                lines = call('--inspect', package_file).splitlines()
                for field, value in TEST_PACKAGE_FIELDS.items():
                    self.assertEqual(match('^ - %s: (.+)$' % field, lines), value)
                # Test `deb-pkg-tools --with-repo=DIR CMD' (we simply check whether
                # apt-cache sees the package).
                if os.getuid() == 0:
                    call('--with-repo=%s' % directory, 'apt-cache show %s' % TEST_PACKAGE_NAME)
            finally:
                for partial in destructors:
                    partial()

    def test_collect_packages(self):
        directory = tempfile.mkdtemp()
        destructors = [functools.partial(shutil.rmtree, directory)]
        try:
            package1 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-1', Depends='deb-pkg-tools-package-2'))
            package2 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-2', Depends='deb-pkg-tools-package-3'))
            package3 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-3'))
            package4 = self.test_package_building(directory, overrides=dict(Package='deb-pkg-tools-package-3', Version='0.2'))
            self.assertEqual(sorted(p.filename for p in collect_related_packages(package1)), [package2, package4])
        finally:
            for partial in destructors:
                partial()

    def test_repository_creation(self, preserve=False):
        if not SKIP_SLOW_TESTS:
            config_dir = tempfile.mkdtemp()
            repo_dir = tempfile.mkdtemp()
            destructors = []
            if not preserve:
                destructors.append(functools.partial(shutil.rmtree, config_dir))
                destructors.append(functools.partial(shutil.rmtree, repo_dir))
            from deb_pkg_tools import repo
            repo.USER_CONFIG_DIR = config_dir
            with open(os.path.join(config_dir, repo.CONFIG_FILE), 'w') as handle:
                handle.write('[test]\n')
                handle.write('directory = %s\n' % repo_dir)
                handle.write('release-origin = %s\n' % TEST_REPO_ORIGIN)
            try:
                self.test_package_building(repo_dir)
                update_repository(repo_dir, release_fields=dict(description=TEST_REPO_DESCRIPTION))
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
            finally:
                for partial in destructors:
                    partial()

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
            working_directory = tempfile.mkdtemp()
            secret_key_file = os.path.join(working_directory, 'subdirectory', 'test.sec')
            public_key_file = os.path.join(working_directory, 'subdirectory', 'test.pub')
            try:
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
                self.assertRaises(Exception, GPGKey, key_id='12345', secret_key_file=missing_secret_key_file, public_key_file=missing_public_key_file)
                os.unlink(secret_key_file)
                self.assertRaises(Exception, GPGKey, name="test-key", description="Whatever", secret_key_file=secret_key_file, public_key_file=public_key_file)
                touch(secret_key_file)
                os.unlink(public_key_file)
                self.assertRaises(Exception, GPGKey, name="test-key", description="Whatever", secret_key_file=secret_key_file, public_key_file=public_key_file)
                os.unlink(secret_key_file)
                self.assertRaises(Exception, GPGKey, secret_key_file=secret_key_file, public_key_file=public_key_file)
            finally:
                shutil.rmtree(working_directory)

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

# vim: ts=4 sw=4 et
