# Debian packaging tools: Automated tests.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: October 26, 2018
# URL: https://github.com/xolox/python-deb-pkg-tools

"""Test suite for the `deb-pkg-tools` package."""

# Standard library modules.
import functools
import logging
import os
import re
import shutil
import sys
import tempfile

# External dependencies.
from capturer import CaptureOutput
from debian.deb822 import Deb822
from executor import execute
from humanfriendly.testing import PatchedAttribute, TestCase, run_cli, touch
from humanfriendly.text import dedent
from six import text_type
from six.moves import StringIO

# Modules included in our package.
from deb_pkg_tools import version
from deb_pkg_tools.cache import PackageCache
from deb_pkg_tools.checks import (
    DuplicateFilesFound,
    VersionConflictFound,
    check_duplicate_files,
    check_version_conflicts,
)
from deb_pkg_tools.cli import main
from deb_pkg_tools.control import (
    create_control_file,
    deb822_from_string,
    load_control_file,
    merge_control_fields,
    parse_control_fields,
    unparse_control_fields,
)
from deb_pkg_tools.deps import (
    Relationship,
    RelationshipSet,
    VersionedRelationship,
    parse_depends,
)
from deb_pkg_tools.gpg import GPGKey
from deb_pkg_tools.package import (
    collect_related_packages,
    copy_package_files,
    find_latest_version,
    find_object_files,
    find_package_archives,
    find_system_dependencies,
    group_by_latest_versions,
    inspect_package,
    parse_filename,
)
from deb_pkg_tools.printer import CustomPrettyPrinter
from deb_pkg_tools.repo import apt_supports_trusted_option, update_repository
from deb_pkg_tools.utils import find_debian_architecture, makedirs

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


class DebPkgToolsTestCase(TestCase):

    """Container for the `deb-pkg-tools` test suite."""

    def setUp(self):
        """Prepare a temporary package cache."""
        # Set up our superclass.
        super(DebPkgToolsTestCase, self).setUp()
        # Prepare the package cache.
        self.db_directory = tempfile.mkdtemp()
        self.load_package_cache()
        # Try to force entropy generation.
        os.environ['DPT_FORCE_ENTROPY'] = 'yes'

    def load_package_cache(self):
        """Prepare a temporary package cache for the duration of a test."""
        self.package_cache = PackageCache(directory=self.db_directory)

    def tearDown(self):
        """Cleanup the temporary package cache."""
        # Tear down our superclass.
        super(DebPkgToolsTestCase, self).tearDown()
        # Cleanup the package cache.
        self.package_cache.collect_garbage(force=True)
        shutil.rmtree(self.db_directory)
        # Disable entropy generation.
        os.environ.pop('DPT_FORCE_ENTROPY')

    def test_makedirs(self):
        """Test that makedirs() can deal with race conditions."""
        with Context() as finalizers:
            parent = finalizers.mkdtemp()
            child = os.path.join(parent, 'nested')
            # This will create the directory.
            makedirs(child)
            # This should not complain that the directory already exists.
            makedirs(child)

    def test_file_copying(self):
        """Test that file copying using hard links actually works."""
        with Context() as finalizers:
            source_directory = finalizers.mkdtemp()
            target_directory = finalizers.mkdtemp()
            touch(os.path.join(source_directory, '42'))
            copy_package_files(source_directory, target_directory, hard_links=True)
            assert os.stat(os.path.join(source_directory, '42')).st_ino == \
                os.stat(os.path.join(target_directory, '42')).st_ino

    def test_package_cache_invalidation(self):
        """Test that the package cache handles invalidation properly."""
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            package_file = self.test_package_building(directory, overrides=dict(
                Package='deb-pkg-tools-package-1',
                Version='1',
            ))
            for i in range(5):
                fields, contents = inspect_package(package_file, cache=self.package_cache)
                if i % 2 == 0:
                    os.utime(package_file, None)
                else:
                    self.load_package_cache()

    def test_architecture_determination(self):
        """Make sure discovery of the current build architecture works properly."""
        valid_architectures = execute('dpkg-architecture', '-L', capture=True).splitlines()
        assert find_debian_architecture() in valid_architectures

    def test_find_package_archives(self):
        """Test searching for package archives."""
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            for filename in 'some-random-file', 'regular-package_1.0_all.deb', 'micro-package_1.5_all.udeb':
                touch(os.path.join(directory, filename))
            matches = find_package_archives(directory)
            assert len(matches) == 2
            assert any(p.name == 'regular-package' and
                       p.version == '1.0' and
                       p.architecture == 'all'
                       for p in matches)
            assert any(p.name == 'micro-package' and
                       p.version == '1.5' and
                       p.architecture == 'all'
                       for p in matches)

    def test_find_latest_version(self):
        """Test the selection of latest versions."""
        good = ['name_1.0_all.deb', 'name_0.5_all.deb']
        assert os.path.basename(find_latest_version(good).filename) == 'name_1.0_all.deb'
        bad = ['one_1.0_all.deb', 'two_0.5_all.deb']
        self.assertRaises(ValueError, find_latest_version, bad)

    def test_group_by_latest_versions(self):
        """Test the grouping by latest versions."""
        packages = ['one_1.0_all.deb', 'one_0.5_all.deb', 'two_1.5_all.deb', 'two_0.1_all.deb']
        assert sorted(os.path.basename(a.filename) for a in group_by_latest_versions(packages).values()) == \
            sorted(['one_1.0_all.deb', 'two_1.5_all.deb'])

    def test_control_field_parsing(self):
        """Test the parsing of control file fields."""
        deb822_package = Deb822(['Package: python-py2deb',
                                 'Depends: python-deb-pkg-tools, python-pip, python-pip-accel',
                                 'Installed-Size: 42'])
        parsed_info = parse_control_fields(deb822_package)
        assert parsed_info == {'Package': 'python-py2deb',
                               'Depends': RelationshipSet(
                                   Relationship(name=u'python-deb-pkg-tools'),
                                   Relationship(name=u'python-pip'),
                                   Relationship(name=u'python-pip-accel')),
                               'Installed-Size': 42}
        # Test backwards compatibility with the old interface where `Depends'
        # like fields were represented as a list of strings (shallow parsed).
        parsed_info['Depends'] = [text_type(r) for r in parsed_info['Depends']]
        assert unparse_control_fields(parsed_info) == deb822_package
        # Test compatibility with fields like `Depends' containing a string.
        parsed_info['Depends'] = deb822_package['Depends']
        assert unparse_control_fields(parsed_info) == deb822_package

    def test_control_field_merging(self):
        """Test the merging of control file fields."""
        defaults = Deb822(['Package: python-py2deb',
                           'Depends: python-deb-pkg-tools',
                           'Architecture: all'])
        # The field names of the dictionary with overrides are lower case on
        # purpose; control file merging should work properly regardless of
        # field name casing.
        overrides = Deb822(dict(version='1.0',
                                depends='python-pip, python-pip-accel',
                                architecture='amd64'))
        assert merge_control_fields(defaults, overrides) == \
            Deb822(['Package: python-py2deb',
                    'Version: 1.0',
                    'Depends: python-deb-pkg-tools, python-pip, python-pip-accel',
                    'Architecture: amd64'])

    def test_control_file_creation(self):
        """Test control file creation."""
        with Context() as context:
            directory = context.mkdtemp()
            # Use a non-existing subdirectory to verify that it's created.
            control_file = os.path.join(directory, 'DEBIAN', 'control')
            # Try to create a control file but omit some mandatory fields.
            self.assertRaises(ValueError, create_control_file, control_file, dict(Package='created-from-python'))
            # Now we'll provide all of the required fields to actually create the file.
            create_control_file(control_file, dict(
                Package='created-from-python',
                Description='whatever',
                Maintainer='Peter Odding',
                Version='1.0',
            ))
            # Load the control file to verify its contents.
            control_fields = load_control_file(control_file)
            # These fields were provided by us (the caller of create_control_file()).
            assert control_fields['Package'] == 'created-from-python'
            assert control_fields['Description'] == 'whatever'
            # This field was written as a default value.
            assert control_fields['Architecture'] == 'all'

    def test_control_file_patching_and_loading(self):
        """Test patching and loading of control files."""
        deb822_package = Deb822(['Package: unpatched-example',
                                 'Depends: some-dependency'])
        with Context() as finalizers:
            control_file = tempfile.mktemp()
            finalizers.register(os.unlink, control_file)
            with open(control_file, 'wb') as handle:
                deb822_package.dump(handle)
            returncode, output = run_cli(
                main, '--patch=%s' % control_file,
                '--set=Package: patched-example',
                '--set=Depends: another-dependency',
            )
            assert returncode == 0
            patched_fields = load_control_file(control_file)
            assert patched_fields['Package'] == 'patched-example'
            assert str(patched_fields['Depends']) == 'another-dependency, some-dependency'

    def test_version_comparison(self):
        """Test the comparison of version objects (under both implementations)."""
        self.version_comparison_helper()
        if version.have_python_apt:
            with PatchedAttribute(version, 'have_python_apt', False):
                self.version_comparison_helper()
                self.assertRaises(NotImplementedError, version.compare_versions_with_python_apt, '0.1', '<<', '0.2')

    def version_comparison_helper(self):
        """Test the comparison of version objects."""
        # V() shortcut for deb_pkg_tools.version.Version().
        V = version.Version
        # Check version sorting implemented on top of `=' and `<<' comparisons.
        expected_order = ['0.1', '0.5', '1.0', '2.0', '3.0', '1:0.4', '2:0.3']
        assert list(sorted(expected_order)) != expected_order
        assert list(sorted(map(V, expected_order))) == expected_order
        # Check each individual operator (to make sure the two implementations
        # agree). We use the Version() class for this so that we test both
        # compare_versions() and the Version() wrapper.
        # Test `>'.
        assert V('1.0') > V('0.5')      # usual semantics
        assert V('1:0.5') > V('2.0')    # unusual semantics
        assert not V('0.5') > V('2.0')  # sanity check
        # Test `>='.
        assert V('0.75') >= V('0.5')     # usual semantics
        assert V('0.50') >= V('0.5')     # usual semantics
        assert V('1:0.5') >= V('5.0')    # unusual semantics
        assert not V('0.2') >= V('0.5')  # sanity check
        # Test `<'.
        assert V('0.5') < V('1.0')      # usual semantics
        assert V('2.0') < V('1:0.5')    # unusual semantics
        assert not V('2.0') < V('0.5')  # sanity check
        # Test `<='.
        assert V('0.5') <= V('0.75')     # usual semantics
        assert V('0.5') <= V('0.50')     # usual semantics
        assert V('5.0') <= V('1:0.5')    # unusual semantics
        assert not V('0.5') <= V('0.2')  # sanity check
        # Test `=='.
        assert V('42') == V('42')        # usual semantics
        assert V('0.5') == V('0:0.5')    # unusual semantics
        assert not V('0.5') == V('1.0')  # sanity check
        # Test `!='.
        assert V('1') != V('0')            # usual semantics
        assert not V('0.5') != V('0:0.5')  # unusual semantics

    def test_relationship_parsing(self):
        """Test the parsing of Debian package relationship declarations."""
        # Happy path (no parsing errors).
        relationship_set = parse_depends('foo, bar (>= 1) | baz')
        assert relationship_set.relationships[0].name == 'foo'
        assert relationship_set.relationships[1].relationships[0].name == 'bar'
        assert relationship_set.relationships[1].relationships[0].operator == '>='
        assert relationship_set.relationships[1].relationships[0].version == '1'
        assert relationship_set.relationships[1].relationships[1].name == 'baz'
        assert parse_depends('foo (=1.0)') == RelationshipSet(VersionedRelationship(
            name='foo',
            operator='=',
            version='1.0',
        ))
        # Unhappy path (parsing errors).
        self.assertRaises(ValueError, parse_depends, 'foo (bar) (baz)')
        self.assertRaises(ValueError, parse_depends, 'foo (bar baz qux)')

    def test_architecture_restriction_parsing(self):
        """Test the parsing of architecture restrictions."""
        relationship_set = parse_depends('qux [i386 amd64]')
        assert relationship_set.relationships[0].name == 'qux'
        assert len(relationship_set.relationships[0].architectures) == 2
        assert 'i386' in relationship_set.relationships[0].architectures
        assert 'amd64' in relationship_set.relationships[0].architectures

    def test_relationship_unparsing(self):
        """Test the unparsing (serialization) of parsed relationship declarations."""
        def strip(text):
            return re.sub(r'\s+', '', text)
        relationship_set = parse_depends('foo, bar(>=1)|baz[i386]')
        assert text_type(relationship_set) == 'foo, bar (>= 1) | baz [i386]'
        assert strip(repr(relationship_set)) == strip("""
            RelationshipSet(
                Relationship(name='foo', architectures=()),
                AlternativeRelationship(
                    VersionedRelationship(name='bar', operator='>=', version='1', architectures=()),
                    Relationship(name='baz', architectures=('i386',))
                )
            )
        """)

    def test_relationship_evaluation(self):
        """Test the evaluation of package relationships."""
        # Relationships without versions.
        relationship_set = parse_depends('python')
        assert relationship_set.matches('python')
        assert not relationship_set.matches('python2.7')
        assert list(relationship_set.names) == ['python']
        # Alternatives (OR) without versions.
        relationship_set = parse_depends('python2.6 | python2.7')
        assert not relationship_set.matches('python2.5')
        assert relationship_set.matches('python2.6')
        assert relationship_set.matches('python2.7')
        assert not relationship_set.matches('python3.0')
        assert sorted(relationship_set.names) == ['python2.6', 'python2.7']
        # Combinations (AND) with versions.
        relationship_set = parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
        assert not relationship_set.matches('python', '2.5')
        assert relationship_set.matches('python', '2.6')
        assert relationship_set.matches('python', '2.7')
        assert not relationship_set.matches('python', '3.0')
        assert relationship_set.matches('python', '3.4')
        assert list(relationship_set.names) == ['python']
        # Testing for matches without providing a version is valid (should not
        # raise an error) but will never match a relationship with a version.
        relationship_set = parse_depends('python (>= 2.6), python (<< 3)')
        assert relationship_set.matches('python', '2.7')
        assert not relationship_set.matches('python')
        assert list(relationship_set.names) == ['python']
        # Distinguishing between packages whose name was matched but whose
        # version didn't match vs packages whose name wasn't matched.
        relationship_set = parse_depends('python (>= 2.6), python (<< 3) | python (>= 3.4)')
        assert relationship_set.matches('python', '2.7') is True  # name and version match
        assert relationship_set.matches('python', '2.5') is False  # name matched, version didn't
        assert relationship_set.matches('python2.6') is None  # name didn't match
        assert relationship_set.matches('python', '3.0') is False  # name in alternative matched, version didn't
        assert list(relationship_set.names) == ['python']

    def test_custom_pretty_printer(self):
        """Test pretty printing of deb822 objects and parsed relationships."""
        printer = CustomPrettyPrinter()
        # Test pretty printing of debian.deb822.Deb822 objects.
        deb822_object = deb822_from_string('''
            Package: pretty-printed-control-fields
            Version: 1.0
            Architecture: all
        ''')
        formatted_object = printer.pformat(deb822_object)
        assert normalize_repr_output(formatted_object) == normalize_repr_output('''
            {'Architecture': u'all',
             'Package': u'pretty-printed-control-fields',
             'Version': u'1.0'}
        ''')
        # Test pretty printing of RelationshipSet objects.
        relationship_set = parse_depends('python-deb-pkg-tools, python-pip, python-pip-accel')
        formatted_object = printer.pformat(relationship_set)
        assert normalize_repr_output(formatted_object) == normalize_repr_output('''
            RelationshipSet(Relationship(name='python-deb-pkg-tools', architectures=()),
                            Relationship(name='python-pip', architectures=()),
                            Relationship(name='python-pip-accel', architectures=()))
        ''')

    def test_filename_parsing(self):
        """Test filename parsing."""
        # Test the happy path.
        filename = '/var/cache/apt/archives/python2.7_2.7.3-0ubuntu3.4_amd64.deb'
        components = parse_filename(filename)
        assert components.filename == filename
        assert components.name == 'python2.7'
        assert components.version == '2.7.3-0ubuntu3.4'
        assert components.architecture == 'amd64'
        # Test the unhappy paths.
        self.assertRaises(ValueError, parse_filename, 'python2.7_2.7.3-0ubuntu3.4_amd64.not-a-deb')
        self.assertRaises(ValueError, parse_filename, 'python2.7.deb')

    def test_find_object_files(self):
        """Test the :func:`deb_pkg_tools.package.find_object_files()` function."""
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            shutil.copy(__file__, directory)
            shutil.copy(sys.executable, directory)
            object_files = find_object_files(directory)
            assert len(object_files) == 1
            assert object_files[0] == os.path.join(directory, os.path.basename(sys.executable))

    def test_find_system_dependencies(self):
        """Test the :func:`deb_pkg_tools.package.find_system_dependencies()` function."""
        dependencies = find_system_dependencies(['/usr/bin/python'])
        assert len(dependencies) >= 1
        assert any(re.match(r'^libc\d+\b', d) for d in dependencies)

    def test_package_building(self, repository=None, overrides={}, contents={}):
        """Test building of Debian binary packages."""
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
                    makedirs(directory)
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
                makedirs(os.path.join(build_directory, 'tmp', '.git'))
                # Create a file that should be cleaned up by clean_package_tree().
                with open(os.path.join(build_directory, 'tmp', '.gitignore'), 'w') as handle:
                    handle.write('\n')
            # Build the package (without any contents :-).
            returncode, output = run_cli(main, '--build', build_directory)
            assert returncode == 0
            package_file = os.path.join(tempfile.gettempdir(),
                                        '%s_%s_%s.deb' % (control_fields['Package'],
                                                          control_fields['Version'],
                                                          control_fields['Architecture']))
            assert os.path.isfile(package_file)
            if repository:
                shutil.move(package_file, repository)
                return os.path.join(repository, os.path.basename(package_file))
            else:
                finalizers.register(os.unlink, package_file)
                # Verify the package metadata.
                fields, contents = inspect_package(package_file)
                for name in TEST_PACKAGE_FIELDS:
                    assert fields[name] == TEST_PACKAGE_FIELDS[name]
                # Verify that the package contains the `/' and `/tmp'
                # directories (since it doesn't contain any actual files).
                assert contents['/'].permissions[0] == 'd'
                assert contents['/'].permissions[1:] == 'rwxr-xr-x'
                assert contents['/'].owner == 'root'
                assert contents['/'].group == 'root'
                assert contents['/tmp/'].permissions[0] == 'd'
                assert contents['/tmp/'].owner == 'root'
                assert contents['/tmp/'].group == 'root'
                # Verify that clean_package_tree() cleaned up properly
                # (`/tmp/.git' and `/tmp/.gitignore' have been cleaned up).
                assert '/tmp/.git/' not in contents
                assert '/tmp/.gitignore' not in contents
                return package_file

    def test_command_line_interface(self):
        """Test the command line interface."""
        if SKIP_SLOW_TESTS:
            return self.skipTest("skipping slow tests")
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            # Test `deb-pkg-tools --inspect PKG'.
            package_file = self.test_package_building(directory)
            returncode, output = run_cli(main, '--verbose', '--inspect', package_file)
            assert returncode == 0
            lines = output.splitlines()
            for field, value in TEST_PACKAGE_FIELDS.items():
                assert match('^ - %s: (.+)$' % field, lines) == value
            # Test `deb-pkg-tools --update=DIR' with a non-existing directory.
            returncode, output = run_cli(main, '--update', '/a/directory/that/will/never/exist')
            assert returncode != 0

    def test_with_repo_cli(self):
        """Test ``deb-pkg-tools --with-repo``."""
        if SKIP_SLOW_TESTS:
            return self.skipTest("skipping slow tests")
        elif os.getuid() != 0:
            return self.skipTest("need superuser privileges")
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            self.test_package_building(directory)
            with CaptureOutput() as capturer:
                run_cli(
                    main, '--with-repo=%s' % directory,
                    'apt-cache show %s' % TEST_PACKAGE_NAME,
                )
                # Check whether apt-cache sees the package.
                expected_line = "Package: %s" % TEST_PACKAGE_NAME
                assert expected_line in capturer.get_lines()

    def test_check_package(self):
        """Test the command line interface for static analysis of package archives."""
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            root_package, conflicting_package = self.create_version_conflict(directory)
            # This *should* raise SystemExit.
            returncode, output = run_cli(main, '--check', root_package)
            assert returncode != 0
            # Test for lack of duplicate files.
            os.unlink(conflicting_package)
            # This should *not* raise SystemExit.
            returncode, output = run_cli(main, '--check', root_package)
            assert returncode == 0

    def test_version_conflicts_check(self):
        """Test static analysis of version conflicts."""
        with Context() as finalizers:
            # Check that version conflicts raise an exception.
            directory = finalizers.mkdtemp()
            root_package, conflicting_package = self.create_version_conflict(directory)
            packages_to_scan = collect_related_packages(root_package)
            # Test the duplicate files check.
            self.assertRaises(VersionConflictFound, check_version_conflicts, packages_to_scan, self.package_cache)
            # Test for lack of duplicate files.
            os.unlink(conflicting_package)
            assert check_version_conflicts(packages_to_scan, cache=self.package_cache) is None

    def create_version_conflict(self, directory):
        """Build a directory of packages with a version conflict."""
        root_package = self.test_package_building(directory, overrides=dict(
            Package='deb-pkg-tools-package-1',
            Depends='deb-pkg-tools-package-2 (=1)',
        ))
        self.test_package_building(directory, overrides=dict(
            Package='deb-pkg-tools-package-2',
            Version='1',
        ))
        conflicting_package = self.test_package_building(directory, overrides=dict(
            Package='deb-pkg-tools-package-2',
            Version='2',
        ))
        return root_package, conflicting_package

    def test_duplicates_check(self):
        """Test static analysis of duplicate files."""
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
        """Test the command line interface for collection of related packages."""
        with Context() as finalizers:
            source_directory = finalizers.mkdtemp()
            target_directory = finalizers.mkdtemp()
            package1 = self.test_package_building(source_directory, overrides=dict(
                Package='deb-pkg-tools-package-1',
                Depends='deb-pkg-tools-package-2',
            ))
            package2 = self.test_package_building(source_directory, overrides=dict(
                Package='deb-pkg-tools-package-2',
                Depends='deb-pkg-tools-package-3',
            ))
            package3 = self.test_package_building(source_directory, overrides=dict(
                Package='deb-pkg-tools-package-3',
            ))
            returncode, output = run_cli(
                main, '--yes',
                '--collect=%s' % target_directory,
                package1,
            )
            assert returncode == 0
            assert sorted(os.listdir(target_directory)) == \
                sorted(map(os.path.basename, [package1, package2, package3]))

    def test_collect_packages_preference_for_newer_versions(self):
        """Test the preference of package collection for newer versions."""
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            package1 = self.test_package_building(directory, overrides=dict(
                Package='deb-pkg-tools-package-1',
                Depends='deb-pkg-tools-package-2',
            ))
            package2_1 = self.test_package_building(directory, overrides=dict(
                Package='deb-pkg-tools-package-2',
                Version='1',
                Depends='deb-pkg-tools-package-3 (= 1)',
            ))
            package2_2 = self.test_package_building(directory, overrides=dict(
                Package='deb-pkg-tools-package-2',
                Version='2',
                Depends='deb-pkg-tools-package-3 (= 2)',
            ))
            package3_1 = self.test_package_building(directory, overrides=dict(
                Package='deb-pkg-tools-package-3',
                Version='1',
            ))
            package3_2 = self.test_package_building(directory, overrides=dict(
                Package='deb-pkg-tools-package-3',
                Version='2',
            ))
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
        """Test conflict resolution in collection of related packages."""
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            # The following names are a bit confusing, this is to enforce
            # implicit sorting on file system level (exposing an otherwise
            # unnoticed bug).
            package_a = self.test_package_building(directory, overrides=dict(
                Package='package-a',
                Depends='package-b, package-c',
            ))
            package_b = self.test_package_building(directory, overrides=dict(
                Package='package-b',
                Depends='package-d',
            ))
            package_c = self.test_package_building(directory, overrides=dict(
                Package='package-c',
                Depends='package-d (= 1)',
            ))
            package_d1 = self.test_package_building(directory, overrides=dict(
                Package='package-d',
                Version='1',
            ))
            package_d2 = self.test_package_building(directory, overrides=dict(
                Package='package-d',
                Version='2',
            ))
            related_packages = [p.filename for p in collect_related_packages(package_a, cache=self.package_cache)]
            # Make sure package-b was collected.
            assert package_b in related_packages
            # Make sure package-c was collected.
            assert package_c in related_packages
            # Make sure package-d1 was collected.
            assert package_d1 in related_packages
            # Make sure package-d2 wasn't collected.
            assert package_d2 not in related_packages

    def test_collect_packages_with_prompt(self):
        """Test the confirmation prompt during interactive package collection."""
        with Context() as finalizers:
            # Temporarily change stdin to respond with `y' (for `yes').
            finalizers.register(setattr, sys, 'stdin', sys.stdin)
            sys.stdin = StringIO('y')
            # Prepare some packages to collect.
            source_directory = finalizers.mkdtemp()
            target_directory = finalizers.mkdtemp()
            package1 = self.test_package_building(source_directory, overrides=dict(
                Package='deb-pkg-tools-package-1',
                Depends='deb-pkg-tools-package-2',
            ))
            package2 = self.test_package_building(source_directory, overrides=dict(
                Package='deb-pkg-tools-package-2',
            ))
            # Run `deb-pkg-tools --collect' ...
            returncode, output = run_cli(main, '--collect=%s' % target_directory, package1)
            assert returncode == 0
            assert sorted(os.listdir(target_directory)) == sorted(map(os.path.basename, [package1, package2]))

    def test_collect_packages_concurrent(self):
        """Test concurrent collection of related packages."""
        with Context() as finalizers:
            source_directory = finalizers.mkdtemp()
            target_directory = finalizers.mkdtemp()
            # Prepare some packages to collect.
            package1 = self.test_package_building(source_directory, overrides=dict(
                Package='package-1',
                Depends='package-3',
            ))
            package2 = self.test_package_building(source_directory, overrides=dict(
                Package='package-2',
                Depends='package-4',
            ))
            package3 = self.test_package_building(source_directory, overrides=dict(
                Package='package-3',
            ))
            package4 = self.test_package_building(source_directory, overrides=dict(
                Package='package-4',
            ))
            # Run `deb-pkg-tools --collect' ...
            returncode, output = run_cli(
                main, '--collect=%s' % target_directory,
                '--yes', package1, package2,
            )
            assert returncode == 0
            # Make sure the expected packages were promoted.
            assert sorted(os.listdir(target_directory)) == \
                sorted(map(os.path.basename, [package1, package2, package3, package4]))

    def test_repository_creation(self, preserve=False):
        """Test the creation of trivial repositories."""
        if SKIP_SLOW_TESTS:
            return self.skipTest("skipping slow tests")
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
            update_repository(repo_dir,
                              release_fields=dict(description=TEST_REPO_DESCRIPTION),
                              cache=self.package_cache)
            assert os.path.isfile(os.path.join(repo_dir, 'Packages'))
            assert os.path.isfile(os.path.join(repo_dir, 'Packages.gz'))
            assert os.path.isfile(os.path.join(repo_dir, 'Release'))
            with open(os.path.join(repo_dir, 'Release')) as handle:
                fields = Deb822(handle)
                assert fields['Origin'] == TEST_REPO_ORIGIN
                assert fields['Description'] == TEST_REPO_DESCRIPTION
            if not apt_supports_trusted_option():
                assert os.path.isfile(os.path.join(repo_dir, 'Release.gpg'))
            return repo_dir

    def test_repository_activation(self):
        """Test the activation of trivial repositories."""
        if SKIP_SLOW_TESTS:
            return self.skipTest("skipping slow tests")
        elif os.getuid() != 0:
            return self.skipTest("need superuser privileges")
        repository = self.test_repository_creation(preserve=True)
        returncode, output = run_cli(main, '-vv', '--activate-repo=%s' % repository)
        assert returncode == 0
        try:
            handle = os.popen('apt-cache show %s' % TEST_PACKAGE_NAME)
            fields = Deb822(handle)
            assert fields['Package'] == TEST_PACKAGE_NAME
        finally:
            returncode, output = run_cli(main, '-vv', '--deactivate-repo=%s' % repository)
            assert returncode == 0

    def test_repository_activation_fallback(self):
        """Test the activation of trivial repositories using the fall-back mechanism."""
        # If we skipped the GPG key handling in test_repository_activation()
        # because apt supports the [trusted=yes] option, we re-run the test
        # *including* GPG key handling because we want this to be tested...
        from deb_pkg_tools import repo
        if repo.apt_supports_trusted_option():
            with PatchedAttribute(repo, 'apt_supports_trusted_option', lambda: False):
                self.test_repository_activation()

    def test_gpg_key_generation(self):
        """Test automatic GPG key generation."""
        if SKIP_SLOW_TESTS:
            return self.skipTest("skipping slow tests")
        with Context() as finalizers:
            directory = finalizers.mkdtemp()
            # Generate a named GPG key on the spot.
            key = GPGKey(
                description="GPG key pair generated for unit tests",
                directory=directory,
                name="deb-pkg-tools test suite",
            )
            # Make sure a key pair was generated.
            assert key.existing_files
            # Make sure an identifier can be extracted from the key.
            assert re.match('^[0-9A-Fa-f]{10,}$', key.identifier)

    def test_gpg_key_error_handling(self):
        """Test explicit error handling of GPG key generation."""
        from deb_pkg_tools import gpg
        with PatchedAttribute(gpg, 'have_updated_gnupg', lambda: False):
            with Context() as finalizers:
                directory = finalizers.mkdtemp()
                options = dict(
                    key_id='12345',
                    public_key_file=os.path.join(directory, 'test.pub'),
                    secret_key_file=os.path.join(directory, 'test.sec'),
                )
                touch(options['public_key_file'])
                self.assertRaises(EnvironmentError, GPGKey, **options)
                os.unlink(options['public_key_file'])
                touch(options['secret_key_file'])
                self.assertRaises(EnvironmentError, GPGKey, **options)


def match(pattern, lines):
    """Get the regular expression match in an iterable of lines."""
    for line in lines:
        m = re.match(pattern, line)
        if m:
            return m.group(1)


def normalize_repr_output(expression):
    """
    Enable string comparison between :func:`repr()` output on different Python versions.

    This function enables string comparison between :func:`repr()` output on
    Python 2 (where Unicode strings have the ``u`` prefix) and Python 3 (where
    Unicode strings are the default and no prefix is emitted by
    :func:`repr()`).
    """
    return re.sub(r'\bu([\'"])', r'\1', dedent(expression).strip())


class Context(object):

    """Context manager for simple and reliable finalizers."""

    def __init__(self):
        """Initialize a :class:`Context` object."""
        self.finalizers = []

    def __enter__(self):
        """Enter the context."""
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Leave the context (running the finalizers)."""
        for finalizer in reversed(self.finalizers):
            finalizer()
        self.finalizers = []

    def register(self, *args, **kw):
        """Register a finalizer."""
        self.finalizers.append(functools.partial(*args, **kw))

    def mkdtemp(self, *args, **kw):
        """Create a temporary directory that will be cleaned up when the context ends."""
        directory = tempfile.mkdtemp(*args, **kw)
        self.register(shutil.rmtree, directory)
        return directory
