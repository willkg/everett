#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


import os
import re
from setuptools import find_packages, setup


def get_version():
    fn = os.path.join("src", "everett", "__init__.py")
    vsre = r"""^__version__ = ['"]([^'"]*)['"]"""
    version_file = open(fn).read()
    return re.search(vsre, version_file, re.M).group(1)


def get_file(fn):
    with open(fn) as fp:
        return fp.read()


INSTALL_REQUIRES = []
EXTRAS_REQUIRE = {
    "ini": ["configobj"],
    "yaml": ["PyYAML"],
    "dev": [
        "black==20.8b1",
        "check-manifest==0.47",
        "cogapp==3.3.0",
        "flake8==4.0.1",
        "mypy==0.931",
        "pytest==6.2.5",
        "Sphinx==4.3.2",
        "sphinx_rtd_theme==1.0.0",
        "tox==3.24.5",
        "tox-gh-actions==2.9.1",
        "twine==3.7.1",
        "types-PyYAML==6.0.3",
    ],
}


setup(
    name="everett",
    version=get_version(),
    description="Configuration library for Python applications",
    long_description=(get_file("README.rst") + "\n\n" + get_file("HISTORY.rst")),
    author="Will Kahn-Greene",
    author_email="willkg@mozilla.com",
    url="https://github.com/willkg/everett",
    install_requires=INSTALL_REQUIRES,
    extras_require=EXTRAS_REQUIRE,
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    license="MPLv2",
    zip_safe=False,
    keywords="conf config configuration component",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    project_urls={
        "Documentation": "https://everett.readthedocs.io/",
        "Tracker": "https://github.com/willkg/everett/issues",
        "Source": "https://github.com/willkg/everett/",
    },
)
