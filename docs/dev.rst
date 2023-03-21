==================
Developing Everett
==================

Install for development
=======================

Clone the repository::

    $ git clone https://github.com/willkg/everett

Create and activate a virtualenvironment::

    $ mkvirtualenv everett

    OR

    $ python -m venv venv
    $ . ./venv/bin/activate

Install Everett and dev requirements into virtual environment::

    $ pip install -r requirements-dev.txt


Release process
===============

1. Checkout main tip.

2. Check to make sure ``setup.py`` and requirements files
   have correct versions of requirements.

   Check dev dependencies using ``make checkrot``.

3. Update version numbers in ``src/everett/__init__.py``.

   1. Set ``__version__`` to something like ``1.0.0`` (use semver).
   2. Set ``__releasedate__`` to something like ``20190107``.

4. Update ``HISTORY.rst``

   1. Set the date for the release.
   2. Make sure to note any backwards incompatible changes.

5. Verify correctness.

   1. Check the manifest: ``check-manifest``
   2. Run tests and linting: ``make test``
   3. Build docs and verify example code: ``make docs``

6. Land any changes.

7. Tag the release::

       $ git tag --sign v1.0.0

   Copy the details from ``HISTORY.rst`` into the tag comment.

8. Update PyPI::

       $ rm -rf dist/*
       $ python -m build
       $ twine upload -r REPO dist/*

   Make sure ``REPO`` matches a section in your ``~/.pypyrc`` file.

9. Push everything::

       $ git push --tags origin main

10. Announce the release.
