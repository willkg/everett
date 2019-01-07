History
=======

1.0.0 (January 7th, 2019)
-------------------------

Backwards incompatible changes:

* Dropped support for Python 2.7. Everett no longer supports Python 2. (#73)

* Dropped support for Python 3.3 and added support for Python 3.7. Thank you,
  pjz! (#68)

* Moved ``ConfigIniEnv`` to a different module. Now you need to import it
  like this::

      from everett.ext.inifile import ConfigIniEnv

  (#79)

Features:

* Everett now logs configuration discovery in the ``everett`` logger at the
  ``logging.DEBUG`` level. This is helpful for trouble-shooting some kinds of
  issues. (#74)

Fixes:

* Everett no longer requires ``configobj``--it's now optional. If you use
  ``ConfigIniEnv``, you can install it with::

      $ pip install everett[ini]

  (#79)

* Fixed list parsing and file discovery in ConfigIniEnv so they match the
  docs and are more consistent with other envs. Thank you, apollo13! (#71)

* Added a ``.basic_config()`` for fast opinionated setup that uses the
  process environment and a ``.env`` file in the current working directory.

* Switching to semver.


0.9 (April 7th, 2017)
---------------------

Changed:

* Rewrite Sphinx extension. The extension is now in the ``everett.sphinxext``
  module and the directive is now ``.. autocomponent::``. It generates better
  documentation and it now indexes Everett components and options.

  This is backwards-incompatible. You will need to update your Sphinx
  configuration and documentation.

* Changed the ``HISTORY.rst`` structure.

* Changed the repr for ``everett.NO_VALUE`` to ``"NO_VALUE"``.

* ``InvalidValueError`` and ``ConfigurationMissingError`` now have
  ``namespace``, ``key``, and ``parser`` attributes allowing you to build your
  own messages.

Fixed:

* Fix an example in the docs where the final key was backwards. Thank you, pjz!

Documentation fixes and updates.


0.8 (January 24th, 2017)
------------------------

Added:

* Add ``:namespace:`` and ``:case:`` arguments to autoconfig directive. These
  make it easier to cater your documentation to your project's needs.

* Add support for Python 3.6.

Minor documentation fixes and updates.


0.7 (January 5th, 2017)
-----------------------

Added:

* Feature: You can now include documentation hints and urls for
  ``ConfigManager`` objects and config options. This will make it easier for
  your users to debug configuration errors they're having with your software.

Fixed:

* Fix ``ListOf`` so it returns empty lists rather than a list with a single
  empty string.

Documentation fixes and updates.


0.6 (November 28th, 2016)
-------------------------

Added:

* Add ``RequiredConfigMixin.get_runtime_config()`` which returns the runtime
  configuration for a component or tree of components. This lets you print
  runtime configuration at startup, generate INI files, etc.

* Add ``ConfigObjEnv`` which lets you use an object for configuration. This
  works with argparse's Namespace amongst other things.

Changed:

* Change ``:show-docstring:`` to take an optional value which is the attribute
  to pull docstring content from. This means you don't have to mix programming
  documentation with user documentation--they can be in different attributes.

* Improve configuration-related exceptions. With Python 3, configuration errors
  all derive from ``ConfigurationError`` and have helpful error messages that
  should make it clear what's wrong with the configuration value. With Python 2,
  you can get other kinds of Exceptions thrown depending on the parser used, but
  configuration error messages should still be helpful.

Documentation fixes and updates.


0.5 (November 8th, 2016)
------------------------

Added:

* Add ``:show-docstring:`` flag to ``autoconfig`` directive.

* Add ``:hide-classname:`` flag to ``autoconfig`` directive.

Changed:

* Rewrite ``ConfigIniEnv`` to use configobj which allows for nested sections in
  INI files. This also allows you to specify multiple INI files and have later
  ones override earlier ones.

Fixed:

* Fix ``autoconfig`` Sphinx directive and add tests--it was all kinds of broken.

Documentation fixes and updates.


0.4 (October 27th, 2016)
------------------------

Added:

* Add ``raw_value`` argument to config calls. This makes it easier to write code
  that prints configuration.

Fixed:

* Fix ``listify(None)`` to return ``[]``.

Documentation fixes and updates.


0.3.1 (October 12th, 2016)
--------------------------

Fixed:

* Fix ``alternate_keys`` with components. Previously it worked for everything
  but components. Now it works with components, too.

Documentation fixes and updates.


0.3 (October 6th, 2016)
-----------------------

Added:

* Add ``ConfigManager.from_dict()`` shorthand for building configuration
  instances.

* Add ``.get_namespace()`` to ``ConfigManager`` and friends for getting
  the complete namespace for a given config instance as a list of strings.

* Add ``alternate_keys`` to config call. This lets you specify a list of keys in
  order to try if the primary key doesn't find a value. This is helpful for
  deprecating keys that you used to use in a backwards-compatible way.

* Add ``root:`` prefix to keys allowing you to look outside of the current
  namespace and at the configuration root for configuration values.

Changed:

* Make ``ConfigDictEnv`` case-insensitive to keys and namespaces.

Documentation fixes and updates.


0.2 (August 16th, 2016)
-----------------------

Added:

* Add ``ConfigEnvFileEnv`` for supporting ``.env`` files. Thank you, Paul!

* Add "on" and "off" as valid boolean values. This makes it easier to use config
  for feature flippers. Thank you, Paul!

Changed:

* Change ``ConfigIniEnv`` to take a single path or list of paths. Thank you,
  Paul!

* Make ``NO_VALUE`` falsy.

Fixed:

* Fix ``__call__`` returning None--it should return ``NO_VALUE``.

Lots of docs updates: finished the section about making your own parsers, added
a section on using dj-database-url, added a section on django-cache-url and
expanded on existing examples.


0.1 (August 1st, 2016)
----------------------

Initial writing.
