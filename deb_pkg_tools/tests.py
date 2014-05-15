# Debian packaging tools: Automated tests.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 16, 2014
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
import unittest

try:
    # Python 2.x.
    from StringIO import StringIO
except ImportError:
    # Python 3.x.
    from io import StringIO

# External dependencies.
import coloredlogs
from debian.deb822 import Deb822

# Modules included in our package.
from deb_pkg_tools.cli import main
from deb_pkg_tools.control import (merge_control_fields,
                                   parse_control_fields,
                                   unparse_control_fields)
from deb_pkg_tools.gpg import GPGKey
from deb_pkg_tools.package import inspect_package, parse_filename
from deb_pkg_tools.repo import (apt_supports_trusted_option,
                                update_repository)

# Initialize a logger.
logger = logging.getLogger(__name__)

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
                          'Depends': ['python-deb-pkg-tools', 'python-pip', 'python-pip-accel'],
                          'Installed-Size': 42})
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

    def test_filename_parsing(self):
        # Test the happy path.
        components = parse_filename('/var/cache/apt/archives/python2.7_2.7.3-0ubuntu3.4_amd64.deb')
        self.assertEqual(components.name, 'python2.7')
        self.assertEqual(components.version, '2.7.3-0ubuntu3.4')
        self.assertEqual(components.architecture, 'amd64')
        self.assertEqual(components, ('python2.7', '2.7.3-0ubuntu3.4', 'amd64'))
        # Test the unhappy paths.
        self.assertRaises(ValueError, parse_filename, 'python2.7_2.7.3-0ubuntu3.4_amd64.not-a-deb')
        self.assertRaises(ValueError, parse_filename, 'python2.7.deb')

    def test_package_building(self, repository=None):
        directory = tempfile.mkdtemp()
        destructors = [functools.partial(shutil.rmtree, directory)]
        try:
            # Create the package template.
            os.mkdir(os.path.join(directory, 'DEBIAN'))
            with open(os.path.join(directory, 'DEBIAN', 'control'), 'wb') as handle:
                TEST_PACKAGE_FIELDS.dump(handle)
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
                                        '%s_%s_%s.deb' % (TEST_PACKAGE_FIELDS['Package'],
                                                          TEST_PACKAGE_FIELDS['Version'],
                                                          TEST_PACKAGE_FIELDS['Architecture']))
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
            call('--with-repo=%s' % directory, 'apt-cache show %s' % TEST_PACKAGE_NAME)
        finally:
            for partial in destructors:
                partial()

    def test_repository_creation(self, preserve=False):
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
                self.assertEquals(fields['Origin'], TEST_REPO_ORIGIN)
                self.assertEquals(fields['Description'], TEST_REPO_DESCRIPTION)
            if not apt_supports_trusted_option():
                self.assertTrue(os.path.isfile(os.path.join(repo_dir, 'Release.gpg')))
            return repo_dir
        finally:
            for partial in destructors:
                partial()

    def test_repository_activation(self):
        if os.getuid() != 0:
            logger.warn("Skipping repository activation test because it requires root access!")
        else:
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
            self.assertEquals(os.path.basename(default_key.secret_key_file), 'secring.gpg')
            self.assertEquals(os.path.basename(default_key.public_key_file), 'pubring.gpg')
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

if __name__ == '__main__':
    unittest.main()

# vim: ts=4 sw=4 et
