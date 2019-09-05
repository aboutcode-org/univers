"""
Make python-apt available in the Python virtual environment without using the
system site-packages support built into Travis CI because this doesn't work
for Python 3.4, 3.7 and PyPy. See the following failed build:
https://travis-ci.org/xolox/python-deb-pkg-tools/builds/581437417
"""

import os
import sys

from distutils.sysconfig import get_python_lib

src = "/usr/lib/python%s/dist-packages/apt" % ("2.7" if sys.version_info[0] == 2 else "3")
dst = os.path.join(get_python_lib(), "apt")
assert os.path.isdir(src)
os.symlink(src, dst)
