# Debian packaging tools: Automated tests.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 16, 2013
# URL: https://github.com/xolox/python-deb-pkg-tools

# Standard library modules.
import functools
import logging
import os
import shutil
import tempfile
import unittest

# External dependencies.
import coloredlogs
from debian.deb822 import Deb822

# Modules included in our package.
from deb_pkg_tools.control import (merge_control_fields, parse_control_fields,
                                   patch_control_file, unparse_control_fields)
from deb_pkg_tools.repo import (activate_repository,
                                apt_supports_trusted_option,
                                deactivate_repository,
                                update_repository)
from deb_pkg_tools.package import build_package, inspect_package

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
            with open(control_file, 'w') as handle:
                deb822_package.dump(handle)
            patch_control_file(control_file, dict(Package='patched-example',
                                                  Depends='another-dependency'))
            with open(control_file) as handle:
                patched_fields = Deb822(handle)
            self.assertEqual(patched_fields['Package'], 'patched-example')
            self.assertEqual(patched_fields['Depends'], 'another-dependency, some-dependency')
        finally:
            os.unlink(control_file)

    def test_package_building(self, repository=None):
        directory = tempfile.mkdtemp()
        destructors = [functools.partial(shutil.rmtree, directory)]
        try:
            # Create the package template.
            os.mkdir(os.path.join(directory, 'DEBIAN'))
            with open(os.path.join(directory, 'DEBIAN', 'control'), 'w') as handle:
                TEST_PACKAGE_FIELDS.dump(handle)
            with open(os.path.join(directory, 'DEBIAN', 'conffiles'), 'w') as handle:
                handle.write('/etc/file1\n')
                handle.write('/etc/file2\n')
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
            package_file = build_package(directory)
            self.assertTrue(os.path.isfile(package_file))
            if repository:
                shutil.move(package_file, repository)
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
        finally:
            for partial in destructors:
                partial()

    def test_repository_creation(self, preserve=False):
        repository = tempfile.mkdtemp()
        destructors = []
        if not preserve:
            destructors.append(functools.partial(shutil.rmtree, repository))
        try:
            self.test_package_building(repository)
            update_repository(repository)
            self.assertTrue(os.path.isfile(os.path.join(repository, 'Packages')))
            self.assertTrue(os.path.isfile(os.path.join(repository, 'Packages.gz')))
            self.assertTrue(os.path.isfile(os.path.join(repository, 'Release')))
            if not apt_supports_trusted_option():
                self.assertTrue(os.path.isfile(os.path.join(repository, 'Release.gpg')))
            return repository
        finally:
            for partial in destructors:
                partial()

    def test_repository_activation(self):
        if os.getuid() != 0:
            logger.warn("Skipping repository activation test because it requires root access!")
        else:
            repository = self.test_repository_creation(preserve=True)
            activate_repository(repository)
            try:
                handle = os.popen('apt-cache show %s' % TEST_PACKAGE_NAME)
                fields = Deb822(handle)
                self.assertEqual(fields['Package'], TEST_PACKAGE_NAME)
            finally:
                deactivate_repository(repository)
            # XXX If we skipped the GPG key handling because apt supports the
            # [trusted=yes] option, re-run the test *including* GPG key
            # handling (we want this to be tested...).
            import deb_pkg_tools
            if deb_pkg_tools.repo.apt_supports_trusted_option():
                deb_pkg_tools.repo.trusted_option_supported = False
                self.test_repository_activation()

def touch(filename, contents='\n'):
    with open(filename, 'w') as handle:
        handle.write(contents)

if __name__ == '__main__':
    unittest.main()

# vim: ts=4 sw=4 et
