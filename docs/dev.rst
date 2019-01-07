=======
Hacking
=======

Release process
===============

1. Checkout master tip.

2. Check to make sure ``setup.py`` and requirements files
   have correct versions of requirements.

3. Update version numbers in ``everett/__init__.py``.

   1. Set ``__version__`` to something like ``1.0.0`` (use semver).
   2. Set ``__releasedate__`` to something like ``20190107``.

4. Update ``HISTORY.rst``

   1. Set the date for the release.
   2. Make sure to note any backwards incompatible changes.

5. Verify correctness.

   1. Run tests.
   2. Build docs (this runs example code).
   3. Verify all that works.

6. Tag the release::

       $ git tag -a v1.0.0

   Copy the details from ``HISTORY.rst`` into the tag comment.

7. Update PyPI::

       $ rm -rf dist/*
       $ python setup.py sdist bdist_wheel
       $ twine upload dist/*

8. Push everything::

       $ git push --tags official master

9. Announce the release.
