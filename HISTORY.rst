History
=======

0.2 (August 16th, 2016)
-----------------------

Feature: Add ``ConfigEnvFileEnv`` for supporting ``.env`` files. Thank you,
Paul!

Feature: Change ``ConfigIniEnv`` to take a single path or list of paths. Thank
you, Paul!

Feature: Add "on" and "off" as valid boolean values. This makes it easier to use
config for feature flippers. Thank you, Paul!

Feature: Make ``NO_VALUE`` falsy.

Bug: Fix ``__call__`` returning None--it should return ``NO_VALUE``.

Lots of docs updates: finished the section about making your own parsers, added
a section on using dj-database-url, added a section on django-cache-url and
expanded on existing examples.


0.1 (August 1st, 2016)
----------------------

Initial writing.
