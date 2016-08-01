#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import os
import re
from setuptools import setup


def get_version():
    fn = os.path.join('everett', '__init__.py')
    vsre = r"""^__version__ = ['"]([^'"]*)['"]"""
    version_file = open(fn, 'rt').read()
    return re.search(vsre, version_file, re.M).group(1)


def get_file(fn):
    with open(fn) as fp:
        return fp.read()


# FIXME: This requires the requirements in requirements.txt, but we need to
# pull that in without the hashes.

setup(
    name='everett',
    version=get_version(),
    description='Configuration library for Python applications',
    long_description=(
        get_file('README.rst') + '\n\n' + get_file('HISTORY.rst')
    ),
    author="Will Kahn-Greene",
    author_email='willkg@mozilla.com',
    url='https://github.com/willkg/everett',
    install_requires=[
        'six'
    ],
    packages=[
        'everett',
    ],
    package_dir={
        'everett': 'everett'
    },
    include_package_data=True,
    license="MPLv2",
    zip_safe=False,
    keywords='conf config configuration component',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
        "Programming Language :: Python :: 3",
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
)
