"""
Workaround to enable python-apt on Travis CI.

Make python-apt available in the Python virtual environment without using the
system site-packages support built into Travis CI because this doesn't work
for Python 3.4, 3.7 and PyPy. See the following failed build:
https://travis-ci.org/xolox/python-deb-pkg-tools/builds/581437417
"""

import os
import sys
import subprocess

from distutils.sysconfig import get_python_lib

src = subprocess.check_output(
    ["/usr/bin/python%i" % sys.version_info[0], "-c", "import apt_pkg; print(apt_pkg.__file__)"]
).decode('ascii').strip()
print("System wide module: %s" % src)
assert os.path.isfile(src)

dst = os.path.join(get_python_lib(), os.path.basename(src))
print("Link in virtual environment: %s" % dst)
os.symlink(src, dst)
