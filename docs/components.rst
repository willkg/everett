==========
Components
==========

.. contents::


Building components with Everett
================================

Everett allows you to build components that specify their own configuration as a
class property.

This lets you do three things:

1. instantiate components in a specified configuration namespace
2. restrict the configuration the component uses to that specified in the
   component
3. inherit and override configuration from superclasses

To create a component, you want to use the
``everett.component.RequiredConfigMixin``.

For example, let's create a RabbitMQComponent for accessing RabbitMQ::

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
            ...


``ConfigOptions`` groups a set of configuration options that this component
requires. Options of subclasses override those of superclasses.

We also need an ``__init__`` method that takes the ``config`` as an argument so
that you can bind the component's config options with the config using
``.with_options()``.

Then in our app, we instantiate a RabbitMQComponent, but with configuration in
the rmq namespace::

    queue = RabbitMQComponent(config.with_namespace('rmq'))

In our environment, we would provide ``RMQ_HOST``, etc for this component.

Say our app actually needs to connect to two separate queues–one for regular
processing and one for priority processing::

    regular_queue = RabbitMQComponent(
        config.with_namespace('regular').with_namespace('rmq')
    )
    priority_queue = RabbitMQComponent(
        config.with_namespace('priority').with_namespace('rmq')
    )

In our environment, we provide the regular queue configuration with
``RMQ_REGULAR_HOST``, etc and the priority queue configuration with
``RMQ_PRIORITY_HOST``, etc.

Same component code–two different instances.


Documenting components
======================

Components can have configuration. It's important to be able to easily document
this configuration.

As such, everett includes a Sphinx extension that adds a ``autoconfig``
declaration for auto-documenting configuration for components.

.. automodule:: everett.sphinx_autoconfig
