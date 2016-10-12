History
=======

0.3.1 (October 12th, 2016)
--------------------------

Bug: Fix ``alternate_keys`` with components. Previously it worked for everything
but components. Now it works with components, too.


0.3 (October 6th, 2016)
-----------------------

Feature: Add ``ConfigManager.from_dict()`` shorthand for building configuration
instances.

Feature: Add ``.get_namespace()`` to ``ConfigManager`` and friends for getting
the complete namespace for a given config instance as a list of strings.

Feature: Make ``ConfigDictEnv`` case-insensitive to keys and namespaces.

Feature: Add ``alternate_keys`` to config call. This lets you specify a list
of keys in order to try if the primary key doesn't find a value. This is
helpful for deprecating keys that you used to use in a backwards-compatible
way.

Feature: Add ``root:`` prefix to keys allowing you to look outside of the
current namespace and at the configuration root for configuration values.


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
