==========
Components
==========

.. contents::


.. versionchanged:: 2.0

   This is redone for v2.0.0 and simplified.


Building components with Everett
================================

Everett allows you to build components that specify the configuration options
for that component.

This lets you do three things:

1. instantiate components in a specified configuration namespace
2. restrict the configuration the component uses to that specified in the
   component
3. inherit and override configuration from superclasses

To create a component, add a ``Config`` class to the class definition. In
the ``Config`` class, specify the options for that class.

For example, let's create a RabbitMQComponent for accessing RabbitMQ::

    from everett.manager import Option

    class RabbitMQComponent:
        class Config:
            host = Option(doc="RabbitMQ host to connect to")
            port = Option(default="5672", doc="Port to use", parser=int)
            queue_name = Option(doc="Queue to insert things into")

        def __init__(self, config):
            # Bind the configuration manager to just the options
            # specified by this component. If this configuration manager
            # is asked to return a configuration option that's not
            # specified by # this class, then it'll throw an error.
            self.config = config.with_options(self)
            ...


We also need an ``__init__`` method that takes the ``config`` as an argument so
that you can bind the component's config options with the config using
``.with_options()``.

Then in our app, we could instantiate a ``RabbitMQComponent`` using an ``rmq``
configuration namespace like this::

    rmq = RabbitMQComponent(config.with_namespace('rmq'))

In our environment, we would provide a ``RMQ_HOST`` variable for this
component.

Say our app needs to connect to two separate queues--one for regular processing
and one for priority processing::

    rmq_regular = RabbitMQComponent(config.with_namespace("rmq_regular"))
    rmq_priority = RabbitMQComponent(config.with_namespace("rmq_priority"))

In our environment, we provide the host for the regular queue configuration
with ``RMQ_REGULAR_HOST`` and the the host for the priority queue configuration
with ``RMQ_PRIORITY_HOST``.

Same component code--two different instances with two different configurations.


Subclassing
===========

You can subclass components and override configuration options.

For example::

    from everett.manager import ConfigManager, Option

    class ComponentA:
        class Config:
            foo = Option(default="foo_from_a")
            bar = Option(default="bar_from_a")

    class ComponentB(ComponentA):
        class Config:
            foo = Option(default="foo_from_b")

        def __init__(self, config):
            self.config = config.with_options(self)

    config = ConfigManager.basic_config()
    compb = ComponentB(config)

    print(compb.config("foo"))  # prints "foo_from_b"
    print(compb.config("bar"))  # prints "bar_from_a"


Getting configuration information for components
================================================

You can get the configuration options for a component class using
:py:func:`everett.manager.get_config_for_class`. This returns a dict of
``configuration key -> (option, class)``. This helps with debugging which
option came from which class.

.. autofunction:: everett.manager.get_config_for_class
   :noindex:


You can get the runtime configuration for a component or tree of components
using :py:func:`everett.manager.get_runtime_config`. This returns a list of
``(namespace, key, value, option, class)`` tuples. The value is the computed
runtime value taking into account the environments specified in the
``ConfigManager`` and class hierarchies.

It'll traverse any instance attributes that are components with options.

.. autofunction:: everett.manager.get_runtime_config
   :noindex:
