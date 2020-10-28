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
3. easy documentation of configuration for users

From that, Everett has the following features:

* is composeable and flexible
* makes it easier to provide helpful error messages for users trying to
  configure your software
* supports auto-documentation of configuration with a Sphinx
  ``autocomponent`` directive
* has an API for testing configuration variations in your tests
* can pull configuration from a variety of specified sources (environment,
  INI files, YAML files, dict, write-your-own)
* supports parsing values (bool, int, lists of things, classes,
  write-your-own)
* supports key namespaces
* supports component architectures
* works with whatever you're writing--command line tools, web sites, system
  daemons, etc

Everett is inspired by `python-decouple
<https://github.com/henriquebastos/python-decouple>`_ and `configman
<https://configman.readthedocs.io/en/latest/>`_.


Quick start
===========

Fast start example
------------------

You're writing an app and want it to look for configuration:

1. in an ``.env`` file in the current working directory
2. then in the process environment

You set up a configuration manager like this::

    from everett.manager import ConfigManager

    config = ConfigManager.basic_config()


and use it to get configuration values like this::

    api_host = config("api_host")

    max_bytes = config("max_bytes", default=1000, parser=int)

    debug_mode = config("debug", default="False", parser=bool)


When you outgrow that or need different variations of it, you can switch to
creating a ``ConfigManager`` instance that meets your needs.


More complex example
--------------------

You're writing an app and want to pull configuration (in order of prcedence):

1. from the process environment
2. from an INI file stored in a place specified by (in order of precedence):
   1. ``MYAPP_INI`` in the environment
   2. ``~/.myapp.ini``
   3. ``/etc/myapp.ini``

First, you need need to install the additional requirements for INI file
environments::

    pip install everett[ini]


Then set up the ``ConfigManager``::

    import os
    import sys

    from everett.ext.inifile import ConfigIniEnv
    from everett.manager import ConfigManager, ConfigOSEnv


    def build_config_manager():
        return ConfigManager(
            # Specify one or more configuration environments in
            # the order they should be checked
            environments=[
                # Look in OS process environment first
                ConfigOSEnv(),

                # Look in INI files in order specified
                ConfigIniEnv([
                    os.environ.get("MYAPP_INI"),
                    "~/.myapp.ini",
                    "/etc/myapp.ini"
                ]),
            ],

            # Provide users a link to documentation for when they hit
            # configuration errors
            doc="Check https://example.com/configuration for docs."
        )


Then use it::

    def is_debug(config):
        return config(
            "debug", default="False", parser=bool,
            doc="Set to True for debugmode; False for regular mode."
        )

    config = build_config_manager()

    if is_debug(config):
        print('DEBUG MODE ON!')


Let's write some tests that verify behavior based on the ``debug``
configuration value::

    from myapp import get_config, is_debug

    from everett.manager import config_override


    @config_override(DEBUG="true")
    def test_debug_true():
        assert is_debug(get_config()) is True


    def test_debug_false():
        with config_override(DEBUG="false"):
            assert is_debug(get_config()) is False


If the user sets ``DEBUG`` with a bad value, they get a helpful error message
with the documentation for the configuration option and the ``ConfigManager``::

    $ DEBUG=foo python myprogram.py
    <traceback>
    namespace=None key=debug requires a value parseable by bool
    Set to True for debugmode; False for regular mode.
    Check https://example.com/configuration for docs.


Configuration classes
---------------------

Everett supports centralizing your configuration in a class. Instead of having
configuration-related bits defined across your codebase, you can define it in
a class. Let's rewrite the above example using a configuration class.

First, create a configuration class::

    import os
    import sys

    from everett.component import RequiredConfigMixin, ConfigOptions
    from everett.ext.inifile import ConfigIniEnv
    from everett.manager import ConfigManager, ConfigOSEnv


    class AppConfig(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            "debug",
            parser=bool,
            default="false",
            doc="Switch debug mode on and off.")
        )
    

Then we set up our ``ConfigManager``::

    def get_config():
        manager = ConfigManager(
            # Specify one or more configuration environments in
            # the order they should be checked
            environments=[
                # Look in OS process environment first
                ConfigOSEnv(),

                # Look in INI files in order specified
                ConfigIniEnv([
                    os.environ.get("MYAPP_INI"),
                    "~/.myapp.ini",
                    "/etc/myapp.ini"
                ]),
            ],

            # Provide users a link to documentation for when they hit
            # configuration errors
            doc="Check https://example.com/configuration for docs."
        )

        # Apply the configuration class to the configuration manager
        # so that it handles option properties like defaults, parsers,
        # documentation, and so on.
        return manager.with_options(AppConfig())


Then use it::

    config = get_config()

    if config("debug"):
        print("DEBUG MODE ON!")


Further, you can auto-generate configuration documentation by including the
``everett.sphinxext`` Sphinx extension and using the ``autocomponent``
directive::

    .. autocomponent:: path.to.AppConfig


That has some niceties:

1. your application configuration is centralized in one place instead
   of spread out across your code base

2. you can use the ``autocomponent`` Sphinx directive to auto-generate
   configuration documentation for your users


Everett components
------------------

Everett supports components that require configuration. Say your app needs to
connect to RabbitMQ. With Everett, you can define the component's configuration
needs in the component class::

    from everett.component import RequiredConfigMixin, ConfigOptions


    class RabbitMQComponent(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            "host",
            doc="RabbitMQ host to connect to"
        )
        required_config.add_option(
            "port",
            default="5672",
            doc="Port to use",
            parser=int
        )
        required_config.add_option(
            "queue_name",
            doc="Queue to insert things into"
        )

        def __init__(self, config):
            # Bind the configuration to just the configuration this
            # component requires such that this component is
            # self-contained
            self.config = config.with_options(self)

            self.host = self.config("host")
            self.port = self.config("port")
            self.queue_name = self.config("queue_name")


Then instantiate a ``RabbitMQComponent`` that looks for configuration keys
in the ``rmq`` namespace::

    queue = RabbitMQComponent(config.with_namespace("rmq"))


The ``RabbitMQComponent`` has a ``HOST`` key, so your configuration would
need to define ``RMQ_HOST``.

You can auto-generate configuration documentation for this component in your
Sphinx docs by including the ``everett.sphinxext`` Sphinx extension and
using the ``autocomponent`` directive::

    .. autocomponent:: path.to.RabbitMQComponent
       :namespace: rmq


Say your app actually needs to connect to two separate queues--one for regular
processing and one for priority processing::

    from everett.manager import ConfigManager

    config = ConfigManager.basic_config()

    # Apply the "rmq" namespace to the configuration so all keys are
    # prepended with RMQ_
    rmq_config = config.with_namespace("rmq")

    # Create a RabbitMQComponent with RMQ_REGULAR_ prepended to keys
    regular_queue = RabbitMQComponent(rmq_config.with_namespace("regular"))

    # Create a RabbitMQComponent with RMQ_PRIORITY_ prepended to keys
    priority_queue = RabbitMQComponent(rmq_config.with_namespace("priority"))


In your environment, you provide the regular queue configuration with
``RMQ_REGULAR_HOST``, etc and the priority queue configuration with
``RMQ_PRIORITY_HOST``, etc.

Same component code. Two different instances pulling configuration from two
different namespaces.

Components support subclassing, mixins and all that, too.


Install
=======

Install from PyPI
-----------------

Run::

    $ pip install everett

If you want to use the ``ConfigIniEnv``, you need to install its requirements
as well::

    $ pip install everett[ini]

If you want to use the ``ConfigYamlEnv``, you need to install its requirements
as well::

    $ pip install everett[yaml]


Install for hacking
-------------------

Run::

    # Clone the repository
    $ git clone https://github.com/willkg/everett

    # Create a virtualenvironment
    $ mkvirtualenv --python /usr/bin/python3 everett
    ...

    # Install Everett and dev requirements
    $ pip install -r requirements-dev.txt


Why not other libs?
===================

Most other libraries I looked at had one or more of the following issues:

* were tied to a specific web app framework
* didn't allow you to specify configuration sources
* provided poor error messages when users configure things wrong
* had a global configuration object
* made it really hard to override specific configuration when writing tests
* had no facilities for auto-generating configuration documentation
