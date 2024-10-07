.. NOTE: Make sure to edit the template for this file in docs_tmpl/ and
.. not the cog-generated version.

=============
Configuration
=============

.. contents::
   :local:


Extracting values
=================

Once you have a configuration manager set up with sources, you can pull
configuration values from it.

Configuration must have a key. Everything else is optional.

Examples:

::

    config("password")

The key is "password".

The value is parsed as a string.

There is no default value provided so if "password" isn't provided in any of
the configuration sources, then this will raise a
:py:class:`everett.ConfigurationError`.

This is what you want to do to require that a configuration value exist.

::

    config("name", raise_error=False)

The key is "name".

The value is parsed as a string.

There is no default value provided and raise_error is set to False, so if
this configuration variable isn't set anywhere, the result of this will be
``everett.NO_VALUE``.

.. Note::

   :py:data:`everett.NO_VALUE` is a falsy value so you can use it in
   comparative contexts::

       debug = config("DEBUG", parser=bool, raise_error=False)
       if not debug:
           pass

::

    config("port", parser=int, default="5432")

The key is "port".

The value is parsed using int.

There is a default provided, so if this configuration variable isn't set in
the specified sources, the default will be false.

Note that the default value is always a string that's parseable by the
parser.

::

    config("username", namespace="db")

The key is "username".

The namespace is "db".

There's no default, so if there's no "username" in namespace "db"
configuration variable set in the sources, this will raise a
:py:class:`everett.ConfigurationError`.

If you're looking up values in the process environment, then the full
key would be ``DB_USERNAME``.

::

    config("password", namespace="postgres", alternate_keys=["db_password", "root:postgres_password"])

The key is "password".

The namespace is "postgres".

If there is no key "password" in namespace "postgres", then it looks for
"db_password" in namespace "postgres". This makes it possible to deprecate
old key names, but still support them.

If there is no key "password" or "db_password" in namespace "postgres", then
it looks at "postgres_password" in the root namespace. This allows you to
have multiple components that share configuration like credentials and
hostnames.

::

    config(
        "debug", default="false", parser=bool,
        doc="Set to True for debugmode; False for regular mode",
    )

You can provide a ``doc`` argument which will give users users who are trying to
configure your software a more helpful error message when they hit a configuration
error.

Example of error message for an option that specifies ``doc`` when trying to
set ``DEBUG`` to ``foo``:

.. [[[cog
   import cog
   import os
   import subprocess
   if os.path.exists(".env"):
       os.remove(".env")
   os.environ["DEBUG"] = "foo"
   ret = subprocess.run(["python", "examples/myserver.py"], capture_output=True)
   stderr = ret.stderr.decode("utf-8").strip()
   stderr = stderr[stderr.find("everett.InvalidValueError"):]
   cog.outl("\n::\n")
   cog.outl("   $ python example.py")
   cog.outl("   <traceback>")
   for line in stderr.splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   ]]]

::

   $ python example.py
   <traceback>
   everett.InvalidValueError: ValueError: 'foo' is not a valid bool value
   DEBUG requires a value parseable by everett.manager.parse_bool
   DEBUG docs: Set to True for debugmode; False for regular mode
   Project docs: Check https://example.com/configuration for documentation.

.. [[[end]]]

That last line comes directly from the ``doc`` argument you provide.


.. automethod:: everett.manager.ConfigManager.__call__
   :noindex:

.. autoclass:: everett.ConfigurationError
   :noindex:

.. autoclass:: everett.InvalidValueError
   :noindex:

.. autoclass:: everett.ConfigurationMissingError
   :noindex:

.. autoclass:: everett.InvalidKeyError
   :noindex:


Namespaces
==========

Everett has namespaces for grouping related configuration values.

For example, this uses "username", "password", and "port" configuration keys
in the "db" namespace:

.. literalinclude:: ../examples/namespaces.py
   :language: python

These variables in the environment would be ``DB_USERNAME``, ``DB_PASSWORD``
and ``DB_PORT``.

.. [[[cog
   import cog
   import os
   import subprocess
   if os.path.exists(".env"):
       os.remove(".env")
   ret = subprocess.run(["python", "examples/namespaces.py"], capture_output=True)
   cog.outl("\n::\n")
   cog.outl("   $ python namespaces.py")
   for line in ret.stdout.decode("utf-8").splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   ]]]

::

   $ python namespaces.py
   Opened database with admin/ou812 on port 5432

.. [[[end]]]


This is helpful when you need to create two of the same thing, but using
separate configuration.

What if we had source and destination databases and needed to have the
configuration keys separated?

.. literalinclude:: ../examples/namespaces2.py
   :language: python

.. [[[cog
   import cog
   import os
   import subprocess
   if os.path.exists(".env"):
       os.remove(".env")
   ret = subprocess.run(["python", "examples/namespaces2.py"], capture_output=True)
   cog.outl("\n::\n")
   cog.outl("   $ python namespaces2.py")
   for line in ret.stdout.decode("utf-8").splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   ]]]

::

   $ python namespaces2.py
   Opened database with admin/ou812 on port 5432
   Opened database with admin/P9rwvnnj8CidECMb on port 5432

.. [[[end]]]


Handling exceptions when extracting values
==========================================

When the namespaced key isn't found in any of the sources, then Everett will
raise an exception that is a subclass of
:py:class:`everett.ConfigurationError`. This makes it easier to
programmatically figure out what happened.

If you don't like what Everett prints by default, you can catch
the errors and print something different.

For example:

.. literalinclude:: ../examples/handling_exceptions.py
   :language: python


Also, you can change the structure of the error message by passing in a ``msg_builder``
argument to the :py:class:`everett.manager.ConfigManager`.

For example, say your project is entirely done with INI configuration. Then you'd
want to tailor the message accordingly.

.. literalinclude:: ../examples/msg_builder.py
   :language: python

That prints this:

.. [[[cog
   import cog
   import os
   import subprocess
   os.environ["DEBUG"] = "lizard"
   if os.path.exists(".env"):
       os.remove(".env")
   ret = subprocess.run(["python", "examples/msg_builder.py"], capture_output=True)
   stderr = ret.stderr.decode("utf-8").strip()
   stderr = stderr[stderr.find("everett.InvalidValueError"):]
   cog.outl("\n::\n")
   cog.outl("   $ DEBUG=lizard python msg_builder.py")
   cog.outl("   <traceback>")
   for line in stderr.splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   del os.environ["DEBUG"]
   ]]]

::

   $ DEBUG=lizard python msg_builder.py
   <traceback>
   everett.InvalidValueError: Dear user. debug in section [main] is not correct. Please fix it.

.. [[[end]]]


Trouble-shooting and logging what happened
=============================================

If you have a non-trivial Everett configuration, it might be difficult to
figure out exactly why a key lookup failed.

Everett logs to the ``everett`` logger at the ``logging.DEBUG`` level. You
can enable this logging and get a clearer idea of what's going on.

See `Python logging documentation
<https://docs.python.org/3/library/logging.html>`_ for details on enabling
logging.
