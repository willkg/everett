History
=======

0.8 (January 24th, 2016)
------------------------

Feature: Add ``:namespace:`` and ``:case:`` arguments to autoconfig
directive. These make it easier to cater your documentation to your
project's needs.

Feature: Add support for Python 3.6.

Minor documentation fixes and updates.


0.7 (January 5th, 2016)
-----------------------

Feature: You can now include documentation hints and urls for
``ConfigManager`` objects and config options. This will make it easier
for your users to debug configuration errors they're having with your
software.

Bug: Fix ``ListOf`` so it returns empty lists rather than a list with
a single empty string.

Documentation fixes and updates.


0.6 (November 28th, 2016)
-------------------------

Feature: Change ``:show-docstring:`` to take an optional value which is the
attribute to pull docstring content from. This means you don't have to mix
programming documentation with user documentation--they can be in different
attributes.

Feature: Add ``RequiredConfigMixin.get_runtime_config()`` which returns the
runtime configuration for a component or tree of components. This lets you print
runtime configuration at startup, generate INI files, etc.

Feature: Add ``ConfigObjEnv`` which lets you use an object for configuration.
This works with argparse's Namespace amongst other things.

Feature: Improve configuration-related exceptions. With Python 3, configuration
errors all derive from ``ConfigurationError`` and have helpful error messages
that should make it clear what's wrong with the configuration value. With Python
2, you can get other kinds of Exceptions thrown depending on the parser used,
but configuration error messages should still be helpful.

Documentation fixes and updates.


0.5 (November 8th, 2016)
------------------------

Feature: Add ``:show-docstring:`` flag to ``autoconfig`` directive.

Feature: Add ``:hide-classname:`` flag to ``autoconfig`` directive.

Feature: Rewrite ``ConfigIniEnv`` to use configobj which allows for nested
sections in INI files. This also allows you to specify multiple INI files
and have later ones override earlier ones.

Bug: Fix ``autoconfig`` Sphinx directive and add tests--it was all kinds of
broken.


0.4 (October 27th, 2016)
------------------------

Feature: Add ``raw_value`` argument to config calls. This makes it easier to
write code that prints configuration.

Bug: Fix ``listify(None)`` to return ``[]``.

Documentation fixes and updates.


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
