# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Module holding component parts.

A component can define the configuration it requires. This is handy in a couple
of ways:

1. components are self-documenting so documentation for a component can be
   extracted and automatically generated and users don't have to hunt for it

2. components can be subclassed and behavior and configuration can be
   overridden which makes it easier to have families of components that solve a
   common problem

3. components are instantiated and named allowing them namespaced configuration
   which lets you have two instances of the same component and be able to
   differentiate that in configuration


To create a component, you want to use the ``RequiredConfigMixin``::

    class SomeComponent(RequiredConfigMixin):

        required_config = ConfigOptions()
        required_config.add_option(
            'is_hardcore',
            doc='is this component hardcore or not?',
            default=False,
            parser=bool
        )

        def __init__(self, config, ...):
            self.config = config.with_options(self)

        def some_method(self):
            username = self.config('username')
            password = self.config('password', raise_error=False)

            connection = self.connect(username, password)


``ConfigOptions`` groups a set of configuration options that this component
requires. Options of subclasses override those of superclasses (assuming you
ever want to do that).

You also need an ``__init__`` method that takes the ``config`` as the first
argument. You need to bind the component's config options to the config using
``.with_options()``::

    self.config = config.with_options(self)


The code that instantiates the component probably wants to apply a namespace to
the configuration. You can apply one or more namespaces to the config using
``.with_namespace()``. For example::

    config = config.with_namespace('foo')


This yields a config that returns keys in the foo namespace. An example
environment variable might be ``FOO_USER`` which is the ``user`` key in the
``foo`` namespace.

Namespaces can stack where the outermost namespace is the one specified last.
For example::

    config = (config
              .with_namespace('foo')
              .with_namespace('bar'))


This yields a config that returns keys in the foo namespace which is in the bar
namespace. An example environment variable might be ``BAR_FOO_USER`` which is
the ``user`` key in the ``foo`` namespace in the ``bar`` namespace.

"""

from configmanlite import NO_VALUE, ConfigurationError


class ClassifiedConfigManager(object):
    def __init__(self, options, config_manager, namespace=None):
        self.options = options
        self.config_manager = config_manager
        if namespace:
            namespace = '_'.join(namespace)
        self.namespace = namespace

    def __call__(self, key, raise_error=True):
        try:
            option = self.options[key]
        except KeyError:
            if raise_error:
                raise ConfigurationError(
                    '%s is not a valid key for this component' % (key,)
                )
            return None

        return self.config_manager(
            key, self.namespace, default=option.default,
            parser=option.parser, raise_error=raise_error
        )


def create_instance(cls, config, namespace=None, **kwargs):
    # Generate a ``ClassifiedConfigManager`` which takes a namespace (if there
    # is one) and a ``ConfigOptions`` and applies that to a ``ConfigManager``
    # so we're calling ``config()`` correctly.
    classifiedcm = ClassifiedConfigManager(cls, config, namespace)

    # Create the instance passing in the ``ClassifiedConfigManager`` instance
    # and kwargs.
    instance = cls(classifiedcm, **kwargs)

    return instance


class Option(object):
    def __init__(self, key, default, parser, raise_error):
        self.key = key
        self.default = default
        self.parser = parser
        self.raise_error = raise_error


class ConfigOptions(object):
    def __init__(self):
        self.options = []
        self.option_lookkup = {}

    def add_option(self, key, default=NO_VALUE, doc='', parser=str,
                   raise_error=True):
        option = Option(key, default, doc, parser, raise_error)
        self._add_option(option)

    def _add_option(self, option):
        self.options.append(option)
        self.option_lookup[option.key] = option

    def update(self, class_config):
        for option in class_config.option_lookup.values():
            self._add_option(option)

    def __getitem__(self, key):
        return self.option_lookup[key]


class RequiredConfigMixin(object):
    @classmethod
    def get_required_config(cls):
        """Rolls up the configuration for class and parent classes

        :returns: final ConfigOptions representing all configuration for this
            class

        """
        options = ConfigOptions()
        for cls in reversed(cls.__mro__):
            try:
                options.update(cls.required_config)
            except AttributeError:
                pass
        return options
