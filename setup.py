#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from glob import glob
from os.path import basename
from os.path import splitext

from setuptools import find_packages
from setuptools import setup

# FIXME
requirements = [
    r.strip() for r in open("requirements.txt") if r.strip() and not r.strip().startswith("#")
]


setup(
    name="univers",
    install_requires=requirements,
    packages=find_packages("src"),
    package_dir={"": "src"},
    py_modules=[splitext(basename(path))[0] for path in glob("src/*.py")],
)
