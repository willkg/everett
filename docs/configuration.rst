=============
Configuration
=============

.. contents::


Setting up configuration in your app
====================================

Create a ConfigManager and specify sources
------------------------------------------

Configuration is handled by a ``ConfigManager``. The ``ConfigManager`` handles
looking up configuration keys across specified sources to resolve them to
a value.

You can create a basic ``ConfigManager`` like this:

.. literalinclude:: code/configuration_basic.py
   :language: python


You can also specify the source environments in the order you want them
looked at.

For example:

.. literalinclude:: code/configuration_sources.py
   :language: python


Specify pointer to configuration documentation
----------------------------------------------

In addition to a list of sources, you can provide a ``doc`` argument. You can
use this to guide users hitting configuration errors to configuration
documentation.

For example:

.. literalinclude:: code/configuration_doc.py


Let's configure the program wrong and run it to see what it tells us:

::

   $ python trivial.py
   Debug mode off.

   $ DEBUG=true python trivial.py
   Debug mode is on!

   $ DEBUG=omg python trivial.py
   Traceback (most recent call last):
     File "/home/willkg/mozilla/everett/everett/manager.py", line 908, in __call__
       return parser(val)
     File "/home/willkg/mozilla/everett/everett/manager.py", line 109, in parse_bool
       raise ValueError('"%s" is not a valid bool value' % val)
   ValueError: "omg" is not a valid bool value

   During handling of the above exception, another exception occurred:

   Traceback (most recent call last):
     File "configuration_doc.py", line 22, in <module>
       main()
     File "configuration_doc.py", line 12, in main
       doc='True to put the app in debug mode. Don\'t use this in production!'
     File "/home/willkg/mozilla/everett/everett/manager.py", line 936, in __call__
       raise InvalidValueError(msg)
   everett.InvalidValueError: ValueError: "omg" is not a valid bool value
   namespace=None key=debug requires a value parseable by everett.manager.parse_bool
   True to put the app in debug mode. Don't use this in production!
   For configuration help, see https://example.com/configuration


Here, we see the documentation for the configuration item, the documentation
from the ``ConfigManager``, and the specific Python exception information.


Where to put ConfigManager instance
===================================

You can create the ``ConfigManager`` when instantiating an app class as a
property on that instance--that works fine.

You could create the ``ConfigManager`` as a module-level singleton. That's
fine, too.

``ConfigManager`` should be thread-safe and re-entrant with the provided
sources. If you implement your own configuration environments, then
thread-safety and re-entrantcy depend on whether your configuration
environments are safe in these ways.


Configuration sources
=====================

Dict (ConfigDictEnv)
--------------------

.. autoclass:: everett.manager.ConfigDictEnv
   :noindex:


Process environment (ConfigOSEnv)
---------------------------------

.. autoclass:: everett.manager.ConfigOSEnv
   :noindex:


ENV files (ConfigEnvFileEnv)
----------------------------

.. autoclass:: everett.manager.ConfigEnvFileEnv
   :noindex:


Python objects (ConfigObjEnv)
-----------------------------

.. autoclass:: everett.manager.ConfigObjEnv
   :noindex:


INI files (ConfigIniEnv)
------------------------

.. autoclass:: everett.ext.inifile.ConfigIniEnv
   :noindex:


YAML files (ConfigYamlEnv)
--------------------------

.. autoclass:: everett.ext.yamlfile.ConfigYamlEnv
   :noindex:


Implementing your own configuration environments
------------------------------------------------

You can implement your own configuration environments. For example, maybe you
want to pull configuration from a database or Redis or a post-it note on the
refrigerator.

They just need to implement the ``.get()`` method. A no-op implementation is
this:

.. literalinclude:: code/configuration_implementing_sources.py
   :language: python


Generally, environments should return a value if the key exists in that
environment and should return ``NO_VALUE`` if and only if the key does not
exist in that environment.

For exceptions, it depends on what you want to have happen. It's ok to let
exceptions go unhandled--Everett will wrap them in a :py:class:`everett.ConfigurationError`.
If your environment promises never to throw an exception, then you should
handle them all and return ``NO_VALUE`` since with that promise all exceptions
would indicate the key is not in the environment.


Extracting values
=================

Once you have a configuration manager set up with sources, you can pull
configuration values from it.

Configuration must have a key. Other than that, everything is optionally
specified.

.. automethod:: everett.manager.ConfigManager.__call__

Some more examples:

``config("password")``
    The key is "password".

    The value is parsed as a string.

    There is no default value provided so if "password" isn't provided in any of
    the configuration sources, then this will raise a
    :py:class:`everett.ConfigurationError`.

    This is what you want to do to require that a configuration value exist.

``config("name", raise_error=False)``
    The key is "name".

    The value is parsed as a string.

    There is no default value provided and raise_error is set to False, so if
    this configuration variable isn't set anywhere, the result of this will be
    ``everett.NO_VALUE``.

    .. Note::

       ``everett.NO_VALUE`` is a falsy value so you can use it in comparative
       contexts::

           debug = config("DEBUG", parser=bool, raise_error=False)
           if not debug:
               pass

``config("debug", default="false", parser=bool)``
    The key is "debug".

    The value is parsed using the special Everett bool parser.

    There is a default provided, so if this configuration variable isn't set in
    the specified sources, the default will be false.

    Note that the default value is always a string that's parseable by the
    parser.

``config("username", namespace="db")``
    The key is "username".

    The namespace is "db".

    There's no default, so if there's no "username" in namespace "db"
    configuration variable set in the sources, this will raise a
    :py:class:`everett.ConfigurationError`.

    If you're looking up values in the process environment, then the full
    key would be ``DB_USERNAME``.

``config("password", namespace="postgres", alternate_keys=["db_password", "root:postgres_password"])``
    The key is "password".

    The namespace is "postgres".

    If there is no key "password" in namespace "postgres", then it looks for
    "db_password" in namespace "postgres". This makes it possible to deprecate
    old key names, but still support them.

    If there is no key "password" or "db_password" in namespace "postgres", then
    it looks at "postgres_password" in the root namespace. This allows you to
    have multiple components that share configuration like credentials and
    hostnames.

``config("port", parser=int, doc="The port you want this to listen on.")``
    You can provide a ``doc`` argument which will give users users who are trying to
    configure your software a more helpful error message when they hit a configuration
    error.

    Example of error message with ``doc``::

        everett.InvalidValueError: ValueError: invalid literal for int() with base 10:
        'bar'; namespace=None key=foo requires a value parseable by int
        The port you want this to listen on.

    That last line comes directly from the ``doc`` argument you provide.


.. autoclass:: everett.ConfigurationError
   :noindex:

.. autoclass:: everett.InvalidValueError
   :noindex:

.. autoclass:: everett.ConfigurationMissingError
   :noindex:

.. autoclass:: everett.InvalidKeyError
   :noindex:


Handling exceptions when extracting values
==========================================

When the namespaced key isn't found in any of the sources, then Everett will
always a subclass of :py:class:`everett.ConfigurationError`. This makes it
easier to programmatically figure out what happened.

For example:

.. literalinclude:: code/configuration_handling_exceptions.py

That logs this::

   ERROR:root:logged exception gah!
   Traceback (most recent call last):
     File "/home/willkg/mozilla/everett/src/everett/manager.py", line 1197, in __call__
       parsed_val = parser(val)
     File "/home/willkg/mozilla/everett/src/everett/manager.py", line 226, in parse_bool
       raise ValueError(f"{val!r} is not a valid bool value")
   ValueError: 'monkey' is not a valid bool value

   During handling of the above exception, another exception occurred:

   Traceback (most recent call last):
     File "code/configuration_handling_exceptions.py", line 13, in <module>
       some_val = config("debug_mode", parser=bool)
     File "/home/willkg/mozilla/everett/src/everett/manager.py", line 1217, in __call__
       raise InvalidValueError(msg, namespace, key, parser)
   everett.InvalidValueError: ValueError: 'monkey' is not a valid bool value
   DEBUG_MODE requires a value parseable by everett.manager.parse_bool
   DEBUG_MODE docs: set debug mode



If that output won't be helpful to your users, you can catch the
:py:class:`everett.ConfigurationError` and log/print what will be helpful.

Also, you can change the structure of the error message by passing in a ``msg_builder``
argument to the :py:class:`everett.manager.ConfigManager`.

For example, say your project is entirely done with INI configuration. Then you'd
want to tailor the message accordingly.

.. literalinclude:: code/configuration_msg_builder.py

That logs this::

   ERROR:root:logged exception gah!
   Traceback (most recent call last):
     File "/home/willkg/mozilla/everett/src/everett/manager.py", line 1197, in __call__
       parsed_val = parser(val)
     File "/home/willkg/mozilla/everett/src/everett/manager.py", line 226, in parse_bool
       raise ValueError(f"{val!r} is not a valid bool value")
   ValueError: 'lizard' is not a valid bool value

   During handling of the above exception, another exception occurred:

   Traceback (most recent call last):
     File "code/configuration_msg_builder.py", line 24, in <module>
       debug_mode = config(
     File "/home/willkg/mozilla/everett/src/everett/manager.py", line 1217, in __call__
       raise InvalidValueError(msg, namespace, key, parser)
   everett.InvalidValueError: debug in section [main] requires a value parseable by everett.manager.parse_bool
   debug in [main] docs: Set DEBUG=True to put the app in debug mode. Don't use this in production!
   Project docs:


Namespaces
==========

Everett has namespaces for grouping related configuration values.

For example, say you had database code that required a username, password
and port. You could do something like this::

    def open_db_connection(config):
        username = config('username', namespace='db')
        password = config('password', namespace='db')
        port = config('port', namespace='db', default=5432, parser=int)


    conn = open_db_connection(config)


These variables in the environment would be ``DB_USERNAME``, ``DB_PASSWORD``
and ``DB_PORT``.

This is helpful when you need to create two of the same thing, but using
separate configuration. Extending this example, you could pass the namespace as
an argument.

For example, say you wanted to use ``open_db_connection`` for a source
db and for a dest db::

    def open_db_connection(config, namespace):
        username = config('username', namespace=namespace)
        password = config('password', namespace=namespace)
        port = config('port', namespace=namespace, default=5432, parser=int)


    source = open_db_connection(config, 'source_db')
    dest = open_db_connection(config, 'dest_db')


Then you end up with ``SOURCE_DB_USERNAME`` and friends and
``DEST_DB_USERNAME`` and friends.


Parsers
=======

All parsers are functions that take a string value and return a parsed
instance.

For example:

* ``int`` takes a string value and returns an int.
* ``parse_class`` takes a dotted Python path string value and returns the class
  object
* ``ListOf(str)`` takes a string value and returns a list of strings


.. Note::

   When specifying configuration options, the default value must always be a
   string. When Everett can't find a value for a requested key, it will take
   the default value and pass it through the parser. Because parsers always
   take a string as input, the default value must always be a string.

   This is valid::

       debug = config("debug", parser=bool, default="false")
                                                    ^^^^^^^

   This is **not** valid::

       debug = config("debug", parser=bool, default=False)
                                                    ^^^^^


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


ListOf(parser)
--------------

Everett provides a special ``everett.manager.ListOf`` parser which
parses a list of some other type. For example::

    ListOf(str)  # comma-delimited list of strings
    ListOf(int)  # comma-delimited list of ints

.. autofunction:: everett.manager.ListOf
   :noindex:


dj_database_url
---------------

Everett works with `dj-database-url
<https://pypi.org/project/dj-database-url/>`_. The ``dj_database_url.parse``
function takes a string and returns a Django database connection value.

For example::

    import dj_database_url
    from everett.manager import ConfigManager, ConfigOSEnv

    config = ConfigManager([ConfigOSEnv()])
    DATABASE = {
        "default": config("DATABASE_URL", parser=dj_database_url.parse)
    }


That'll pull the ``DATABASE_URL`` value from the environment (it throws an
error if it's not there) and runs it through ``dj_database_url`` which parses
it and returns what Django needs.

With a default::

    import dj_database_url
    from everett.manager import ConfigManager, ConfigOSEnv

    config = ConfigManager([ConfigOSEnv()])
    DATABASE = {
        "default": config("DATABASE_URL", default="sqlite:///my.db",
                          parser=dj_database_url.parse)
    }


.. Note::

   To use dj-database-url, you'll need to install it separately. Everett doesn't
   depend on it or require it to be installed.


django-cache-url
----------------

Everett works with `django-cache-url <https://pypi.org/project/django-cache-url/>`_.

For example::

    import django_cache_url
    from everett.manager import ConfigManager, ConfigOSEnv

    config = ConfigManager([ConfigOSEnv()])
    CACHES = {
        'default': config('CACHE_URL', parser=django_cache_url.parse)
    }


That'll pull the ``CACHE_URL`` value from the environment (it throws an error if
it's not there) and runs it through ``django_cache_url`` which parses it and
returns what Django needs.

With a default::

    import django_cache_url
    from everett.manager import ConfigManager, ConfigOSEnv

    config = ConfigManager([ConfigOSEnv()])
    CACHES = {
        'default': config('CACHE_URL', default='locmem://myapp',
                          parser=django_cache_url.parse)
    }


.. Note::

   To use django-cache-url, you'll need to install it separately. Everett
   doesn't require it to be installed.


Implementing your own parsers
-----------------------------

Implementing your own parser should be straight-forward. Parsing functions
always take a string and return the Python value you need.

If the value is not parseable, the parsing function should raise a ``ValueError``.

For example, say we wanted to implement a parser that returned yes/no/no-answer:

.. literalinclude:: code/configuration_parser.py
   :language: python


Say you wanted to make a parser class that's line delimited:

.. literalinclude:: code/configuration_parser2.py


Trouble-shooting and logging what happened
==========================================

If you have a non-trivial Everett configuration, it might be difficult to
figure out exactly why a key lookup failed.

Everett logs to the ``everett`` logger at the ``logging.DEBUG`` level. You
can enable this logging and get a clearer idea of what's going on.

See `Python logging documentation
<https://docs.python.org/3/library/logging.html>`_ for details on enabling
logging.
