# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""This module contains the configuration infrastructure allowing for deriving
configuration from specified sources in the order you specify.

"""

import importlib
import inspect
import os
from functools import wraps

import six
from six.moves import configparser

from everett import NO_VALUE, ConfigurationError


# This is a stack of overrides to be examined in reverse order
_CONFIG_OVERRIDE = []


def parse_bool(val):
    """Parses a bool

    Handles a series of values, but you should probably standardize on
    "true" and "false".

    >>> parse_bool('y')
    True
    >>> parse_bool('FALSE')
    False

    """
    true_vals = ('t', 'true', 'yes', 'y', '1')
    false_vals = ('f', 'false', 'no', 'n', '0')

    val = val.lower()
    if val in true_vals:
        return True
    if val in false_vals:
        return False

    raise ValueError('%s is not a valid bool value' % val)


def parse_class(val):
    """Parses a string, imports the module and returns the class

    >>> parse_class('hashlib.md5')

    """
    module, class_name = val.rsplit('.', 1)
    module = importlib.import_module(module)
    try:
        return getattr(module, class_name)
    except AttributeError:
        raise ValueError('%s is not a valid member of %s' % (
            class_name, module)
        )


def get_parser(parser):
    """Returns a parsing function for a given parser"""
    # Special case bool so that we can explicitly give bool values otherwise
    # all values would be True since they're non-empty strings.
    if parser is bool:
        return parse_bool
    return parser


class ListOf(object):
    """Parses a comma-separated list of things

    >>> ListOf(str)('a,b,c,d')
    ['a', 'b', 'c', 'd']
    >>> ListOf(int)('1,2,3,4')
    [1, 2, 3, 4]

    Note: This doesn't handle quotes or backslashes or any complicated string
    parsing.

    For example:

    >>> ListOf(str)('"a,b",c,d')
    ['"a', 'b"', 'c', 'd']

    """
    def __init__(self, parser, delimiter=','):
        self.sub_parser = parser
        self.delimiter = delimiter

    def __call__(self, value):
        parser = get_parser(self.sub_parser)
        return [parser(token) for token in value.split(self.delimiter)]


class ConfigOverrideEnv(object):
    """Override configuration layer for testing"""
    def get(self, key, namespace=None):
        if namespace:
            key = list(namespace) + [key]
            key = '_'.join(key)

        key = key.upper()

        for env in reversed(_CONFIG_OVERRIDE):
            if key in env:
                return env[key]
        return NO_VALUE


class ConfigDictEnv(object):
    """Source for pulling configuration out of a dict

    This is handy for testing. You might also use it if you wanted to move all
    your defaults values into one centralized place.

    Namespace is prefixed, so key "foo" in namespace "bar" is ``FOO_BAR``.

        For example::

            from everett.manager import ConfigDictEnv, ConfigManager

            config = ConfigManager([
                ConfigDictEnv({
                    'FOO_BAR': 'someval',
                    'BAT': '1',
                })
            ])

    """
    def __init__(self, cfg):
        self.cfg = cfg

    def get(self, key, namespace=None):
        if namespace:
            key = list(namespace) + [key]
            key = '_'.join(key)

        key = key.upper()

        if key in self.cfg:
            return self.cfg[key]
        return NO_VALUE


class ConfigOSEnv(object):
    """Source for pulling configuration out of the environment

    This source lets you specify configuration in the environment. This is
    useful for infrastructure related configuration like usernames and ports
    and secret configuration like passwords.

    Keys are prefixed by namespaces and the whole thing is uppercased.

    For example, key "foo" will be ``FOO`` in the environment.

    For example, namespace "bar" for key "foo" becomes ``BAR_FOO`` in the
    environment.

    Key and namespace can consist of alphanumeric characters and ``_``.

    To use, instantiate and toss in the source list::

        from everett.manager import ConfigOSEnv, ConfigManager

        config = ConfigManager([
            ConfigOSEnv()
        ])

    """
    def get(self, key, namespace=[]):
        if namespace:
            key = list(namespace) + [key]
            key = '_'.join(key)

        key = key.upper()
        if key in os.environ:
            return os.environ[key]

        return NO_VALUE


class ConfigIniEnv(object):
    """Source for pulling configuration from INI files

    Takes a list of ``possible_paths`` to look for the INI file and uses the
    first one it finds.

    If it finds no INI files in the possible paths, then this configuration
    source will be a no-op.

    This will expand ``~`` and work relative to the current working directory.

    Here's an example that looks for a filename specified in the environment
    variable ``FOO_INI`` and then the ``.antenna.ini`` in the user's home
    directory::

        from everett.manager import ConfigIniEnv, ConfigManager

        config = ConfigManager([
            ConfigIniEnv([
                os.environ.get('FOO_INI'),
                '~/.antenna.ini'
            ])
        ])


    In this example, if there is no ``FOO_INI`` specified in the environment,
    then that path will be ignored.

    INI files must have a "main" section. This is where keys that aren't in a
    namespace are placed.

    Minimal INI file::

        [main]


    In the INI file, namespace is a section. So "user" in namespace "foo" is::

        [foo]
        user=someval


    Everett doesn't support multi-tiered hierarchies, so a key in a
    namespace in another namespace is a key in a section formed by
    concatenating all the namespaces. For example, the key "user" in namespace
    "foo" which is in namespace "bar" ends up like this::

        [bar_foo]
        user=someval

    """
    def __init__(self, possible_paths):
        self._parser = None
        for path in possible_paths:
            if not path:
                continue

            path = os.path.abspath(os.path.expanduser(path.strip()))
            if path and os.path.exists(path) and os.path.isfile(path):
                # FIXME: log which path we used?
                self._parser = configparser.SafeConfigParser()
                self._parser.readfp(open(path, 'r'))
                break

    def get(self, key, namespace=None):
        if not namespace:
            namespace = 'main'
        else:
            namespace = '_'.join(namespace)

        if self._parser and self._parser.has_option(namespace, key):
            return self._parser.get(namespace, key)
        return NO_VALUE


class ConfigManagerBase(object):
    def with_options(self, component):
        options = component.get_required_config()
        return BoundConfig(self, options)

    def with_namespace(self, namespace):
        return NamespacedConfig(self, namespace)


class BoundConfig(ConfigManagerBase):
    """Wraps a config and binds it to a set of options

    This restricts the config to only return keys from the option set. Further,
    it uses the option set to determine the default and the parser for that
    option.

    This is useful for binding configuration to a component's specified
    options.

    """
    def __init__(self, config, options):
        self.config = config
        self.options = options

    def __call__(self, key, namespace=None, default=NO_VALUE, parser=str,
                 raise_error=True):
        """Returns a config value bound to a component's options

        :arg key: the key to look up
        :arg namespace: the namespace for the key--different environments
            use this differently
        :arg default: IGNORED
        :arg parser: IGNORED
        :arg raise_error: True if you want a lack of value to raise a
            ``ConfigurationError``

        """
        try:
            option = self.options[key]
        except KeyError:
            if raise_error:
                raise ConfigurationError(
                    '%s is not a valid key for this component' % (key,)
                )
            return None

        return self.config(
            key, namespace, default=option.default,
            parser=option.parser, raise_error=raise_error
        )


class NamespacedConfig(ConfigManagerBase):
    """Applies a namespace to a config

    This restricts keys in a config to those belonging to the specified
    namespace.

    """
    def __init__(self, config, namespace):
        self.config = config
        self.namespace = namespace

    def __call__(self, key, namespace=None, default=NO_VALUE, parser=str,
                 raise_error=True):
        """Returns a config value bound to a component's options

        :arg key: the key to look up
        :arg namespace: the namespace for the key--different environments
            use this differently
        :arg default: the default value (if any); must be a string that is
            parseable by the specified parser
        :arg parser: the parser for converting this value to a Python object
        :arg raise_error: True if you want a lack of value to raise a
            ``ConfigurationError``

        """
        new_namespace = [self.namespace]
        if namespace:
            new_namespace.extend(namespace)

        return self.config(
            key, new_namespace, default, parser, raise_error
        )


class ConfigManager(ConfigManagerBase):
    """Manages multiple configuration environment layers"""

    def __init__(self, environments, with_override=True):
        """Instantiates a ConfigManager

        :arg environents: list of configuration sources to look through in
            the order they should be looked through
        :arg with_override: whether or not to insert the special override
            environment used for testing as the first environment in the list
            of sources

        """
        if with_override:
            environments.insert(0, ConfigOverrideEnv())

        self.envs = environments

    def __call__(self, key, namespace=None, default=NO_VALUE, parser=str,
                 raise_error=True):
        """Returns a parsed value from the environment

        :arg key: the key to look up
        :arg namespace: the namespace for the key--different environments
            use this differently
        :arg default: the default value (if any); must be a string that is
            parseable by the specified parser; if no default is provided, this
            will return ``everett.NO_VALUE``
        :arg parser: the parser for converting this value to a Python object
        :arg raise_error: True if you want a lack of value to raise a
            ``everett.ConfigurationError``

        Examples::

            config = ConfigManager([])

            # Use the special bool parser
            DEBUG = config('DEBUG', default='True', parser=bool)

            # Use the list of parser
            from everett.manager import ListOf
            ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost',
                                   parser=ListOf(str))


        The default value should always be a string that is parseable by the
        parser. This simplifies some things because then default values are
        **always** strings and parseable by parsers. It's not the case that in
        some places they're strings and some places they're parsed values.

        The parser can be any callable that takes a string value and returns a
        parsed value.

        """
        if not (default is NO_VALUE or isinstance(default, six.string_types)):
            raise ConfigurationError(
                'default value %r is not a string' % (default,)
            )

        parser = get_parser(parser)

        # Go through environments in reverse order
        for env in self.envs:
            val = env.get(key, namespace)
            if val is not NO_VALUE:
                return parser(val)

        # Return the default if there is one
        if default is not NO_VALUE:
            return parser(default)

        # No value specified and no default, so raise an error to the user
        if raise_error:
            raise ConfigurationError(
                '%s (%s) requires a value parseable by %s' % (
                    key, namespace, parser)
            )

        # Otherwise return None
        return


class ConfigOverride(object):
    """Allows you to override config for writing tests

    This can be used as a class decorator::

        @config_override(FOO='bar', BAZ='bat')
        class FooTestClass(object):
            ...


    This can be used as a function decorator::

        @config_override(FOO='bar')
        def test_foo():
            ...


    This can also be used as a context manager::

        def test_foo():
            with config_override(FOO='bar'):
                ...

    """
    def __init__(self, **cfg):
        self._cfg = cfg

    def push_config(self):
        """Pushes self._cfg as a config layer onto the stack"""
        _CONFIG_OVERRIDE.append(self._cfg)

    def pop_config(self):
        """Pops a config layer off

        :raises IndexError: If there are no layers to pop off

        """
        _CONFIG_OVERRIDE.pop()

    def __enter__(self):
        self.push_config()

    def __exit__(self, exc_type, exc_value, traceback):
        self.pop_config()

    def decorate(self, fun):
        @wraps(fun)
        def _decorated(*args, **kwargs):
            # Push the config, run the function and pop it afterwards.
            self.push_config()
            try:
                return fun(*args, **kwargs)
            finally:
                self.pop_config()
        return _decorated

    def __call__(self, class_or_fun):
        if inspect.isclass(class_or_fun):
            # If class_or_fun is a class, decorate all of its methods
            # that start with 'test'.
            for attr in class_or_fun.__dict__.keys():
                prop = getattr(class_or_fun, attr)
                if attr.startswith('test') and callable(prop):
                    setattr(class_or_fun, attr, self.decorate(prop))
            return class_or_fun

        else:
            return self.decorate(class_or_fun)


# This gives it a better name
config_override = ConfigOverride
