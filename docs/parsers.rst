=======
Parsers
=======

.. contents::
   :local:


What's a parser?
================

All parsers are functions that take a string value and return a parsed
instance.

For example:

* ``int`` takes a string value and returns an int.
* ``parse_class`` takes a string value that's a dotted Python path and returns
  the class object
* ``ListOf(str)`` takes a string value that uses a comma delimiter and returns
  a list of strings


.. Note::

   When specifying configuration options, the default value must always be a
   string. When Everett can't find a value for a requested key, it will take
   the default value and pass it through the parser. Because parsers always
   take a string as input, the default value must always be a string.

   Good::

       debug = config("debug", parser=bool, default="false")
                                                    ^^^^^^^

   Bad::

       debug = config("debug", parser=bool, default=False)
                                                    ^^^^^ Not a string


Available parsers
=================

Python types like str, int, float, pathlib.Path
-----------------------------------------------

Python types can convert strings to Python values. You can use these as
parsers:

* ``str``
* ``int``
* ``float``
* ``decimal``
* ``pathlib.Path``


bools
-----

Everett provides a special bool parser that handles more descriptive values for
"true" and "false":

* true: t, true, yes, y, on, 1 (and uppercase versions)
* false: f, false, no, n, off, 0 (and uppercase versions)

.. autofunction:: everett.manager.parse_bool
   :noindex:


classes
-------

Everett provides a ``everett.manager.parse_class`` that takes a string
specifying a module and class and returns the class.

.. autofunction:: everett.manager.parse_class
   :noindex:


data size
---------

Everett provides a ``everett.manager.parse_data_size`` that takes a string
specifying an amount and a data size metric (e.g. kb, kib, tb, etc) and returns
the amount of bytes that represents.

.. autofunction:: everett.manager.parse_data_size
   :noindex:


time period
-----------

Everett provides a ``everett.manager.parse_time_period`` that takes a string
specifying a period of time and returns the total number of seconds represented
by that period.

.. autofunction:: everett.manager.parse_data_size
   :noindex:


ListOf(parser)
--------------

Everett provides a special ``everett.manager.ListOf`` parser which
parses a list of some other type. For example::

    ListOf(str)  # comma-delimited list of strings
    ListOf(int)  # comma-delimited list of ints

.. autofunction:: everett.manager.ListOf
   :noindex:


ChoiceOf(parser, list-of-choices)
---------------------------------

Everett provides a ``everett.manager.ChoiceOf`` parser which can enforce that
configuration values belong to a specificed value domain.

.. autofunction:: everett.manager.ChoiceOf
   :noindex:


dj_database_url
---------------

Everett works with `dj-database-url
<https://pypi.org/project/dj-database-url/>`_. The ``dj_database_url.parse``
function takes a string and returns a Django database connection value.

For example::

    import dj_database_url
    from everett.manager import ConfigManager

    config = ConfigManager.basic_config()
    DATABASES = {
        "default": config("DATABASE_URL", parser=dj_database_url.parse)
    }


That'll pull the ``DATABASE_URL`` value from the environment (it throws an
error if it's not there) and runs it through ``dj_database_url`` which parses
it and returns what Django needs.

With a default::

    import dj_database_url
    from everett.manager import ConfigManager

    config = ConfigManager.basic_config()
    DATABASES = {
        "default": config(
            "DATABASE_URL", default="sqlite:///my.db", parser=dj_database_url.parse
        )
    }


.. Note::

   To use dj-database-url, you'll need to install it separately. Everett doesn't
   depend on it or require it to be installed.


django-cache-url
----------------

Everett works with `django-cache-url <https://pypi.org/project/django-cache-url/>`_.

For example::

    import django_cache_url
    from everett.manager import ConfigManager

    config = ConfigManager.basic_config()
    CACHES = {
        "default": config("CACHE_URL", parser=django_cache_url.parse)
    }


That'll pull the ``CACHE_URL`` value from the environment (it throws an error if
it's not there) and runs it through ``django_cache_url`` which parses it and
returns what Django needs.

With a default::

    import django_cache_url
    from everett.manager import ConfigManager

    config = ConfigManager.basic_config()
    CACHES = {
        "default": config(
            "CACHE_URL", default="locmem://myapp", parser=django_cache_url.parse
        )
    }


.. Note::

   To use django-cache-url, you'll need to install it separately. Everett
   doesn't require it to be installed.


Implementing your own parsers
=============================

Implementing your own parser should be straight-forward. Parsing functions
always take a string and return the Python value you need.

If the value is not parseable, the parsing function should raise a ``ValueError``.

For example, say we wanted to implement a parser that returned yes/no/no-answer
or a parser class that's line delimited:

.. literalinclude:: ../examples/parser_examples.py
   :language: python
