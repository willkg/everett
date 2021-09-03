.. NOTE: Make sure to edit the template for this file in docs_tmpl/ and
.. not the cog-generated version.

======================
Configuration Managers
======================

.. contents::
   :local:


Creating a ConfigManager and specifying environments
====================================================

First, you define a :py:class:`everett.manager.ConfigManager` which specifies
the environments you want to pull configuration from.

Then you can use the :py:class:`everett.manager.ConfigManager` to look up
configuration keys. The :py:class:`everett.manager.ConfigManager` will go
through the environments in order to find a value for the configuration key.
Once it finds a value, it runs it through the parser and returns the parsed
value.

There are a few ways to create a :py:class:`everett.manager.ConfigManager`.

The easiest is to use :py:func:`everett.manager.ConfigManager.basic_config`.

For example:

.. literalinclude:: ../examples/myserver.py
   :language: python

That creates a :py:class:`everett.manager.ConfigManager` that looks up
configuration keys in these environments:

1. the process environment
2. the specified env file which defaults to ``.env``

That works for most cases.

You can create your own :py:class:`everett.manager.ConfigManager` and specify
environments specific to your needs.

For example:

.. literalinclude:: ../examples/myserver_with_environments.py
   :language: python


Specifying configuration documentation
======================================

When building a :py:class:`everett.manager.ConfigManager`, you can specify
documentation for configuration. It will get printed when there are
configuration errors. This is a great place to put a link to configuration
documentation.

For example:

.. literalinclude:: ../examples/myserver.py
   :language: python


Let's set ``DEBUG`` wrong and see what it tells us:

::

    $ python myserver.py
    host: localhost
    port: 8000
    debug_mode: False

    $ DEBUG=foo python myserver.py
    <traceback>
    everett.InvalidValueError: ValueError: 'foo' is not a valid bool value
    DEBUG requires a value parseable by everett.manager.parse_bool
    DEBUG docs: Set to True for debugmode; False for regular mode
    Project docs: Check https://example.com/configuration for documentation.


Here, we see the documentation for the ``DEBUG`` option, the documentation from
the ``ConfigManager``, and the specific Python exception information.
