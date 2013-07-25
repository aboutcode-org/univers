# Debian packaging tools: Automated tests.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: July 26, 2013
# URL: https://github.com/xolox/python-deb-pkg-tools

# Standard library modules.
import functools
import logging
import os
import shutil
import tempfile
import textwrap
import unittest

# External dependencies.
import coloredlogs
from debian.deb822 import Deb822

# Modules included in our package.
from deb_pkg_tools.control import parse_control_fields, merge_control_fields
from deb_pkg_tools.repo import update_repository, FailedToSignRelease
from deb_pkg_tools.package import build_package, inspect_package

# Initialize a logger.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class DebPkgToolsTestCase(unittest.TestCase):

    def setUp(self):
        coloredlogs.install()

    def test_control_field_parsing(self):
        deb822_package = Deb822(['Package: python-py2deb',
                                 'Depends: python-deb-pkg-tools, python-pip, python-pip-accel'])
        self.assertEqual(parse_control_fields(deb822_package),
                         dict(Package='python-py2deb',
                              Depends=['python-deb-pkg-tools', 'python-pip', 'python-pip-accel']))

    def test_control_field_merging(self):
        defaults = Deb822(['Package: python-py2deb',
                           'Depends: python-deb-pkg-tools'])
        overrides = Deb822(['Depends: python-pip, python-pip-accel'])
        self.assertEqual(merge_control_fields(defaults, overrides),
                         Deb822(['Package: python-py2deb',
                                 'Depends: python-deb-pkg-tools, python-pip, python-pip-accel']))

    def test_package_building(self, repository=None):
        directory = tempfile.mkdtemp()
        destructors = [functools.partial(shutil.rmtree, directory)]
        try:
            # Create the package template.
            os.mkdir(os.path.join(directory, 'DEBIAN'))
            with open(os.path.join(directory, 'DEBIAN', 'control'), 'w') as handle:
                handle.write(textwrap.dedent('''
                    Architecture: all
                    Description: Nothing to see here, move along
                    Maintainer: Peter Odding
                    Package: just-a-test
                    Version: 0.1
                ''').strip())
            # Build the package (without any contents :-).
            package_file = build_package(directory)
            self.assertTrue(os.path.isfile(package_file))
            if repository:
                shutil.move(package_file, repository)
                return
            destructors.append(functools.partial(os.unlink, package_file))
            # Verify the package metadata.
            fields = inspect_package(package_file)
            self.assertEqual(fields['Architecture'], 'all')
            self.assertEqual(fields['Description'], 'Nothing to see here, move along')
            self.assertEqual(fields['Maintainer'], 'Peter Odding')
            self.assertEqual(fields['Package'], 'just-a-test')
            self.assertEqual(fields['Version'], '0.1')
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
                self.assertTrue(os.path.isfile(os.path.join(repository, 'Release.gpg')))
            except FailedToSignRelease:
                logger.warn("Failed to sign `Release' file; assuming you don't have a private GPG key.")
            self.assertTrue(os.path.isfile(os.path.join(repository, 'Packages')))
            self.assertTrue(os.path.isfile(os.path.join(repository, 'Packages.gz')))
            self.assertTrue(os.path.isfile(os.path.join(repository, 'Release')))
        finally:
            for partial in destructors:
                partial()

    def test_repository_activation(self):
        """
        To-do: Only when os.getuid() == 0?
        """

if __name__ == '__main__':
    unittest.main()

# vim: ts=4 sw=4 et
