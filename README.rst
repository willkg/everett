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
  ini files, dict, write-your-own)
* supports parsing values (bool, int, lists of things, classes,
  write-your-own)
* supports key namespaces
* supports component architectures
* works with whatever you're writing--command line tools, web sites, system
  daemons, etc

Everett is inspired by `python-decouple
<https://github.com/henriquebastos/python-decouple>`_ and `configman
<https://configman.readthedocs.io/en/latest/>`_.


Why not other libs?
===================

Most other libraries I looked at had one or more of the following issues:

* were tied to a specific web app framework
* didn't allow you to specify configuration sources
* provided poor error messages when users configure things wrong
* had a global configuration object
* made it really hard to override specific configuration when writing tests
* had no facilities for auto-generating configuration documentation


Quick start
===========

Fast start example
------------------

You have an app and want it to look for configuration first in an ``.env``
file in the current working directory, then then in the process environment.
You can do this::

    from everett.manager import ConfigManager

    config = ConfigManager.basic_config()


Then you can use it like this::

    debug_mode = config('debug', parser=bool)


When you outgrow that or need different variations of it, you can change
that to creating a ``ConfigManager`` from scratch.


More complex example
--------------------

We have an app and want to pull configuration from an INI file stored in
a place specified by ``MYAPP_INI`` in the environment, ``~/.myapp.ini``,
or ``/etc/myapp.ini`` in that order.

We want to pull infrastructure values from the environment.

Values from the environment should override values from the INI file.

First, we need to install the additional requirements for INI file
environments::

    pip install everett[ini]

Then we set up our ``ConfigManager``::

    import os
    import sys

    from everett.ext.inifile import ConfigIniEnv
    from everett.manager import ConfigManager, ConfigOSEnv


    def get_config():
        return ConfigManager(
            # Specify one or more configuration environments in
            # the order they should be checked
            environments=[
                # Look in OS process environment first
                ConfigOSEnv(),

                # Look in INI files in order specified
                ConfigIniEnv([
                    os.environ.get('MYAPP_INI'),
                    '~/.myapp.ini',
                    '/etc/myapp.ini'
                ]),
            ],

            # Provide users a link to documentation for when they hit
            # configuration errors
            doc='Check https://example.com/configuration for docs.'
        )


Then we use it::

    def is_debug(config):
        return config('debug', parser=bool,
            doc='Switch debug mode on and off.')


    config = get_config()

    if is_debug(config):
        print('DEBUG MODE ON!')


Let's write some tests that verify behavior based on the ``debug``
configuration value::

    from myapp import get_config, is_debug

    from everett.manager import config_override


    @config_override(DEBUG='true')
    def test_debug_true():
        assert is_debug(get_config()) is True


    @config_override(DEBUG='false')
    def test_debug_false():
        assert is_debug(get_config()) is False


If the user sets ``DEBUG`` wrong, they get a helpful error message with
the documentation for the configuration option and the ``ConfigManager``::

    $ DEBUG=foo python myprogram.py
    <traceback>
    namespace=None key=debug requires a value parseable by bool
    Switch debug mode on and off.
    Check https://example.com/configuration for docs.


Wrapping configuration in a configuration class
-----------------------------------------------

Everett supports wrapping your configuration in an instance. Let's rewrite
the above example using a configuration class.

First, create a configuration class::

    import os
    import sys

    from everett.component import RequiredConfigMixin, ConfigOptions
    from everett.ext.inifile import ConfigIniEnv
    from everett.manager import ConfigManager, ConfigOSEnv


    class AppConfig(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            'debug',
            parser=bool,
            default='false',
            doc='Switch debug mode on and off.')
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
                    os.environ.get('MYAPP_INI'),
                    '~/.myapp.ini',
                    '/etc/myapp.ini'
                ]),
            ],

            # Provide users a link to documentation for when they hit
            # configuration errors
            doc='Check https://example.com/configuration for docs.'
        )

        # Bind the manager to the configuration class
        return manager.with_options(AppConfig())


Then use it::

    config = get_config()

    if config('debug'):
        print('DEBUG MODE ON!')


Further, you can auto-generate configuration documentation by including the
``everett.sphinxext`` Sphinx extension and using the ``autocomponent``
directive::

    .. autocomponent:: path.to.AppConfig


That kind of looks the same, but it has a few niceties:

1. your application configuration is centralized in one place instead
   of spread out across your code base

2. you can use the ``autocomponent`` Sphinx directive to auto-generate
   configuration documentation for your users


Everett components
------------------

Everett supports components. Say your app needs to connect to RabbitMQ.
With Everett, you can wrap the configuration up with the component::

    from everett.component import RequiredConfigMixin, ConfigOptions


    class RabbitMQComponent(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            'host',
            doc='RabbitMQ host to connect to'
        )
        required_config.add_option(
            'port',
            default='5672',
            doc='Port to use',
            parser=int
        )
        required_config.add_option(
            'queue_name',
            doc='Queue to insert things into'
        )

        def __init__(self, config):
            # Bind the configuration to just the configuration this
            # component requires such that this component is
            # self-contained.
            self.config = config.with_options(self)

            self.host = self.config('host')
            self.port = self.config('port')
            self.queue_name = self.config('queue_name')


Then instantiate a ``RabbitMQComponent``, but with configuration in the ``rmq``
namespace::

    queue = RabbitMQComponent(config.with_namespace('rmq'))


In your environment, you would provide ``RMQ_HOST``, etc for this component.

You can auto-generate configuration documentation for this component in your
Sphinx docs by including the ``everett.sphinxext`` Sphinx extension and
using the ``autocomponent`` directive::

    .. autocomponent:: path.to.RabbitMQComponent


Say your app actually needs to connect to two separate queues--one for regular
processing and one for priority processing::

    regular_queue = RabbitMQComponent(
        config.with_namespace('regular').with_namespace('rmq')
    )
    priority_queue = RabbitMQComponent(
        config.with_namespace('priority').with_namespace('rmq')
    )


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
