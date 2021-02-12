#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from __future__ import absolute_import
from __future__ import print_function

from glob import glob
import io
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext
import re
import sys

from setuptools import find_packages
from setuptools import setup


def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()


setup(
    name='debut',
    version='0.9.9',
    license='Apache-2.0 AND BSD-3-Clause AND MIT',
    description='Utilities to parse Debian package, copyright and control files.',
    long_description=read('README.rst'),
    author='nexB. Inc. and others',
    author_email='info@aboutcode.org',
    url='https://github.com/nexB/debut',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(path))[0] for path in glob('src/*.py')],
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        # complete classifier list: http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    keywords=[
        'debian', 'deb822', 'copyright', 'package', 'dependency', 'license',
        'licensing', 'dep5', 'control', 'dsc', 'python-debian', 'dpkg', 'libapt',
    ],
    install_requires=[
        'chardet >= 3.0.0',
        'attrs >=19.2',
    ]
)
