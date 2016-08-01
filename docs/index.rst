=======
Everett
=======

Goals
=====

This library tries to do configuration with the least amount of fancy-pants
stuff as possible.

1. configuration can come from a variety of specified sources (dict,
   environment, ini files) with explicit and specified overriding rules
2. configuration values can be namespaced to facilitate component-style
   architectures
3. configuration for component-style architectures is autodocumenting
   using Sphinx and the ``autoconfig`` directive
4. easy to test your code in regards to configuration


Why not other libs?
===================

Most other libraries I looked at didn't allow you to specify configuration
sources, had a global configuration object, made it really hard to override
specific configuration when writing tests and had no facilities for
auto-documenting configuration for components.


Quick start
===========

You're writing a web app using some framework that doesn't provide
infrastructure for configuration.

You want to pull configuration from an INI file stored in a place specified by
``FOO_INI`` in the environment. You want to pull infrastructure values from the
environment. Values from the environment should override values from the INI
file.

First, you set up your ``ConfigManager``::

    from everett.manager import ConfigManager

    def get_config():
        return ConfigManager([
            ConfigOSEnv(),
            ConfigIniEnv([
                os.environ.get('FOO_INI'),
                '~/.foo.ini',
                '/etc/foo.ini'
            ]),
        ])


Second, you set up your app::

    class MyWSGIApp(SomeFrameworkApp):
        def __init__(self):
            self.config = get_config()
            self.is_debug = self.config('debug', parser=bool)

    app = MyWSGIApp()


Then you want to write a test for your app::

    from everett.manager import config_override

    def test_debug():
        with config_override(DEBUG='true'):
            # some tests here
            pass

        with config_override(DEBUG='false'):
            # some tests here
            pass


Contents:

.. toctree::
   :maxdepth: 2

   configuration
   components
   library


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

