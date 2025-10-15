History
=======

3.5.0 (October 15th, 2025)
--------------------------

Backwards incompatibel changes:

* Drop support for Python 3.9. (#282)

* Deprecate Everett.

  I encourage you to switch from Everett to pydantic-settings.
  See https://github.com/willkg/everett/issues/278

Fixes and features:

* Add support for Python 3.14. (#283)


3.4.0 (October 30th, 2024)
--------------------------

Backwards incompatible changes:

* Drop support for Python 3.8. Thanks, Rob!

Fixes and features:

* Add support for Python 3.13. (#260) Thanks, Rob!

* Add support for underscore as first character in variable names in env files.
  (#263)

* Add ``ChoiceOf`` parser for enforcing configuration values belong in
  specified value domain. (#253)

* Fix ``autocomponentconfig`` to support components with no options. (#244)

* Add ``allow_empty`` option to ``ListOf`` parser that lets you specify whether
  empty strings are a configuration error or not. (#268)


3.3.0 (November 6th, 2023)
--------------------------

Backwards incompatible changes:

* Drop support for Python 3.7. (#220)

Fixes and features:

* Add support for Python 3.12 (#221)

* Fix env file parsing in regards to quotes. (#230)


3.2.0 (March 21st, 2023)
------------------------

Fixes and features:

* Implement ``default_if_empty`` argument which will return the default value
  (if specified) if the value is the empty string. (#205)

* Implement ``parse_time_period`` parser for converting time periods like "10m4s"
  into the total number of seconds that represents.

  ::

      >>> from everett.manager import parse_time_period
      >>> parse_time_period("4m")
      240

  (#203)

* Implement ``parse_data_size`` parser for converting values like "40gb" into
  the total number of bytes that represents.

  ::

      >>> from everett.manager import parse_data_size
      >>> parse_time_period("40gb")
      40000000000

  (#204)

* Fix an ``UnboundLocalError`` when using ``automoduleconfig`` and providing a
  Python dotted path to a thing that either kicks up an ``ImportError`` or
  doesn't exist. Now it raises a more helpful error. (#201)


3.1.0 (October 26th, 2022)
--------------------------

Fixes and features:

* Add support for Python 3.11. (#187)

* Add ``raise_configuration_error`` method on ``ConfigManager``. (#185)

* Improve ``automoduleconfig`` to walk the whole AST and document configuration
  set by assign::

      SOMEVAR = _config("somevar")

  and dict::
     
      SOMEGROUP = {
          "SOMEVAR": _config("somevar"),
      }

  (#184)

* Fix options not showing up on ReadTheDocs. (#186)


3.0.0 (January 13th, 2022)
--------------------------

Backwards incompatible changes:

* Dropped support for Python 3.6. (#176)

* Dropped ``autocomponent`` Sphinx directive in favor of
  ``autocomponentconfig``.

Fixes and features:

* Add support for Python 3.10. (#173)

* Rework namespaces so that you can apply a namespace (``with_namespace()``)
  after binding a component (``with_options()``) (#175)

* Overhauled, simplified, and improved documentation. Files with example output
  are now generated using `cog <https://pypi.org/project/cogapp/>`_.

* Rewrite Sphinx extension.

  This now supports manually documenting configuration using
  ``everett:component`` and ``everett:option`` directives.

  This adds ``:everett:component:`` and ``:everett:option:`` roles for linking
  to specific configuration in the docs.

  It also addsh ``autocomponentconfig`` and ``automoduleconfig`` directives for
  automatically generating documentation.

  When using these directives, items are added to the index and everything is
  linkable making it easier to find and talk to users about specific
  configuration items. (#172)


2.0.1 (August, 23rd, 2021)
--------------------------

Fixes:

* Fix Sphinx warning about roles in Everett sphinxext. (#165)

* Fix ``get_runtime_config`` to work with slots (#166)


2.0.0 (July 27th, 2021)
-----------------------

Backwards incompatible changes:

* This radically reduces the boilerplate required to define components. It also
  improves the connections between things so it's easier to:

  * determine the configuration required for a single component (taking into
    account superclasses, overriding, etc)
  * determine the runtime configuration for a component tree given a
    configuration manager

  Previously, components needed to subclass RequiredConfigMixin and provide a
  "required_config" class attribute. Something like this::

      from everett.component import RequiredConfigMixin, ConfigOptions

      class SomeClass(RequiredConfigMixin):
          required_config = ConfigOptions()
          required_config.add_option(
              "some_option",
              default="42",
          )

  That's been slimmed down and now looks like this::

      from everett.manager import Option

      class SomeClass:
          class Config:
              some_option = Option(default="42")

  That's much simpler and the underlying implementation code is less tangled
  and complex, too.

  If you used ``everett.component.RequiredConfigMixin`` or
  ``everett.component.ConfigOptions``, you'll need to update your classes.

  If you didn't use those things, then you don't have to make any changes.

  See the documentation on components for how it all works now.

* Changed the way configuration variables are referred to in configuration
  error messages. Previously, I tried to use a general way "namespace=something
  key=somethingelse" but that's confusing and won't match up with project
  documentation.

  I changed it to the convention used in the process environment and
  env files. For example, ``FOO_BAR``.

  If you use INI or YAML for configuration, you can specify a ``msg_builder``
  argument when you build the ``ConfigManager`` and build error messages
  tailored to your users.

Fixes:

* Switch to ``src/`` repository layout.

* Added type annotations and type checking during CI. (#155)

* Standardized on f-strings across the codebase.

* Switched Sphinx theme.

* Update of documentation, fleshed out and simplified examples, cleaned up
  language, reworked structure of API section (previously called Library or
  some unhelpful thing like that), etc.


1.0.3 (October 28th, 2020)
--------------------------

Backwards incompatible changes:

* Dropped support for Python 3.4. (#96)

* Dropped support for Python 3.5. (#116)

Fixes:

* Add support for Python 3.7. (#68)

* Add support for Python 3.8. (#102)

* Add support for Python 3.9. (#117)

* Reformatted code with Black, added Makefile, switched to GitHub Actions.

* Fix ``get_runtime_config()`` to infer namespaces. (#118)

* Fix ``RemovedInSphinx50Warning``. (#115)

* Documentation fixes and clarifications.


1.0.2 (February 22nd, 2019)
---------------------------

Fixes:

* Improve documentation.

* Fix problems when there are nested ``BoundConfigs``. Now they work
  correctly. (#90)

* Add "meta" to options letting you declare additional data on the option
  when you're adding it.

  For example, this lets you do things like mark options as "secrets"
  so that you know which ones to ``******`` out when logging your
  configuration. (#88)


1.0.1 (January 8th, 2019)
-------------------------

Fixes:

* Fix documentation issues.

* Package missing ``everett.ext``. Thank you, dsblank! (#84)


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

* Everett now has a YAML configuration environment. In order to use it, you
  need to install its requirements::

      $ pip install everett[yaml]

  Then you can import it like this::

      from everett.ext.yamlfile import ConfigYamlEnv

  (#72)

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
