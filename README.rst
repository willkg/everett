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

This library tries to do configuration with minimal "fanciness".

Configuration with Everett:

* is composeable and flexible
* makes it easier to provide helpful error messages for users trying to
  configure your software
* supports auto-documentation of configuration with a Sphinx
  ``autocomponent`` directive
* supports easy testing with configuration override
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

Example
-------

We have an app and want to pull configuration from an INI file stored in
a place specified by ``MYAPP_INI`` in the environment, ``~/.myapp.ini``,
or ``/etc/myapp.ini`` in that order.

We want to pull infrastructure values from the environment.

Values from the environment should override values from the INI file.

First, we set up our ``ConfigManager``::

    import os
    import sys

    from everett.manager import ConfigManager, ConfigOSEnv, ConfigIniEnv


    def get_config():
        return ConfigManager(
            # Specify one or more configuration environments in
            # the order they should be checked
            [
                # Looks in OS environment first
                ConfigOSEnv(),

                # Looks in INI files in order specified
                ConfigIniEnv([
                    os.environ.get('MYAPP_INI'),
                    '~/.myapp.ini',
                    '/etc/myapp.ini'
                ]),
            ],

            # Make it easy for users to find your configuration
            # docs
            doc='Check https://example.com/configuration for docs.'
        )

Then we use it::

    def is_debug(config):
        return config('debug', parser=bool,
            doc='Switch debug mode on and off.')


    def main(args):
        config = get_config()

        if is_debug(config):
            print('DEBUG MODE ON!')


    if __name__ == '__main__':
        sys.exit(main(sys.argv[1:]))


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


What can you use Everett with
-----------------------------

Everett works with frameworks that have configuration infrastructure like
Django and Flask.

Everett works with non-web things like scripts and servers and other things.


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


Install for hacking
-------------------

Run::

    # Clone the repository
    $ git clone https://github.com/willkg/everett

    # Create a virtualenvironment
    ...

    # Install Everett and dev requirements
    $ pip install -r requirements-dev.txt
