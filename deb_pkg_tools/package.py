# Debian packaging tools: Package manipulation.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 1, 2015
# URL: https://github.com/xolox/python-deb-pkg-tools

"""
Package manipulation
====================

This module provides functions to build and inspect Debian package archives
(``*.deb`` files).
"""

# Standard library modules.
import collections
import copy
import fnmatch
import logging
import os
import os.path
import pipes
import random
import re
import shutil
import tempfile

# External dependencies.
from debian.deb822 import Deb822
from executor import execute
from humanfriendly import coerce_boolean, concatenate, format_path, pluralize, Spinner, Timer

# Modules included in our package.
from deb_pkg_tools.control import (deb822_from_string,
                                   parse_control_fields,
                                   patch_control_file)
from deb_pkg_tools.version import Version

# Initialize a logger.
logger = logging.getLogger(__name__)

# The names of control file fields that specify dependencies.
DEPENDENCY_FIELDS = ('Depends', 'Pre-Depends')

# http://lintian.debian.org/tags/package-contains-vcs-control-dir.html
DIRECTORIES_TO_REMOVE = ('.bzr', # Bazaar
                         '.git', # Git
                         '.hg',  # Mercurial
                         '.svn', # SVN
                         '__pycache__') # Python 3.x byte code files (http://lintian.debian.org/tags/package-installs-python-pycache-dir.html)

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

# Enable power users to customize how packages are built in order to enable
# limited use of deb-pkg-tools in non-Debian environments like Mac OS X.
ALLOW_CHOWN = coerce_boolean(os.environ.get('DPT_CHOWN_FILES', 'true'))
ALLOW_FAKEROOT_OR_SUDO = coerce_boolean(os.environ.get('DPT_ALLOW_FAKEROOT_OR_SUDO', 'true'))
ALLOW_HARD_LINKS = coerce_boolean(os.environ.get('DPT_HARD_LINKS', 'true'))
ALLOW_RESET_SETGID = coerce_boolean(os.environ.get('DPT_RESET_SETGID', 'true'))

def parse_filename(filename):
    """
    Parse the filename of a Debian binary package archive into three fields:
    the name of the package, its version and its architecture. See also
    :py:func:`determine_package_archive()`.

    :param filename: The pathname of a ``*.deb`` archive (a string).
    :returns: A :py:class:`PackageFile` object.
    :raises: Raises :py:exc:`~exceptions.ValueError` when the given filename
             cannot be parsed.

    Here's an example:

    >>> from deb_pkg_tools.package import parse_filename
    >>> components = parse_filename('/var/cache/apt/archives/python2.7_2.7.3-0ubuntu3.4_amd64.deb')
    >>> print(repr(components))
    PackageFile(name='python2.7',
                version='2.7.3-0ubuntu3.4',
                architecture='amd64',
                filename='/var/cache/apt/archives/python2.7_2.7.3-0ubuntu3.4_amd64.deb')

    """
    if isinstance(filename, PackageFile):
        return filename
    pathname = os.path.abspath(filename)
    filename = os.path.basename(pathname)
    basename, extension = os.path.splitext(filename)
    if extension != '.deb':
        raise ValueError("Refusing to parse filename that doesn't have `.deb' extension! (%r)" % pathname)
    components = basename.split('_')
    if len(components) != 3:
        raise ValueError("Filename doesn't have three underscore separated components! (%r)" % pathname)
    return PackageFile(name=components[0],
                       version=Version(components[1]),
                       architecture=components[2],
                       filename=pathname)

class PackageFile(collections.namedtuple('PackageFile', 'name, version, architecture, filename')):

    """
    The function :py:func:`parse_filename()` reports the fields of a package
    archive's filename as a :py:class:`PackageFile` object (a named tuple).
    Here are the fields supported by these named tuples:

    .. py:attribute:: name

       The name of the package (a string).

    .. py:attribute:: version

       The version of the package (a :py:class:`.Version` object).

    .. py:attribute:: architecture

       The architecture of the package (a string).

    .. py:attribute:: filename

       The absolute pathname of the package archive (a string).

    The following fields are generated on demand:

    .. py:attribute:: directory

       The absolute pathname of the directory containing the package archive (a
       string).

    .. py:attribute:: other_versions

       A list of :py:class:`PackageFile` objects with other versions of the
       same package in the same directory.

    .. py:attribute: newer_versions

       A list of :py:class:`PackageFile` objects with newer versions of the
       same package in the same directory.

    :py:class:`PackageFile` objects support sorting according to Debian's
    package version comparison algorithm as implemented in ``dpkg
    --compare-versions``.
    """

    @property
    def directory(self):
        return os.path.dirname(self.filename)

    @property
    def other_versions(self):
        archives = []
        for other_archive in find_package_archives(self.directory):
            if self.name == other_archive.name and self.version != other_archive.version:
                archives.append(other_archive)
        return archives

    @property
    def newer_versions(self):
        archives = []
        for other_archive in self.other_versions:
            if other_archive.version > self.version:
                archives.append(other_archive)
        return archives

def find_package_archives(directory):
    """
    Find the Debian package archive(s) in the given directory.

    :param directory: The pathname of a directory (a string).
    :returns: A list of :py:class:`PackageFile` objects.
    """
    archives = []
    for entry in os.listdir(directory):
        if entry.endswith('.deb'):
            pathname = os.path.join(directory, entry)
            if os.path.isfile(pathname):
                archives.append(parse_filename(pathname))
    return archives

def collect_related_packages(filename, cache=None):
    """
    Collect the package archive(s) related to the given package archive. This
    works by parsing and resolving the dependencies of the given package to
    filenames of package archives, then parsing and resolving the dependencies
    of those package archives, etc. until no more relationships can be resolved
    to existing package archives.

    :param filename: The filename of an existing ``*.deb`` archive (a string).
    :param cache: The :py:class:`.PackageCache` to use (defaults to ``None``).
    :returns: A list of :py:class:`PackageFile` objects.

    Known limitations / sharp edges of this function:

    - Only `Depends` and `Pre-Depends` relationships are processed, `Provides`
      is ignored. I'm not yet sure whether it makes sense to add support for
      `Conflicts`, `Provides` and `Replaces` (and how to implement it).

    - Unsatisfied relationships don't trigger a warning or error because this
      function doesn't know in what context a package can be installed (e.g.
      which additional repositories a given apt client has access to).

    - Please thoroughly test this functionality before you start to rely on it.
      What this function tries to do is a complex operation to do correctly
      (given the limited information this function has to work with) and the
      implementation is far from perfect. Bugs have been found and fixed in
      this code and more bugs will undoubtedly be discovered. You've been
      warned :-).

    - This function can be rather slow on large package repositories and
      dependency sets due to the incremental nature of the related package
      collection. It's a known issue / limitation.

    This function is used to implement the ``deb-pkg-tools --collect`` command:

    .. code-block:: sh

       $ deb-pkg-tools -c /tmp python-deb-pkg-tools_1.13-1_all.deb
       2014-05-18 08:33:42 deb_pkg_tools.package INFO Collecting packages related to ~/python-deb-pkg-tools_1.13-1_all.deb ..
       2014-05-18 08:33:42 deb_pkg_tools.package INFO Scanning ~/python-deb-pkg-tools_1.13-1_all.deb ..
       2014-05-18 08:33:42 deb_pkg_tools.package INFO Scanning ~/python-coloredlogs_0.4.8-1_all.deb ..
       2014-05-18 08:33:42 deb_pkg_tools.package INFO Scanning ~/python-chardet_2.2.1-1_all.deb ..
       2014-05-18 08:33:42 deb_pkg_tools.package INFO Scanning ~/python-humanfriendly_1.7.1-1_all.deb ..
       2014-05-18 08:33:42 deb_pkg_tools.package INFO Scanning ~/python-debian_0.1.21-1_all.deb ..
       Found 5 package archives:
        - ~/python-chardet_2.2.1-1_all.deb
        - ~/python-coloredlogs_0.4.8-1_all.deb
        - ~/python-deb-pkg-tools_1.13-1_all.deb
        - ~/python-humanfriendly_1.7.1-1_all.deb
        - ~/python-debian_0.1.21-1_all.deb
       Copy 5 package archives to /tmp? [Y/n] y
       2014-05-18 08:33:44 deb_pkg_tools.cli INFO Done! Copied 5 package archives to /tmp.
    """
    given_archive = parse_filename(filename)
    logger.info("Collecting packages related to %s ..", format_path(given_archive.filename))
    # Group the related package archive candidates by name.
    candidate_archives = collections.defaultdict(list)
    for archive in find_package_archives(given_archive.directory):
        if archive.name != given_archive.name:
            candidate_archives[archive.name].append(archive)
    # Sort the related package archive candidates by descending versions
    # because we want to prefer newer versions over older versions.
    for name in candidate_archives:
        candidate_archives[name].sort(reverse=True)
    # Prepare for more than one attempt to find a converging set of related
    # package archives so we can properly deal with conflicts between
    # transitive (indirect) dependencies.
    while True:
        try:
            # Assuming there are no possible conflicts one call will be enough.
            return collect_related_packages_helper(candidate_archives, given_archive, cache)
        except CollectedPackagesConflict as e:
            # If we do encounter conflicts we take the brute force approach of
            # removing the conflicting package archive(s) from the set of
            # related package archive candidates and retrying from scratch.
            # This approach works acceptably as long as your repository isn't
            # full of conflicts between transitive dependencies...
            logger.warning("Removing %s from candidates (%s) ..",
                           pluralize(len(e.conflicts), "conflicting archive"),
                           concatenate(os.path.basename(archive.filename) for archive in e.conflicts))
            for archive in e.conflicts:
                candidate_archives[archive.name].remove(archive)
            logger.info("Retrying related archive collection without %s ..",
                        pluralize(len(e.conflicts), "conflicting archive"))

def collect_related_packages_helper(candidate_archives, given_archive, cache):
    """
    Internal helper that enables :py:func:`collect_related_packages()` to
    perform conflict resolution (which would otherwise get very complex).
    """
    # Enable mutation of the candidate archives data structure inside the scope
    # of this function without mutating the original data structure.
    candidate_archives = copy.deepcopy(candidate_archives)
    # Prepare some internal state.
    archives_to_scan = [given_archive]
    collected_archives = []
    relationship_sets = set()
    # Loop to collect the related packages.
    spinner = Spinner(label="Collecting related packages", timer=Timer())
    while archives_to_scan:
        selected_archive = archives_to_scan.pop(0)
        logger.debug("Scanning %s ..", format_path(selected_archive.filename))
        # Find the relationships of the given package.
        control_fields = inspect_package_fields(selected_archive.filename, cache)
        for field_name in DEPENDENCY_FIELDS:
            if field_name in control_fields:
                relationship_sets.add(control_fields[field_name])
        # For each group of package archives sharing the same package name ..
        for package_name in sorted(candidate_archives):
            # For each version of the package ..
            for package_archive in list(candidate_archives[package_name]):
                package_matches = match_relationships(package_archive, relationship_sets)
                spinner.step()
                if package_matches == True:
                    logger.debug("Package archive matched all relationships: %s", package_archive.filename)
                    # Move the selected version of the package archive from the
                    # candidates to the list of selected package archives.
                    collected_archives.append(package_archive)
                    # Prepare to scan and collect dependencies of the selected
                    # package archive in a future iteration of the outermost
                    # (while) loop.
                    archives_to_scan.append(package_archive)
                    # Ignore all other versions of the package inside this call
                    # to collect_related_packages_helper().
                    candidate_archives.pop(package_name)
                    # Break out of the loop to avoid scanning other versions of
                    # this package archive; we've made our choice now.
                    break
                elif package_matches == False:
                    # If we're sure we can exclude this version of the package
                    # from future iterations it could be worth it to speed up
                    # the process on big repositories / dependency sets.
                    candidate_archives[package_name].remove(package_archive)
                    # Keep looking for a match in another version.
                elif package_matches == None:
                    # Break out of the loop that scans multiple versions of the
                    # same package because none of the relationship sets collected
                    # so far reference the name of this package (this is intended
                    # as a harmless optimization).
                    break
    spinner.clear()
    # Check for conflicts in the collected set of related package archives.
    conflicts = [a for a in collected_archives if not match_relationships(a, relationship_sets)]
    if conflicts:
        raise CollectedPackagesConflict(conflicts)
    else:
        return collected_archives

def match_relationships(package_archive, relationship_sets):
    """
    Internal helper that enables :py:func:`collect_related_packages_helper()`
    to validate that all relationships are satisfied while the set of related
    package archives is being collected and again afterwards to make sure that
    no previously drawn conclusions were invalidated by additionally collected
    package archives.
    """
    archive_matches = None
    for relationships in relationship_sets:
        status = relationships.matches(package_archive.name, package_archive.version)
        if status == True and archive_matches != False:
            archive_matches = True
        elif status == False:
            # This package archive specifically conflicts with (at least) one
            # of the given relationship sets.
            archive_matches = False
            # Short circuit the evaluation of further relationship sets because
            # we've already found our answer.
            break
    return archive_matches

class CollectedPackagesConflict(Exception):

    """Exception raised by :py:func:`collect_related_packages_helper()`."""

    def __init__(self, conflicts):
        """
        Construct a :py:exc:`CollectedPackagesConflict` exception.

        :param conflicts: A list of conflicting :py:class:`PackageFile` objects.
        """
        self.conflicts = conflicts

def find_latest_version(packages):
    """
    Find the package archive with the highest version number. Uses
    :py:class:`.Version` objects for version comparison. Raises
    :py:exc:`ValueError` when not all of the given package archives share the
    same package name.

    :param packages: A list of filenames (strings) and/or
                     :py:class:`PackageFile` objects.
    :returns: The :py:class:`PackageFile` with
              the highest version number.
    """
    packages = sorted(map(parse_filename, packages))
    names = set(p.name for p in packages)
    if len(names) > 1:
        msg = "Refusing to compare unrelated packages! (%s)"
        raise ValueError(msg % concatenate(sorted(names)))
    return packages[-1]

def group_by_latest_versions(packages):
    """
    Group package archives by name of package and find latest version of each.

    :param packages: A list of filenames (strings) and/or
                     :py:class:`PackageFile` objects.
    :returns: A dictionary with package names as keys and
              :py:class:`PackageFile` objects as values.
    """
    grouped_packages = collections.defaultdict(set)
    for value in packages:
        package = parse_filename(value)
        grouped_packages[package.name].add(package)
    return dict((n, find_latest_version(p)) for n, p in grouped_packages.items())

def inspect_package(archive, cache=None):
    """
    Get the metadata and contents from a ``*.deb`` archive.

    :param archive: The pathname of an existing ``*.deb`` archive.
    :param cache: The :py:class:`.PackageCache` to use (defaults to ``None``).
    :returns: A tuple with two dictionaries:

              1. The result of :py:func:`inspect_package_fields()`.
              2. The result of :py:func:`inspect_package_contents()`.
    """
    return (inspect_package_fields(archive, cache),
            inspect_package_contents(archive, cache))

def inspect_package_fields(archive, cache=None):
    r"""
    Get the fields (metadata) from a ``*.deb`` archive.

    :param archive: The pathname of an existing ``*.deb`` archive.
    :param cache: The :py:class:`.PackageCache` to use (defaults to ``None``).
    :returns: A dictionary with control file fields (the result of
              :py:func:`.parse_control_fields()`).

    Here's an example:

    >>> from deb_pkg_tools.package import inspect_package_fields
    >>> print(repr(inspect_package_fields('python3.4-minimal_3.4.0-1+precise1_amd64.deb')))
    {'Architecture': u'amd64',
     'Conflicts': RelationshipSet(VersionedRelationship(name=u'binfmt-support', operator=u'<<', version=u'1.1.2')),
     'Depends': RelationshipSet(VersionedRelationship(name=u'libpython3.4-minimal', operator=u'=', version=u'3.4.0-1+precise1'),
                                VersionedRelationship(name=u'libexpat1', operator=u'>=', version=u'1.95.8'),
                                VersionedRelationship(name=u'libgcc1', operator=u'>=', version=u'1:4.1.1'),
                                VersionedRelationship(name=u'zlib1g', operator=u'>=', version=u'1:1.2.0')),
     'Description': u'Minimal subset of the Python language (version 3.4)\n This package contains the interpreter and some essential modules.  It can\n be used in the boot process for some basic tasks.\n See /usr/share/doc/python3.4-minimal/README.Debian for a list of the modules\n contained in this package.',
     'Installed-Size': 3586,
     'Maintainer': u'Felix Krull <f_krull@gmx.de>',
     'Multi-Arch': u'allowed',
     'Original-Maintainer': u'Matthias Klose <doko@debian.org>',
     'Package': u'python3.4-minimal',
     'Pre-Depends': RelationshipSet(VersionedRelationship(name=u'libc6', operator=u'>=', version=u'2.15')),
     'Priority': u'optional',
     'Recommends': u'python3.4',
     'Section': u'python',
     'Source': u'python3.4',
     'Suggests': RelationshipSet(Relationship(name=u'binfmt-support')),
     'Version': u'3.4.0-1+precise1'}

    """
    if cache:
        return cache[archive].control_fields
    listing = execute('dpkg-deb', '-f', archive, logger=logger, capture=True)
    raw_control_fields = deb822_from_string(listing)
    return parse_control_fields(raw_control_fields)

def inspect_package_contents(archive, cache=None):
    """
    Get the contents from a ``*.deb`` archive.

    :param archive: The pathname of an existing ``*.deb`` archive.
    :param cache: The :py:class:`.PackageCache` to use (defaults to ``None``).
    :returns: A dictionary with the directories and files contained in the
              package. The dictionary keys are the absolute pathnames and the
              dictionary values are :py:class:`ArchiveEntry` objects (see the
              example below).

    An example:

    >>> from deb_pkg_tools.package import inspect_package_contents
    >>> print(repr(inspect_package_contents('python3.4-minimal_3.4.0-1+precise1_amd64.deb')))
    {u'/': ArchiveEntry(permissions=u'drwxr-xr-x', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:54', target=u''),
     u'/usr/': ArchiveEntry(permissions=u'drwxr-xr-x', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:52', target=u''),
     u'/usr/bin/': ArchiveEntry(permissions=u'drwxr-xr-x', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:54', target=u''),
     u'/usr/bin/python3.4': ArchiveEntry(permissions=u'-rwxr-xr-x', owner=u'root', group=u'root', size=3536680, modified=u'2014-03-20 23:54', target=u''),
     u'/usr/bin/python3.4m': ArchiveEntry(permissions=u'hrwxr-xr-x', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:54', target=u'/usr/bin/python3.4'),
     u'/usr/share/': ArchiveEntry(permissions=u'drwxr-xr-x', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:53', target=u''),
     u'/usr/share/binfmts/': ArchiveEntry(permissions=u'drwxr-xr-x', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:53', target=u''),
     u'/usr/share/binfmts/python3.4': ArchiveEntry(permissions=u'-rw-r--r--', owner=u'root', group=u'root', size=72, modified=u'2014-03-20 23:53', target=u''),
     u'/usr/share/doc/': ArchiveEntry(permissions=u'drwxr-xr-x', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:53', target=u''),
     u'/usr/share/doc/python3.4-minimal/': ArchiveEntry(permissions=u'drwxr-xr-x', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:54', target=u''),
     u'/usr/share/doc/python3.4-minimal/README.Debian': ArchiveEntry(permissions=u'-rw-r--r--', owner=u'root', group=u'root', size=3779, modified=u'2014-03-20 23:52', target=u''),
     u'/usr/share/doc/python3.4-minimal/changelog.Debian.gz': ArchiveEntry(permissions=u'-rw-r--r--', owner=u'root', group=u'root', size=28528, modified=u'2014-03-20 22:32', target=u''),
     u'/usr/share/doc/python3.4-minimal/copyright': ArchiveEntry(permissions=u'-rw-r--r--', owner=u'root', group=u'root', size=51835, modified=u'2014-03-20 20:37', target=u''),
     u'/usr/share/man/': ArchiveEntry(permissions=u'drwxr-xr-x', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:52', target=u''),
     u'/usr/share/man/man1/': ArchiveEntry(permissions=u'drwxr-xr-x', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:54', target=u''),
     u'/usr/share/man/man1/python3.4.1.gz': ArchiveEntry(permissions=u'-rw-r--r--', owner=u'root', group=u'root', size=5340, modified=u'2014-03-20 23:30', target=u''),
     u'/usr/share/man/man1/python3.4m.1.gz': ArchiveEntry(permissions=u'lrwxrwxrwx', owner=u'root', group=u'root', size=0, modified=u'2014-03-20 23:54', target=u'python3.4.1.gz')}

    """
    if cache:
        return cache[archive].contents
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
        if not target:
            pathname, _, target = pathname.partition(' link to ')
            target = re.sub('^./', '/', target)
        contents[pathname] = ArchiveEntry(permissions, owner, group, size, modified, target)
    return contents

class ArchiveEntry(collections.namedtuple('ArchiveEntry', 'permissions, owner, group, size, modified, target')):
    """
    The function :py:func:`inspect_package()` reports the contents of package
    archives as a dictionary containing named tuples. Here are the fields
    supported by those named tuples:

    .. py:attribute:: permissions

       The entry type and permission bits just like ``ls -l`` prints them (a string like `drwxr-xr-x`).

    .. py:attribute:: owner

       The username of the owner of the entry (a string).

    .. py:attribute:: group

       The group name of group owning the entry (a string).

    .. py:attribute:: size

       The size of the entry in bytes (an integer).

    .. py:attribute:: modified

       A string like ``2013-09-26 22:28``.
    """

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
    :py:exc:`executor.ExternalCommandFailed` is raised. If this function
    returns without raising an exception, the generated Debian package can be
    found in the parent directory of the directory given as the first
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
    if not repository:
        repository = tempfile.gettempdir()
    package_file = os.path.join(repository, determine_package_archive(directory))
    logger.debug("Preparing to build package: %s", format_path(package_file))
    try:
        if copy_files:
            build_directory = tempfile.mkdtemp()
            logger.debug("Created build directory: %s", format_path(build_directory))
            # This no longer uses hard links because of all the file permission
            # magic going on further down in this function (permissions are
            # shared between all hard links pointing to an inode).
            copy_package_files(directory, build_directory, hard_links=False)
        else:
            build_directory = directory
        clean_package_tree(build_directory)
        update_conffiles(build_directory)
        update_installed_size(build_directory)
        # Sanitize the permission bits of the root directory. Most build
        # directories will have been created with tempfile.mkdtemp() which
        # creates the directory with mode 0700. The Debian packaging system
        # really doesn't care about any of this, but:
        #
        #  1. It looks weird in the output of ``deb-pkg-tools -i`` :-)
        #  2. When you convert a ``*.deb`` to ``*.rpm`` with Alien and install
        #     the RPM the 0700 mode is actually applied to the system where you
        #     install the package. As you can imagine, the results are
        #     disastrous...
        os.chmod(build_directory, 0o755)
        if ALLOW_CHOWN:
            # Make sure all files included in the package are owned by `root'
            # (the only account guaranteed to exist on all systems).
            root_user = os.environ.get('DPT_ROOT_USER', 'root')
            root_group = os.environ.get('DPT_ROOT_GROUP', 'root')
            user_spec = '%s:%s' % (root_user, root_group)
            logger.debug("Resetting file ownership (to %s) ..", user_spec)
            execute('chown', '-R', user_spec, build_directory,
                    fakeroot=ALLOW_FAKEROOT_OR_SUDO, logger=logger)
        # Reset the file modes of pre/post installation/removal scripts.
        for script_name in ('preinst', 'postinst', 'prerm', 'postrm'):
            script_path = os.path.join(build_directory, 'DEBIAN', script_name)
            if os.path.isfile(script_path):
                logger.debug("Resetting file modes (%s to 755) ..", script_path)
                os.chmod(script_path, 0o755)
        # System packages generally install files that are read only and
        # readable (and possibly executable) for everyone (owner, group and
        # world) so we'll go ahead and remove some potentially harmful
        # permission bits (harmful enough that Lintian complains about them).
        logger.debug("Resetting file modes (go-w) ..")
        execute('chmod', '-R', 'go-w', build_directory,
                fakeroot=ALLOW_FAKEROOT_OR_SUDO, logger=logger)
        # Remove the setgid bit from all directories in the package. Rationale:
        # In my situation package templates are stored in a directory where a
        # team of people have push access (I imagine that this is a common
        # setup). To facilitate shared push access a shared primary UNIX group
        # is used with the sticky bit on directories. However dpkg-deb *really*
        # doesn't like this, failing with the error "dpkg-deb: control
        # directory has bad permissions 2755 (must be >=0755 and <=0775)".
        if ALLOW_RESET_SETGID:
            logger.debug("Removing sticky bit from directories (g-s) ..")
            execute('find -type d -print0 | xargs -0 chmod g-s',
                    directory=build_directory,
                    fakeroot=ALLOW_FAKEROOT_OR_SUDO, logger=logger)
        # Make sure files in /etc/sudoers.d have the correct permissions.
        sudoers_directory = os.path.join(build_directory, 'etc', 'sudoers.d')
        if os.path.isdir(sudoers_directory):
            for filename in os.listdir(sudoers_directory):
                pathname = os.path.join(sudoers_directory, filename)
                logger.debug("Resetting file modes (%s to 440) ..", pathname)
                os.chmod(pathname, 0o440)
        # Build the package using `dpkg-deb'.
        logger.info("Building package in %s ..", format_path(build_directory))
        execute('dpkg-deb', '--build', build_directory, package_file,
                fakeroot=ALLOW_FAKEROOT_OR_SUDO, logger=logger)
        # Check the package for possible issues using Lintian?
        if check_package:
            if not os.access('/usr/bin/lintian', os.X_OK):
                logger.warning("Lintian is not installed, skipping sanity check.")
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
        if copy_files:
            logger.debug("Removing build directory: %s", format_path(build_directory))
            shutil.rmtree(build_directory)

def determine_package_archive(directory):
    """
    Determine the name of the ``*.deb`` package archive that will be generated
    from a directory tree suitable for packaging with ``dpkg-deb --build``. See
    also :py:func:`parse_filename()`.

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

def copy_package_files(from_directory, to_directory, hard_links=True):
    """
    Copy a directory tree suitable for packaging with ``dpkg-deb --build`` to a
    temporary build directory so that individual files can be replaced without
    changing the original directory tree. If the build directory is on the same
    file system as the source directory, hard links are used to speed up the
    copy. This function is used by :py:func:`build_package()`.

    :param from_directory: The pathname of a directory tree suitable for
                           packaging with ``dpkg-deb --build``.
    :param to_directory: The pathname of a temporary build directory.
    :param hard_links: Use hard links to speed up copying when possible.
    """
    logger.info("Copying files (%s) to temporary directory (%s) ..",
                format_path(from_directory), format_path(to_directory))
    command = ['cp', '-a']
    if not os.path.isdir(to_directory):
        os.makedirs(to_directory)
    if hard_links and ALLOW_HARD_LINKS:
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
        except (IOError, OSError):
            pass
        finally:
            for test_file in [test_file_from, test_file_to]:
                if test_file and os.path.isfile(test_file):
                    os.unlink(test_file)
    # I know this looks really funky, but this is a valid use of shell escaping
    # and globbing (obviously I tested it ;-).
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
                    logger.warning("Stripping invalid entry: %s", filename)
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
    output = execute('du', '-sk', directory, logger=logger, capture=True)
    installed_size = output.split()[0]
    # Patch the DEBIAN/control file.
    control_file = os.path.join(directory, 'DEBIAN', 'control')
    patch_control_file(control_file, {'Installed-Size': installed_size})

# vim: ts=4 sw=4 et
