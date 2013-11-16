# Debian packaging tools: Package manipulation.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 16, 2013
# URL: https://github.com/xolox/python-deb-pkg-tools

"""
Package manipulation
====================

This module provides functions to build and inspect Debian package archives
(``*.deb`` files).
"""

# Standard library modules.
import collections
import fnmatch
import logging
import os.path
import pipes
import random
import re
import shutil
import StringIO
import tempfile

# External dependencies.
from debian.deb822 import Deb822
from humanfriendly import format_path, pluralize

# Modules included in our package.
from deb_pkg_tools.control import patch_control_file
from deb_pkg_tools.utils import execute

# Initialize a logger.
logger = logging.getLogger(__name__)

# http://lintian.debian.org/tags/package-contains-vcs-control-dir.html
DIRECTORIES_TO_REMOVE = ('.bzr', # Bazaar
                         '.git', # Git
                         '.hg',  # Mercurial
                         '.svn') # SVN

FILES_TO_REMOVE = ('*.pyc',            # Python byte code files (http://lintian.debian.org/tags/package-installs-python-bytecode.html)
                   '*.pyo',            # Python optimized byte code files (http://lintian.debian.org/tags/package-installs-python-bytecode.html)
                   '*~',               # Emacs/Vim backup files (http://lintian.debian.org/tags/backup-file-in-package.html)
                   '.*.s??',           # Vim named swap files
                   '.bzrignore',       # Bazaar ignore files (http://lintian.debian.org/tags/package-contains-vcs-control-file.html)
                   '.DS_Store',        # Mac OS X custom folder attributes (http://lintian.debian.org/tags/macos-ds-store-file-in-package.html)
                   '.DS_Store.gz',     # Mac OS X custom folder attributes (http://lintian.debian.org/tags/macos-ds-store-file-in-package.html)
                   '._*',              # Mac OS X resource fork (http://lintian.debian.org/tags/macos-resource-fork-file-in-package.html)
                   '.gitignore',       # Git ignore files (http://lintian.debian.org/tags/package-contains-vcs-control-file.html)
                   '.hg_archival.txt', # Artefact of `hg archive' (http://lintian.debian.org/tags/package-contains-vcs-control-file.html)
                   '.hgignore',        # Mercurial ignore files (http://lintian.debian.org/tags/package-contains-vcs-control-file.html)
                   '.hgtags',          # Mercurial ignore files (http://lintian.debian.org/tags/package-contains-vcs-control-file.html)
                   '.s??')             # Vim anonymous swap files

def inspect_package(archive):
    r"""
    Get the metadata and contents from a ``*.deb`` archive.

    :param archive: The pathname of an existing ``*.deb`` archive.
    :returns: A tuple with two dictionaries:

              1. A dictionary with control file fields (an instance of
                 :py:func:`debian.deb822.Deb822`).
              2. A dictionary with the directories and files contained in the
                 package. The dictionary keys are the absolute pathnames and
                 the dictionary values are named tuples with five fields:
                 permissions, owner, group, size, modified (see the example
                 below).

    To give you an idea of what the result looks like:

    >>> from deb_pkg_tools.package import inspect_package
    >>> fields, contents = inspect_package('/var/cache/apt/archives/python2.7_2.7.3-0ubuntu3.4_amd64.deb')
    >>> print fields
    {'Architecture': u'amd64',
     'Conflicts': u'python-profiler (<= 2.7.1-2)',
     'Depends': u'python2.7-minimal (= 2.7.3-0ubuntu3.4), mime-support, libbz2-1.0, libc6 (>= 2.15), libdb5.1, libexpat1 (>= 1.95.8), libgcc1 (>= 1:4.1.1), libncursesw5 (>= 5.6+20070908), libreadline6 (>= 6.0), libsqlite3-0 (>= 3.5.9), libtinfo5',
     'Description': u'Interactive high-level object-oriented language (version 2.7)\n Version 2.7 of the high-level, interactive object oriented language,\n includes an extensive class library with lots of goodies for\n network programming, system administration, sounds and graphics.',
     'Installed-Size': u'8779',
     'Maintainer': u'Ubuntu Core Developers <ubuntu-devel-discuss@lists.ubuntu.com>',
     'Multi-Arch': u'allowed',
     'Original-Maintainer': u'Matthias Klose <doko@debian.org>',
     'Package': u'python2.7',
     'Priority': u'optional',
     'Provides': u'python-argparse, python2.7-argparse, python2.7-celementtree, python2.7-cjkcodecs, python2.7-ctypes, python2.7-elementtree, python2.7-profiler, python2.7-wsgiref',
     'Replaces': u'python-profiler (<= 2.7.1-2)',
     'Section': u'python',
     'Suggests': u'python2.7-doc, binutils',
     'Version': u'2.7.3-0ubuntu3.4'}
    >>> print contents
    {'/usr/lib/python2.7/email/mime/': ArchiveEntry(permissions='drwxr-xr-x', owner='root', group='root', size=0, modified='2013-09-26 22:28'),
     '/usr/lib/python2.7/encodings/gbk.py': ArchiveEntry(permissions='-rw-r--r--', owner='root', group='root', size=1015, modified='2013-09-26 22:28'),
     '/usr/lib/python2.7/multiprocessing/managers.py': ArchiveEntry(permissions='-rw-r--r--', owner='root', group='root', size=36586, modified='2013-09-26 22:28'),
     '/usr/lib/python2.7/sqlite3/dbapi2.py': ArchiveEntry(permissions='-rw-r--r--', owner='root', group='root', size=2615, modified='2013-09-26 22:28'),
     '/usr/lib/python2.7/uuid.py': ArchiveEntry(permissions='-rw-r--r--', owner='root', group='root', size=21095, modified='2013-09-26 22:28'),
     ...}
    """
    metadata = Deb822(StringIO.StringIO(execute('dpkg-deb', '-f', archive, logger=logger, capture=True)))
    contents = {}
    for line in execute('dpkg-deb', '-c', archive, logger=logger, capture=True).splitlines():
        # Example output of dpkg-deb -c archive.deb:
        # drwxr-xr-x root/root 0 2013-07-08 17:49 ./usr/share/doc/
        # lrwxrwxrwx root/root 0 2013-09-26 22:29 ./usr/bin/pdb2.7 -> ../lib/python2.7/pdb.py
        fields = line.split(None, 5)
        permissions = fields[0]
        owner, group = fields[1].split('/')
        size = int(fields[2])
        modified = fields[3] + ' ' + fields[4]
        pathname = re.sub('^./', '/', fields[5])
        pathname, _, target = pathname.partition(' -> ')
        contents[pathname] = ArchiveEntry(permissions, owner, group, size, modified, target)
    return metadata, contents

ArchiveEntry = collections.namedtuple('ArchiveEntry', 'permissions, owner, group, size, modified, target')

def build_package(directory, repository=None, check_package=True, copy_files=True):
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
    :param copy_files: If ``True`` (the default) the package's files are copied
                       to a temporary directory before being modified. You can
                       set this to ``False`` if you're already working on a
                       copy and don't want yet another copy to be made.
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
        update_conffiles(build_directory)
        update_installed_size(build_directory)
        # Make sure all files included in the package are owned by `root'
        # (the only account guaranteed to exist on all systems).
        logger.debug("Resetting file ownership (to root:root) ..")
        execute('fakeroot', 'chown', '-R', 'root:root', build_directory, logger=logger)
        # System packages generally install files that are read only and
        # readable (and possibly executable) for everyone (owner, group and
        # world) so we'll go ahead and remove some potentially harmful
        # permission bits (harmful enough that Lintian complains about them).
        logger.debug("Resetting file modes (go-w) ..")
        execute('fakeroot', 'chmod', '-R', 'go-w', build_directory, logger=logger)
        # Build the package using `dpkg-deb'.
        logger.info("Building package in %s ..", format_path(build_directory))
        execute('fakeroot', 'dpkg-deb', '--build', build_directory, package_file, logger=logger)
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
                execute(*lintian_command, logger=logger, check=False)
        return package_file
    finally:
        logger.debug("Removing build directory: %s", format_path(build_directory))
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

def copy_package_files(from_directory, to_directory):
    """
    Copy a directory tree suitable for packaging with ``dpkg-deb --build`` to a
    temporary build directory so that individual files can be replaced without
    changing the original directory tree. If the build directory is on the same
    file system as the source directory, hard links are used to speed up the
    copy. This function is used by :py:func:`build_package()`.

    :param from_directory: The pathname of a directory tree suitable for
                           packaging with ``dpkg-deb --build``.
    :param to_directory: The pathname of a temporary build directory.
    """
    logger.info("Copying files (%s) to temporary directory (%s) ..",
                format_path(from_directory), format_path(to_directory))
    command = ['cp', '-a']
    if not os.path.isdir(to_directory):
        os.makedirs(to_directory)
    # Check whether we can use hard links to speed up the copy. In the past
    # this used the following simple and obvious check:
    #
    #   os.stat(source_directory).st_dev == os.stat(build_directory).st_dev
    #
    # However this expression holds true inside schroot, yet `cp -al' fails
    # when trying to create the hard links! This is why the following code now
    # tries to create an actual hard link to verify that `cp -al' can be used.
    test_file_from = None
    test_file_to = None
    try:
        # Find a unique filename that we can create and destroy without
        # touching any of the caller's files.
        while True:
            test_name = 'deb-pkg-tools-hard-link-test-%d' % random.randint(1, 1000)
            test_file_from = os.path.join(from_directory, test_name)
            test_file_to = os.path.join(to_directory, test_name)
            if not os.path.isfile(test_file_from):
                break
        # Create the test file.
        with open(test_file_from, 'w') as handle:
            handle.write('test')
        os.link(test_file_from, test_file_to)
        logger.debug("Speeding up file copy using hard links ..")
        command.append('-l')
    except OSError:
        pass
    finally:
        for test_file in [test_file_from, test_file_to]:
            if test_file and os.path.isfile(test_file):
                os.unlink(test_file)
    # I know this looks really funky, but I'm 99% sure this is a valid
    # use of shell escaping and globbing (obviously I tested it ;-).
    command.append('%s/*' % pipes.quote(from_directory))
    command.append(pipes.quote(to_directory))
    execute(' '.join(command), logger=logger)

def clean_package_tree(directory, remove_dirs=DIRECTORIES_TO_REMOVE, remove_files=FILES_TO_REMOVE):
    """
    Clean up files that should not be included in a Debian package from the
    given directory. Uses the :py:mod:`fnmatch` module for directory and
    filename matching. Matching is done on the base name of each directory and
    file. This function assumes it is safe to unlink files from the given
    directory (which it should be when :py:func:`copy_package_files()` was
    previously called, e.g. by :py:func:`build_package()`).

    :param directory: The pathname of the directory to clean (a string).
    :param remove_dirs: An iterable with filename patterns of directories that
                        should not be included in the package (e.g. version
                        control directories like ``.git`` and ``.hg``).
    :param remove_files: An iterable with filename patterns of files that
                         should not be included in the package (e.g. version
                         control files like ``.gitignore`` and
                         ``.hgignore``).
    """
    for root, dirs, files in os.walk(directory):
        for name in dirs:
            if any(fnmatch.fnmatch(name, p) for p in remove_dirs):
                pathname = os.path.join(root, name)
                logger.debug("Cleaning up directory: %s", format_path(pathname))
                shutil.rmtree(pathname)
        for name in files:
            if any(fnmatch.fnmatch(name, p) for p in remove_files):
                pathname = os.path.join(root, name)
                logger.debug("Cleaning up file: %s", format_path(pathname))
                os.unlink(pathname)

def update_conffiles(directory):
    """
    Given a directory tree suitable for packaging with ``dpkg-deb --build``
    this function updates the entries in the ``DEBIAN/conffiles`` file. This
    function is used by :py:func:`build_package()`.

    :param directory: The pathname of a directory tree suitable for packaging
                      with ``dpkg-deb --build``.

    """
    conffiles = set()
    conffiles_file = os.path.join(directory, 'DEBIAN', 'conffiles')
    # Read the existing DEBIAN/conffiles entries (if any).
    if os.path.isfile(conffiles_file):
        logger.debug("Reading existing entries from %s ..", conffiles_file)
        with open(conffiles_file) as handle:
            for line in handle:
                filename = line.strip()
                pathname = os.path.join(directory, filename.lstrip('/'))
                # Validate existing entries.
                if os.path.isfile(pathname):
                    conffiles.add(filename)
                else:
                    logger.warn("Stripping invalid entry: %s", filename)
        os.unlink(conffiles_file)
    # Make sure all regular files in /etc/ are marked as configuration files.
    for root, dirs, files in os.walk(os.path.join(directory, 'etc')):
        for filename in files:
            pathname = os.path.join(root, filename)
            if os.path.isfile(pathname) and not os.path.islink(pathname):
                relpath = '/' + os.path.relpath(pathname, directory)
                if relpath not in conffiles:
                    logger.debug("Marking configuration file: %s", relpath)
                    conffiles.add(relpath)
    # Update DEBIAN/conffiles.
    if conffiles:
        with open(conffiles_file, 'w') as handle:
            for filename in sorted(conffiles):
                handle.write("%s\n" % filename)
        logger.debug("Wrote %s to %s!", pluralize(len(conffiles), "entry", "entries"), conffiles_file)

def update_installed_size(directory):
    """
    Given a directory tree suitable for packaging with ``dpkg-deb --build``
    this function updates the Installed-Size_ field in the ``DEBIAN/control``
    file. This function is used by :py:func:`build_package()`.

    :param directory: The pathname of a directory tree suitable for packaging
                      with ``dpkg-deb --build``.

    .. _Installed-Size: http://www.debian.org/doc/debian-policy/ch-controlfields.html#s-f-Installed-Size
    """
    # Find the installed size of the package (a rough estimate is fine).
    logger.debug("Finding installed size of package ..")
    output = execute('du', '-sB', '1024', directory, logger=logger, capture=True)
    installed_size = output.split()[0]
    # Patch the DEBIAN/control file.
    control_file = os.path.join(directory, 'DEBIAN', 'control')
    patch_control_file(control_file, {'Installed-Size': installed_size})

# vim: ts=4 sw=4 et
