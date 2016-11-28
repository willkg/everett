# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Module holding infrastructure for building components.

"""

from collections import OrderedDict

from everett import NO_VALUE
from everett.manager import BoundConfig


class Option(object):
    def __init__(self, key, default=NO_VALUE, alternate_keys=NO_VALUE, doc='', parser=str):
        self.key = key
        self.default = default
        self.alternate_keys = alternate_keys
        self.doc = doc
        self.parser = parser

    def __eq__(self, obj):
        return (
            isinstance(obj, Option) and
            obj.key == self.key and
            obj.default == self.default and
            obj.alternate_keys == self.alternate_keys and
            obj.doc == self.doc and
            obj.parser == self.parser
        )


class ConfigOptions(object):
    """Class for holding a collection of config options"""
    def __init__(self):
        self.options = OrderedDict()

    def add_option(self, key, default=NO_VALUE, alternate_keys=NO_VALUE,
                   doc='', parser=str):
        """Adds an option to the group

        :arg key: the key to look up

        :arg default: the default value (if any); must be a string that is
            parseable by the specified parser

        :arg alternate_keys: the list of alternate keys to look up;
            supports a ``root:`` key prefix which will cause this to look at
            the configuration root rather than the current namespace

        :arg doc: documentation for this config option

        :arg parser: the parser for converting this value to a Python object

        """
        option = Option(key, default, alternate_keys, doc, parser)
        self.options[key] = option

    def update(self, new_options):
        for option in new_options:
            if option.key in self.options:
                del self.options[option.key]
            self.options[option.key] = option

    def __iter__(self):
        return iter(self.options.values())

    def __getitem__(self, key):
        return self.options.__getitem__(key)


class RequiredConfigMixin(object):
    """Mixin for component classes that have required configuration

    As with all mixins, make sure this is earlier in the class list.

    Example::

        from everett.component import RequiredConfigMixin, ConfigOptions

        class SomeComponent(RequiredConfigMixin):
            required_config = ConfigOptions()
            required_config.add_option('foo')

            def __init__(self, config):
                self.config = config.with_options(self)

    """
    @classmethod
    def get_required_config(cls):
        """Rolls up the configuration for class and parent classes

        :returns: final ``ConfigOptions`` representing all configuration for
            this class

        """
        options = ConfigOptions()
        for cls in reversed(cls.__mro__):
            try:
                options.update(cls.required_config)
            except AttributeError:
                pass
        return options

    def get_runtime_config(self, namespace=None):
        """Roll up the runtime config for this class and all children

        Implement this to call ``.get_runtime_config()`` on child components or
        to adjust how it works.

        For example, if you created a component that has a child component, you
        could do something like this::

            class MyComponent(RequiredConfigMixin):
                ....

                def __init__(self, config):
                    self.config = config.with_options(self)
                    self.child = OtherComponent(config.with_namespace('source'))

                def get_runtime_config(self, namespace=None):
                    for item in super(MyComponent, self).get_runtime_config(namespace):
                        yield item
                    for item in self.child.get_runtime_config(['source']):
                        yield item


        Calling this function can give you the complete runtime configuration
        for a component tree. This is helpful for doing things like printing
        the configuration being used including default values.

        .. Note::

           If this instance has a ``.config`` attribute and it is a
           :py:class:`everett.component.BoundConfig`, then this will try to
           compute the runtime config.

           Otherwise, it'll yield nothing.

        :arg list namespace: list of namespace parts or None

        :returns: list of ``(namespace, key, option)``

        """
        namespace = namespace or []

        cfg = getattr(self, 'config', None)
        if cfg is None or not isinstance(cfg, BoundConfig):
            return

        for key, opt in self.get_required_config().options.items():
            yield (namespace, key, self.config(key, raise_error=False, raw_value=True), opt)
