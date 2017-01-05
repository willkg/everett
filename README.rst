=======
Everett
=======

Everett is a configuration library.

:Code:          https://github.com/willkg/everett
:Issues:        https://github.com/willkg/everett/issues
:License:       MPL v2
:Documentation: https://everett.readthedocs.io/


Goals
=====

This library tries to do configuration with minimal "fanciness":

Configuration with Everett:

* is composeable and flexible
* makes it easier to provide helpful error messages for users trying to
  configure your software
* can pull configuration from a variety of specified sources (environment, ini
  files, dict, write-your-own)
* supports parsing values (bool, int, lists, ..., write-your-own)
* supports key namespaces
* facilitates writing tests that change configuration values
* supports component architectures with auto-documentation of configuration with
  a Sphinx ``autoconfig`` directive

Everett is inspired by `python-decouple
<https://github.com/henriquebastos/python-decouple>`_ and `configman
<https://configman.readthedocs.io/en/latest/>`_.


Why not other libs?
===================

Most other libraries I looked at had one or more of the following issues:

* were tied to a specific web app framework
* didn't allow you to specify configuration sources
* provided poor error messages when you configure things wrong
* had a global configuration object
* made it really hard to override specific configuration when writing tests
* had no facilities for auto-documenting configuration for components


Quick start
===========

Say you're writing a web app using some framework that doesn't provide
infrastructure for configuration.

You want to pull configuration from an INI file stored in a place specified by
``FOO_INI`` in the environment. You want to pull infrastructure values from the
environment. Values from the environment should override values from the INI
file.

First, you set up your ``ConfigManager`` in your webapp::

    from everett.manager import ConfigManager, ConfigOSEnv, ConfigIniEnv


    class MyWSGIApp(SomeFrameworkApp):
        def __init__(self):
            self.config = ConfigManager(
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
                doc='Check https://example.com/configuration for docs'
            )

            # Set ``is_debug`` based on configuration
            self.is_debug = self.config('debug', parser=bool)


    def get_app():
        return MyWSGIApp()


Now all configuration for the app can be pulled from the ``.config`` property.

Let's write some tests that verify behavior based on the ``debug`` configuration
value::

    from everett.manager import config_override

    @config_override(DEBUG='true')
    def test_debug_true():
        app = get_app()
        ...

    @config_override(DEBUG='false')
    def test_debug_false():
        app = get_app()
        ...


This works with frameworks that do have configuration infrastructure like
Django and Flask.

This works with non-web things, too, like command line programs.

Everett supports components, too. Say your app needs to connect to RabbitMQ.
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

You can auto-document the configuration for this component in your Sphinx docs
with::

    .. autoconfig:: path.to.RabbitMQComponent


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

From PyPI
---------

Run::

    $ pip install everett


For hacking
-----------

Run::

    # Clone the repository
    $ git clone https://github.com/willkg/everett

    # Create a virtualenvironment
    ...

    # Install Everett and dev requirements
    $ pip install -r requirements-dev.txt
