# Debian packaging tools: Package manipulation.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: August 11, 2013
# URL: https://github.com/xolox/python-deb-pkg-tools

"""
Package manipulation
====================

This module provides functions to build and inspect Debian package archives
(``*.deb`` files).
"""

# Standard library modules.
import logging
import os.path
import pipes
import shutil
import StringIO
import tempfile

# External dependencies.
from debian.deb822 import Deb822
from humanfriendly import format_path

# Modules included in our package.
from deb_pkg_tools.utils import execute, same_filesystem

# Initialize a logger.
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def inspect_package(archive):
    """
    Get the metadata from a ``*.deb`` archive.

    :param archive: The pathname of an existing ``*.deb`` archive.
    :returns: A dictionary with control file fields (an instance
              of :py:func:`debian.deb822.Deb822`).

    To give you an idea of what the result looks like:

    >>> from deb_pkg_tools.package import inspect_package
    >>> inspect_package('/var/cache/apt/archives/python2.7_2.7.3-0ubuntu3.2_amd64.deb')
    {'Architecture': 'amd64',
     'Conflicts': 'python-profiler (<= 2.7.1-2)',
     'Depends': 'python2.7-minimal (= 2.7.3-0ubuntu3.2), mime-support, libbz2-1.0, libc6 (>= 2.15), libdb5.1, libexpat1 (>= 1.95.8), libgcc1 (>= 1:4.1.1), libncursesw5 (>= 5.6+20070908), libreadline6 (>= 6.0), libsqlite3-0 (>= 3.5.9), libtinfo5',
     'Description': 'Interactive high-level object-oriented language ...',
     'Installed-Size': '8779',
     'Maintainer': 'Ubuntu Core Developers <ubuntu-devel-discuss@lists.ubuntu.com>',
     'Multi-Arch': 'allowed',
     'Original-Maintainer': 'Matthias Klose <doko@debian.org>',
     'Package': 'python2.7',
     'Priority': 'optional',
     'Provides': 'python-argparse, python2.7-argparse, python2.7-celementtree, python2.7-cjkcodecs, python2.7-ctypes, python2.7-elementtree, python2.7-profiler, python2.7-wsgiref',
     'Replaces': 'python-profiler (<= 2.7.1-2)',
     'Section': 'python',
     'Suggests': 'python2.7-doc, binutils',
     'Version': '2.7.3-0ubuntu3.2'}
    """
    return Deb822(StringIO.StringIO(execute('dpkg-deb', '-f', archive, capture=True)))

def build_package(directory, repository=None, check_package=True):
    """
    Create a Debian package using the ``dpkg-deb --build`` command. The
    ``dpkg-deb --build`` command requires a certain directory tree layout and
    specific files; for more information about this topic please refer to the
    `Debian Binary Package Building HOWTO`_. The :py:func:`build_package()`
    function performs the following steps to build a package:

    1. Copies the files in the source directory to a temporary build directory.
    2. Updates the Installed-Size_ field in the ``DEBIAN/control`` file
       based on the size of the given directory (using
       :py:func:`update_installed_size()`).
    3. Sets the owner and group of all files to ``root`` because this is the
       only user account guaranteed to always be available. This uses the
       ``fakeroot`` command so you don't actually need ``root`` access to use
       :py:func:`build_package()`.
    4. Runs the command ``fakeroot dpkg-deb --build`` to generate a Debian
       package from the files in the build directory.
    5. Runs Lintian_ to check the resulting package archive for possible
       issues. The result of Lintian is purely informational: If 'errors' are
       reported and Lintian exits with a nonzero status code, this is ignored
       by :py:func:`build_package()`.

    If any of the external commands invoked by this function fail,
    :py:exc:`deb_pkg_tools.utils.ExternalCommandFailed` is raised. If this
    function returns without raising an exception, the generated Debian package
    can be found in the parent directory of the directory given as the first
    argument.

    :param directory: The pathname of a directory tree suitable for packaging
                      with ``dpkg-deb --build``.
    :param repository: The pathname of an existing directory where the
                       generated ``*.deb`` archive should be stored (defaults
                       to the system wide temporary directory).
    :param check_package: If ``True`` (the default) Lintian_ is run to check
                          the resulting package archive for possible issues.
    :returns: The pathname of the generated ``*.deb`` archive.

    .. _Debian Binary Package Building HOWTO: http://tldp.org/HOWTO/html_single/Debian-Binary-Package-Building-HOWTO/
    .. _Installed-Size: http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Installed-Size
    .. _Lintian: http://lintian.debian.org/
    """
    build_directory = tempfile.mkdtemp()
    logger.debug("Created build directory: %s", format_path(build_directory))
    if not repository:
        repository = tempfile.gettempdir()
    package_file = os.path.join(repository, determine_package_archive(directory))
    logger.debug("Preparing to build package: %s", format_path(package_file))
    try:
        copy_package_files(directory, build_directory)
        clean_package_tree(build_directory)
        update_installed_size(build_directory)
        # Make sure all files included in the package are owned by `root'
        # (the only account guaranteed to exist on all systems).
        logger.debug("Resetting file ownership (to root:root) ..")
        execute('fakeroot', 'chown', '-R', 'root:root', build_directory)
        # Build the package using `dpkg-deb'.
        logger.info("Building package in %s ..", format_path(build_directory))
        execute('fakeroot', 'dpkg-deb', '--build', build_directory, package_file)
        # Check the package for possible issues using Lintian?
        if check_package:
            if not os.access('/usr/bin/lintian', os.X_OK):
                logger.warn("Lintian is not installed, skipping sanity check.")
            else:
                logger.info("Checking package for issues using Lintian ..")
                lintian_command = ['lintian']
                if os.getuid() == 0:
                    lintian_command.append('--allow-root')
                lintian_command.append('--color=auto')
                lintian_command.append(package_file)
                execute(*lintian_command, check=False)
        return package_file
    finally:
        logger.debug("Removing build directory: %s", build_directory)
        shutil.rmtree(build_directory)

def determine_package_archive(directory):
    """
    Determine the name of the ``*.deb`` package archive that will be generated
    from a directory tree suitable for packaging with ``dpkg-deb --build``.

    :param source_directory: The pathname of a directory tree suitable for
                             packaging with ``dpkg-deb --build``.
    :returns: The filename of the ``*.deb`` archive to be built.
    """
    with open(os.path.join(directory, 'DEBIAN', 'control')) as control_file:
        fields = Deb822(control_file)
    components = [fields['Package'], fields['Version']]
    architecture = fields.get('Architecture', '').strip()
    if architecture:
        components.append(architecture)
    return '%s.deb' % '_'.join(components)

def copy_package_files(source_directory, build_directory):
    """
    Copy a directory tree suitable for packaging with ``dpkg-deb --build`` to a
    temporary build directory so that individual files can be replaced without
    changing the original directory tree. If the build directory is on the same
    file system as the source directory, hard links are used to speed up the
    copy. This function is used by :py:func:`build_package()`.

    :param source_directory: The pathname of a directory tree suitable for
                             packaging with ``dpkg-deb --build``.
    :param build_directory: The pathname of a temporary build directory
                            (expected to already exist).
    """
    command = ['cp', '-a']
    if same_filesystem(source_directory, build_directory):
        # If the directories reside on the same file system we'll use hard
        # links to speed up the copy (this matters for large packages).
        logger.debug("Speeding up copying using hard links ..")
        command.append('-l')
    # I know this looks really funky, but I'm 99% sure this is a valid
    # use of shell escaping and globbing (obviously I tested it ;-).
    command.append('%s/*' % pipes.quote(source_directory))
    command.append(pipes.quote(build_directory))
    logger.info("Copying package files (%s) to build directory (%s) ..",
                format_path(source_directory), format_path(build_directory))
    execute(' '.join(command))

def clean_package_tree(directory):
    """
    Cleanup files that should not be included in a Debian package from the
    given directory.

    :param directory: The pathname of the directory to clean (a string).
    """
    for root, dirs, files in os.walk(directory):
        for name in dirs:
            if name in ('.bzr', '.git', '.hg', '.svn'):
                pathname = os.path.join(root, name)
                logger.debug("Cleaning up directory: %s", pathname)
                shutil.rmtree(pathname)
        for name in files:
            if name in ('.gitignore', '.hgignore', '.hg_archival.txt'):
                pathname = os.path.join(root, name)
                logger.debug("Cleaning up file: %s", pathname)
                os.unlink(pathname)

def update_installed_size(directory):
    """
    Given a directory tree suitable for packaging with ``dpkg-deb --build``
    this function updates the Installed-Size_ field in the ``DEBIAN/control``
    file. This function is used by :py:func:`build_package()`.

    :param directory: The pathname of a directory tree suitable for packaging
                      with ``dpkg-deb --build``.
    :returns: The parsed control file fields (an instance
              of :py:func:`debian.deb822.Deb822`).

    .. _Installed-Size: http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Installed-Size
    """
    control_file = os.path.join(directory, 'DEBIAN', 'control')
    logger.debug("Reading control file: %s", format_path(control_file))
    with open(control_file) as handle:
        control_fields = Deb822(handle)
    # Prepare to overwrite the control file by making
    # sure we dereference the hard link (see copy_package_files).
    os.unlink(control_file)
    # Find the installed size of the package (a rough estimate is fine).
    logger.debug("Finding installed size of package ..")
    output = execute('du', '-sB', '1024', directory, capture=True)
    installed_size = output.split()[0]
    # Update the Installed-Size field in the DEBIAN/control file.
    control_fields['Installed-Size'] = installed_size
    logger.debug("Writing control file: %s", format_path(control_file))
    with open(control_file, 'w') as handle:
        control_fields.dump(handle)
    return control_fields

# vim: ts=4 sw=4 et
