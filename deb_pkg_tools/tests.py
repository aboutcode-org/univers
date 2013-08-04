# Debian packaging tools: Automated tests.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: August 4, 2013
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
                                   unparse_control_fields)
from deb_pkg_tools.repo import (activate_repository, deactivate_repository,
                                update_repository, FailedToSignRelease)
from deb_pkg_tools.package import build_package, inspect_package

# Initialize a logger.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TEST_PACKAGE_NAME = 'deb-pkg-tools-demo-package'
TEST_PACKAGE_FIELDS = Deb822(dict(Architecture='all',
                                  Description='Nothing to see here, move along',
                                  Maintainer='Peter Odding',
                                  Package=TEST_PACKAGE_NAME,
                                  Version='0.1'))

class DebPkgToolsTestCase(unittest.TestCase):

    def setUp(self):
        coloredlogs.install()

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
        overrides = Deb822(['Version: 1.0',
                            'Depends: python-pip, python-pip-accel',
                            'Architecture: amd64'])
        self.assertEqual(merge_control_fields(defaults, overrides),
                         Deb822(['Package: python-py2deb',
                                 'Version: 1.0',
                                 'Depends: python-deb-pkg-tools, python-pip, python-pip-accel',
                                 'Architecture: amd64']))

    def test_package_building(self, repository=None):
        directory = tempfile.mkdtemp()
        destructors = [functools.partial(shutil.rmtree, directory)]
        try:
            # Create the package template.
            os.mkdir(os.path.join(directory, 'DEBIAN'))
            with open(os.path.join(directory, 'DEBIAN', 'control'), 'w') as handle:
                TEST_PACKAGE_FIELDS.dump(handle)
            # Build the package (without any contents :-).
            package_file = build_package(directory)
            self.assertTrue(os.path.isfile(package_file))
            if repository:
                shutil.move(package_file, repository)
            else:
                destructors.append(functools.partial(os.unlink, package_file))
                # Verify the package metadata.
                fields = inspect_package(package_file)
                for name in TEST_PACKAGE_FIELDS:
                    self.assertEqual(fields[name], TEST_PACKAGE_FIELDS[name])
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
            try:
                update_repository(repository)
            except FailedToSignRelease:
                logger.warn("Failed to sign `Release' file! (assuming you don't have a private GPG key)")
                was_signed = False
            else:
                self.assertTrue(os.path.isfile(os.path.join(repository, 'Release.gpg')))
                was_signed = True
            self.assertTrue(os.path.isfile(os.path.join(repository, 'Packages')))
            self.assertTrue(os.path.isfile(os.path.join(repository, 'Packages.gz')))
            self.assertTrue(os.path.isfile(os.path.join(repository, 'Release')))
            return repository, was_signed
        finally:
            for partial in destructors:
                partial()

    def test_repository_activation(self):
        """
        To-do: Only when os.getuid() == 0?
        """
        if os.getuid() != 0:
            logger.warn("Skipping repository activation test because it requires root access!")
        else:
            repository, was_signed = self.test_repository_creation(preserve=True)
            if not was_signed:
                logger.warn("Skipping repository activation test because it requires a signed repository!")
            else:
                activate_repository(repository)
                try:
                    handle = os.popen('apt-cache show %s' % TEST_PACKAGE_NAME)
                    fields = Deb822(handle)
                    self.assertEqual(fields['Package'], TEST_PACKAGE_NAME)
                finally:
                    deactivate_repository(repository)

if __name__ == '__main__':
    unittest.main()

# vim: ts=4 sw=4 et
