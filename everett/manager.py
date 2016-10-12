# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""This module contains the configuration infrastructure allowing for deriving
configuration from specified sources in the order you specify.

"""

import importlib
import inspect
import os
import re
from functools import wraps

import six
from six.moves import configparser

from everett import NO_VALUE, ConfigurationError


# This is a stack of overrides to be examined in reverse order
_CONFIG_OVERRIDE = []
ENV_KEY_RE = re.compile(r'^[a-z][a-z0-9_]*$', flags=re.IGNORECASE)


def parse_bool(val):
    """Parses a bool

    Handles a series of values, but you should probably standardize on
    "true" and "false".

    >>> parse_bool('y')
    True
    >>> parse_bool('FALSE')
    False

    """
    true_vals = ('t', 'true', 'yes', 'y', '1', 'on')
    false_vals = ('f', 'false', 'no', 'n', '0', 'off')

    val = val.lower()
    if val in true_vals:
        return True
    if val in false_vals:
        return False

    raise ValueError('%s is not a valid bool value' % val)


def parse_env_file(envfile):
    """Parse the content of an iterable of lines as .env

    Return a dict of config variables.

    >>> parse_env_file(['DUDE=Abides'])
    {'DUDE': 'Abides'}

    """
    data = {}
    for line in envfile:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if '=' not in line:
            raise ConfigurationError('Env file line missing = operator')
        k, v = line.split('=', 1)
        k = k.strip()
        if not ENV_KEY_RE.match(k):
            raise ConfigurationError(
                'Invalid variable name %s in env file' % k
            )
        v = v.strip().strip('\'"')
        data[k] = v

    return data


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


def listify(thing):
    """Returns a new list of thing

    If thing is a string, then returns a list of thing. Otherwise
    returns thing.

    :arg thing: string or list of things

    :returns: list

    """
    if isinstance(thing, six.string_types):
        return [thing]
    return thing


def get_key_from_envs(envs, key, namespace=None):
    """Return the value of a key from the given dict respecting namespaces.

    Data can also be a list of data dicts.
    """
    # if it barks like a dict, make it a list
    # have to use `get` since dicts and lists
    # both have __getitem__
    if hasattr(envs, 'get'):
        envs = [envs]

    if namespace:
        namespace = listify(namespace)
        key = '_'.join(namespace + [key])

    key = key.upper()
    for env in envs:
        if key in env:
            return env[key]

    return NO_VALUE


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
        # Short-circuit to reduce overhead.
        if not _CONFIG_OVERRIDE:
            return NO_VALUE
        return get_key_from_envs(reversed(_CONFIG_OVERRIDE), key, namespace)


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

    Keys are not case sensitive. This also works::

            from everett.manager import ConfigDictEnv, ConfigManager

            config = ConfigManager([
                ConfigDictEnv({
                    'foo_bar': 'someval',
                    'bat': '1',
                })
            ])

            print config('foo_bar')
            print config('FOO_BAR')
            print config.with_namespace('foo')('bar')


    Also, ``ConfigManager`` has a convenience classmethod for creating a
    ``ConfigManager`` with just a dict environment::

            from everett.manager import ConfigManager

            config = ConfigManager.from_dict({
                'FOO_BAR': 'bat'
            })


    .. versionchanged:: 0.3
       Keys are no longer case-sensitive.

    """
    def __init__(self, cfg):
        self.cfg = dict(
            (key.upper(), val) for key, val in cfg.items()
        )

    def get(self, key, namespace=None):
        if namespace is not None:
            namespace = [part.upper() for part in namespace]
        return get_key_from_envs(self.cfg, key.upper(), namespace)


class ConfigEnvFileEnv(object):
    """Source for pulling configuration out of .env files

    This source lets you specify configuration in an .env file. This
    is useful for local development when in production you use values
    in environment variables.

    Keys are prefixed by namespaces and the whole thing is uppercased.

    For example, key "foo" will be ``FOO`` in the file.

    For example, namespace "bar" for key "foo" becomes ``BAR_FOO`` in the
    file.

    Key and namespace can consist of alphanumeric characters and ``_``.

    To use, instantiate and toss in the source list::

        from everett.manager import ConfigEnvFileEnv, ConfigManager

        config = ConfigManager([
            ConfigEnvFileEnv('.env')
        ])


    For multiple paths::

        from everett.manager import ConfigEnvFileEnv, ConfigManager

        config = ConfigManager([
            ConfigEnvFileEnv([
                '.env',
                'config/prod.env'
            ])
        ])


    Here's an example .env file::

        DEBUG=true

        # secrets
        SECRET_KEY=ou812

        # database setup
        DB_HOST=localhost
        DB_PORT=5432

    """
    data = None

    def __init__(self, possible_paths):
        possible_paths = listify(possible_paths)
        for path in possible_paths:
            if not path:
                continue

            path = os.path.abspath(os.path.expanduser(path.strip()))
            if path and os.path.isfile(path):
                with open(path) as envfile:
                    self.data = parse_env_file(envfile)
                    break

    def get(self, key, namespace=None):
        if not self.data:
            return NO_VALUE

        return get_key_from_envs(self.data, key, namespace)


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
    def get(self, key, namespace=None):
        return get_key_from_envs(os.environ, key, namespace)


class ConfigIniEnv(object):
    """Source for pulling configuration from INI files

    Takes a path or list of possible paths to look for the INI file and uses
    the first one it finds.

    If it finds no INI files in the possible paths, then this configuration
    source will be a no-op.

    This will expand ``~`` as well as work relative to the current working
    directory.

    This example looks just for the INI file specified in the environment::

        from everett.manager import ConfigIniEnv, ConfigManager

        config = ConfigManager([
            ConfigIniEnv(os.environ.get('FOO_INI'))
        ])


    If there's no ``FOO_INI`` in the environment, then the path will be
    ignored.

    Here's an example that looks for the INI file specified in the environment
    variable ``FOO_INI`` and failing that will look for ``.antenna.ini`` in the
    user's home directory::

        from everett.manager import ConfigIniEnv, ConfigManager

        config = ConfigManager([
            ConfigIniEnv([
                os.environ.get('FOO_INI'),
                '~/.antenna.ini'
            ])
        ])


    This example looks for a ``config/local.ini`` file which overrides values
    in a ``config/base.ini`` file both are relative to the current working
    directory::

        from everett.manager import ConfigIniEnv, ConfigManager

        config = ConfigManager([
            ConfigIniEnv('config/local.ini'),
            ConfigIniEnv('config/base.ini')
        ])


    Note how you can have multiple ``ConfigIniEnv`` files and this is how you
    can set Everett up to have values in one INI file override values in
    another INI file.

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
        possible_paths = listify(possible_paths)

        for path in possible_paths:
            if not path:
                continue

            path = os.path.abspath(os.path.expanduser(path.strip()))
            if path and os.path.isfile(path):
                # FIXME: log which path we used?
                self._parser = configparser.SafeConfigParser()
                self._parser.readfp(open(path, 'r'))
                break

    def get(self, key, namespace=None):
        # INI files always have a namespace which defaults to "main".
        namespace = listify(namespace) if namespace else ['main']
        namespace = '_'.join(namespace)

        if self._parser and self._parser.has_option(namespace, key):
            return self._parser.get(namespace, key)
        return NO_VALUE


class ConfigManagerBase(object):
    def get_namespace(self):
        """Retrieves the complete namespace for this config object

        :returns: namespace as a list of strings

        """
        return []

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

    def get_namespace(self):
        """Retrieves the complete namespace for this config object

        :returns: namespace as a list of strings

        """
        return self.config.get_namespace()

    def __call__(self, key, namespace=None, default=NO_VALUE,
                 alternate_keys=NO_VALUE, parser=str, raise_error=True):
        """Returns a config value bound to a component's options

        :arg key: the key to look up

        :arg namespace: the namespace for the key--different environments
            use this differently

        :arg default: IGNORED

        :arg alternate_keys: the list of alternate keys to look up;
            supports a ``root:`` key prefix which will cause this to look at
            the configuration root rather than the current namespace

            .. versionadded:: 0.3

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
            key,
            namespace=namespace,
            default=option.default,
            alternate_keys=option.alternate_keys,
            parser=option.parser,
            raise_error=raise_error
        )


class NamespacedConfig(ConfigManagerBase):
    """Applies a namespace to a config

    This restricts keys in a config to those belonging to the specified
    namespace.

    """
    def __init__(self, config, namespace):
        self.config = config
        self.namespace = namespace

    def get_namespace(self):
        """Retrieves the complete namespace for this config object

        :returns: namespace as a list of strings

        """
        return self.config.get_namespace() + [self.namespace]

    def __call__(self, key, namespace=None, default=NO_VALUE,
                 alternate_keys=NO_VALUE, parser=str, raise_error=True):
        """Returns a config value bound to a component's options

        :arg key: the key to look up

        :arg namespace: the namespace for the key--different environments
            use this differently

        :arg default: the default value (if any); must be a string that is
            parseable by the specified parser

        :arg alternate_keys: the list of alternate keys to look up;
            supports a ``root:`` key prefix which will cause this to look at
            the configuration root rather than the current namespace

            .. versionadded:: 0.3

        :arg parser: the parser for converting this value to a Python object

        :arg raise_error: True if you want a lack of value to raise a
            ``ConfigurationError``

        """
        new_namespace = [self.namespace]
        if namespace:
            new_namespace.extend(namespace)

        return self.config(
            key,
            namespace=new_namespace,
            default=default,
            alternate_keys=alternate_keys,
            parser=parser,
            raise_error=raise_error
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

    @classmethod
    def from_dict(cls, dict_config):
        """Creates a ConfigManager with specified configuration as a Python dict

        This is shorthand for::

            config = ConfigManager([ConfigDictEnv(dict_config)])


        This is handy for writing tests for the app you're using Everett in.

        :arg dict_config: Python dict holding the configuration for this
            manager

        :returns: ConfigManager with specified configuration

        .. versionadded:: 0.3

        """
        return ConfigManager([ConfigDictEnv(dict_config)])

    def __call__(self, key, namespace=None, default=NO_VALUE,
                 alternate_keys=NO_VALUE, parser=str, raise_error=True):
        """Returns a parsed value from the environment

        :arg key: the key to look up

        :arg namespace: the namespace for the key--different environments
            use this differently

        :arg default: the default value (if any); must be a string that is
            parseable by the specified parser; if no default is provided, this
            will raise an error or return ``everett.NO_VALUE`` depending on
            the value of ``raise_error``

        :arg alternate_keys: the list of alternate keys to look up;
            supports a ``root:`` key prefix which will cause this to look at
            the configuration root rather than the current namespace

            .. versionadded:: 0.3

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

            # Use alternate_keys for backwards compatibility with an
            # older version of this software
            PASSWORD = config('PASSWORD', alternate_keys=['SECRET'])


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

        # Go through all possible keys
        all_keys = [key]
        if alternate_keys is not NO_VALUE:
            all_keys = all_keys + alternate_keys

        for possible_key in all_keys:
            if possible_key.startswith('root:'):
                # If this is a root-anchored key, we drop the namespace.
                possible_key = possible_key[5:]
                use_namespace = None
            else:
                use_namespace = namespace

            # Go through environments in reverse order
            for env in self.envs:
                val = env.get(possible_key, use_namespace)

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

        # Otherwise return NO_VALUE
        return NO_VALUE


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
