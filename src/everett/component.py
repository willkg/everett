# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Module holding infrastructure for building components."""

from collections import OrderedDict
from collections.abc import Mapping
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)

from everett import EverettComponent, NO_VALUE, NoValue
from everett.manager import BoundConfig


class Option:
    """A single option comprised of a key and settings."""

    def __init__(
        self,
        key: str,
        default: Union[str, NoValue] = NO_VALUE,
        alternate_keys: Optional[List[str]] = None,
        doc: str = "",
        parser: Callable = str,
        meta: Any = None,
    ):
        self.key = key
        self.default = default
        self.alternate_keys = alternate_keys
        self.doc = doc
        self.parser = parser
        self.meta = meta or {}

    def __eq__(self, obj: Any) -> bool:
        return (
            isinstance(obj, Option)
            and obj.key == self.key
            and obj.default == self.default
            and obj.alternate_keys == self.alternate_keys
            and obj.doc == self.doc
            and obj.parser == self.parser
            and obj.meta == self.meta
        )


class ConfigOptions(Mapping):
    """A mapping of config options."""

    def __init__(self) -> None:
        self.options: Dict = OrderedDict()

    def add_option(
        self,
        key: str,
        default: Union[str, NoValue] = NO_VALUE,
        alternate_keys: Optional[List[str]] = None,
        doc: str = "",
        parser: Callable = str,
        **meta: Any,
    ) -> None:
        """Add an option to the group.

        :arg key: the key to look up

        :arg default: the default value (if any); must be a string that is
            parseable by the specified parser

        :arg alternate_keys: the list of alternate keys to look up;
            supports a ``root:`` key prefix which will cause this to look at
            the configuration root rather than the current namespace

        :arg doc: documentation for this config option

        :arg parser: the parser for converting this value to a Python object

        :arg meta: catch-all for other key/value pairs you want to association
            with this option

        """
        option = Option(
            key=key,
            default=default,
            alternate_keys=alternate_keys,
            doc=doc,
            parser=parser,
            meta=meta,
        )
        self.options[key] = option

    def update(self, new_options: List[Option]) -> None:
        """Update this ConfigOptions using data from another."""
        for option in new_options:
            if option.key in self.options:
                del self.options[option.key]
            self.options[option.key] = option

    def __iter__(self) -> Iterator[Option]:
        return iter(self.options.values())

    def __getitem__(self, key: str) -> Option:
        return self.options.__getitem__(key)

    def __len__(self) -> int:
        return len(self.options)


class RequiredConfigMixin(EverettComponent):
    """Mixin for component classes that have required configuration.

    As with all mixins, make sure this is earlier in the class list.

    Example::

        from everett.component import RequiredConfigMixin, ConfigOptions

        class SomeComponent(RequiredConfigMixin):
            required_config = ConfigOptions()
            required_config.add_option('foo')

            def __init__(self, config):
                self.config = config.with_options(self)

    .. Note::

       The class member must be named ``required_config``. If you want to use a
       different name, you need to implement your own ``get_required_config``.

    """

    @classmethod
    def get_required_config(cls) -> ConfigOptions:
        """Roll up configuration options for this class and parent classes.

        This handles subclasses overriding options in parent classes.

        :returns: final ``ConfigOptions`` representing all configuration for
            this class

        """
        options = ConfigOptions()
        for cls in reversed(cls.__mro__):
            if hasattr(cls, "required_config"):
                options.update(getattr(cls, "required_config"))
        return options

    def get_runtime_config(
        self, namespace: Union[List[str], None] = None
    ) -> Generator[Tuple[Union[List[str], None], str, Any, Option], None, None]:
        """Roll up the runtime config for this class and all children.

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
           compute the runtime config including the current value for that
           configuration option.

           Otherwise, it'll yield nothing.

        :arg list namespace: list of namespace parts or None

        :returns: list of ``(namespace, key, value, option)``

        """
        cfg = getattr(self, "config", None)
        if cfg is None or not isinstance(cfg, BoundConfig):
            return

        namespace = namespace or cfg.get_namespace()

        for opt in self.get_required_config():
            yield (
                namespace,
                opt.key,
                cfg(opt.key, raise_error=False, raw_value=True),
                opt,
            )
