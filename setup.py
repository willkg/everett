#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


from setuptools import setup


def get_file(fn):
    with open(fn) as fp:
        return fp.read()


# FIXME: This requires the requirements in requirements.txt, but we need to
# pull that in without the hashes.

setup(
    name='everett',
    version='0.1.0',
    description='Lite configuration management for a component architecture',
    long_description=get_file('README.rst'),
    author="Will Kahn-Greene",
    author_email='willkg@mozilla.com',
    url='https://github.com/willkg/everett',
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
    ],
)
