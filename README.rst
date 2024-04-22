.. NOTE: Make sure to edit the template for this file in docs_tmpl/ and
.. not the cog-generated version.

=======
Everett
=======

Everett is a Python configuration library for your app.

:Code:          https://github.com/willkg/everett
:Issues:        https://github.com/willkg/everett/issues
:License:       MPL v2
:Documentation: https://everett.readthedocs.io/


Goals
=====

Goals of Everett:

1. flexible configuration from multiple configured environments
2. easy testing with configuration
3. easy automated documentation of configuration for users

From that, Everett has the following features:

* is flexible for your configuration environment needs and supports
  process environment, env files, dicts, INI files, YAML files,
  and writing your own configuration environments
* facilitates helpful error messages for users trying to configure your
  software
* has a Sphinx extension for documenting configuration including
  ``autocomponentconfig`` and ``automoduleconfig`` directives for
  automatically generating configuration documentation
* facilitates testing of configuration values
* supports parsing values of a variety of types like bool, int, lists of
  things, classes, and others and lets you write your own parsers
* supports key namespaces
* supports component architectures
* works with whatever you're writing--command line tools, web sites, system
  daemons, etc

Everett is inspired by `python-decouple
<https://github.com/henriquebastos/python-decouple>`_ and `configman
<https://configman.readthedocs.io/en/latest/>`_.


Install
=======

Run::

    $ pip install everett

Some configuration environments require additional dependencies::


    # For INI support
    $ pip install 'everett[ini]'

    # for YAML support
    $ pip install 'everett[yaml]'


Quick start
===========

Example::

    # myserver.py

    """
    Minimal example showing how to use configuration for a web app.
    """

    from everett.manager import ConfigManager

    config = ConfigManager.basic_config(
        doc="Check https://example.com/configuration for documentation."
    )

    host = config("host", default="localhost")
    port = config("port", default="8000", parser=int)
    debug_mode = config(
        "debug",
        default="False",
        parser=bool,
        doc="Set to True for debugmode; False for regular mode",
    )

    print(f"host: {host}")
    print(f"port: {port}")
    print(f"debug_mode: {debug_mode}")

Then you can run it::

    $ python myserver.py
    host: localhost
    port: 8000
    debug_mode: False

You can set environment variables to affect configuration::

    $ PORT=7000 python myserver.py
    host: localhost
    port: 7000
    debug_mode: False

It checks a ``.env`` file in the current directory::

    $ echo "HOST=127.0.0.1" > .env
    $ python myserver.py
    host: 127.0.0.1
    port: 8000
    debug_mode: False

It spits out useful error information if configuration is wrong::

    $ DEBUG=foo python myserver.py
    <traceback>
    everett.InvalidValueError: ValueError: 'foo' is not a valid bool value
    DEBUG requires a value parseable by everett.manager.parse_bool
    DEBUG docs: Set to True for debugmode; False for regular mode
    Project docs: Check https://example.com/configuration for documentation.

You can test your code using ``config_override`` in your tests to test various
configuration values::

    # testdebug.py

    """
    Minimal example showing how to override configuration values when testing.
    """

    import unittest

    from everett.manager import ConfigManager, config_override


    class App:
        def __init__(self):
            config = ConfigManager.basic_config()
            self.debug = config("debug", default="False", parser=bool)


    class TestDebug(unittest.TestCase):
        def test_debug_on(self):
            with config_override(DEBUG="on"):
                app = App()
                self.assertTrue(app.debug)

        def test_debug_off(self):
            with config_override(DEBUG="off"):
                app = App()
                self.assertFalse(app.debug)


    if __name__ == "__main__":
        unittest.main()

Run that::

    ..
    ----------------------------------------------------------------------
    Ran 2 tests in 0.000s

    OK

That's perfectly fine for a `12-Factor <https://12factor.net/>`_ app.

When you outgrow that or need different variations of it, you can switch to
creating a ``ConfigManager`` instance that meets your needs.


Why not other libs?
===================

Most other libraries I looked at had one or more of the following issues:

* were tied to a specific web app framework
* didn't allow you to specify configuration sources
* provided poor error messages when users configure things wrong
* had a global configuration object
* made it really hard to override specific configuration when writing tests
* had no facilities for autogenerating configuration documentation
