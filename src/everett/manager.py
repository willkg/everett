# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Contains configuration infrastructure.

This module contains the configuration classes and functions for deriving
configuration values from specified sources in the order specified.

"""

from functools import wraps
import importlib
import inspect
import logging
import os
import re
import sys
from types import TracebackType
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
    Type,
    Union,
)

from everett import (
    ConfigurationError,
    ConfigurationMissingError,
    InvalidValueError,
    InvalidKeyError,
    NO_VALUE,
    NoValue,
)


__all__ = [
    "ConfigDictEnv",
    "ConfigEnvFileEnv",
    "ConfigManager",
    "ConfigOSEnv",
    "ConfigObjEnv",
    "ListOf",
    "Option",
    "config_override",
    "get_config_for_class",
    "get_runtime_config",
    "parse_bool",
    "parse_class",
    "parse_data_size",
    "parse_time_period",
    "parse_env_file",
]


# Regex for valid keys in an env file
ENV_KEY_RE = re.compile(r"^[a-z][a-z0-9_]*$", flags=re.IGNORECASE)

logger = logging.getLogger("everett")


def qualname(thing: Any) -> str:
    """Return the Python dotted name for a given thing.

    >>> import everett.manager
    >>> qualname(str)
    'str'
    >>> qualname(everett.manager.parse_class)
    'everett.manager.parse_class'
    >>> qualname(everett.manager)
    'everett.manager'

    :param thing: the thing to get the qualname from

    :returns: the Python dotted name

    """
    parts = []

    # Add the module, unless it's a builtin
    mod = inspect.getmodule(thing)
    if mod and mod.__name__ not in ("__main__", "__builtin__", "builtins"):
        parts.append(mod.__name__)

    if hasattr(thing, "__qualname__"):
        parts.append(thing.__qualname__)
        return ".".join(parts)

    # If it's a module
    if inspect.ismodule(thing):
        return ".".join(parts)

    # It's an instance, so ... let's call repr on it
    return repr(thing)


def build_msg(
    namespace: Optional[List[str]],
    key: Optional[str],
    parser: Optional[Callable],
    msg: str = "",
    option_doc: str = "",
    config_doc: str = "",
) -> str:
    """Builds a message for a configuration error exception

    :param namespace: list of strings that represent the configuration variable namespace or ``None``
    :param key: the configuration variable key or ``None``
    :param parser: the parser that will be used to parse the value for this configuration variable or ``None``
    :param msg: the error message
    :param option_doc: the configuration option documentation
    :param config_doc: the ConfigManager documentation

    :returns: the error message string

    """
    text = [msg]
    if key and parser:
        full_key = generate_uppercase_key(key, namespace)
        text.append(f"{full_key} requires a value parseable by {qualname(parser)}")
    else:
        full_key = None
    if option_doc and full_key:
        text.append(f"{full_key} docs: {option_doc}")
    if config_doc:
        text.append(f"Project docs: {config_doc}")

    return "\n".join([line for line in text if line])


# FIXME(willkg): we can rewrite this as a dataclass as soon as we can drop
# Python 3.6 support
class Option:
    """Settings for a single configuration option.

    Use this when creating Everett configuration components.

    Example::

        from everett.manager import Option

        class MyService:
            # Note: The Config class has to be called "Config".
            class Config:
                host = Option(default="localhost")
                port = Option(default="8000", parser=int)

    """

    def __init__(
        self,
        default: Union[str, NoValue] = NO_VALUE,
        alternate_keys: Optional[List[str]] = None,
        doc: str = "",
        parser: Callable = str,
        meta: Any = None,
    ):
        """
        :param default: the default value (if any); this must be a string that is
            parseable by the specified parser; if no default is provided, this
            will raise an error or return ``everett.NO_VALUE`` depending on
            the value of ``raise_error``

        :param alternate_keys: the list of alternate keys to look up;
            supports a ``root:`` key prefix which will cause this to look at
            the configuration root rather than the current namespace

            .. versionadded:: 0.3

        :param doc: documentation for this config option

            .. versionadded:: 0.6

        :param parser: the parser for converting this value to a Python object

        :param meta: any meta information that's tied to this option; useful
            for noting which options are related in some way or which are secrets
            that shouldn't be logged

        """
        self.default = default
        self.alternate_keys = alternate_keys
        self.doc = doc
        self.parser = parser
        self.meta = meta or {}

    def __eq__(self, obj: Any) -> bool:
        return (
            isinstance(obj, Option)
            and obj.default == self.default
            and obj.alternate_keys == self.alternate_keys
            and obj.doc == self.doc
            and obj.parser == self.parser
            and obj.meta == self.meta
        )


def get_config_for_class(cls: Type) -> Dict[str, Tuple[Option, Type]]:
    """Roll up configuration options for this class and parent classes.

    This handles subclasses overriding configuration options in parent classes.

    :param cls: the component class to return configuration options for

    :returns: final dict of configuration options for this class in
        ``key -> (option, cls)`` form

    """
    options = {}
    for subcls in reversed(cls.__mro__):
        if not hasattr(subcls, "Config"):
            continue

        subcls_config = subcls.Config
        for attr in subcls_config.__dict__.keys():
            if attr.startswith("__"):
                continue

            val = getattr(subcls_config, attr)
            if isinstance(val, Option):
                options[attr] = (val, subcls)
    return options


def traverse_tree(
    instance: Any, namespace: Optional[List[str]] = None
) -> Iterable[Tuple[List[str], str, Option, Any]]:
    """Traverses a tree of objects and computes the configuration for it

    Note: This expects the tree not to have any loops or repeated nodes.

    :param instance: the component to traverse
    :param namespace: the list of strings forming the namespace or None

    :returns: list of ``(namespace, key, value, option, component)``

    """
    namespace = namespace or []

    # Check to see if this class has options; if it does, capture those and
    # traverse the tree
    this_options = get_config_for_class(instance.__class__)
    if not this_options:
        return []

    options = [
        (namespace, key, option, instance)
        for key, (option, cls) in this_options.items()
    ]

    # Now go through attributes for other options classes
    for attr in dir(instance):
        if attr.startswith("__"):
            continue
        # NOTE(willkg): we skip slots; maybe they could be component classes,
        # but that seems bizarre and I'd like to see a reasonable example
        # before supporting it
        val = getattr(instance, attr, None)
        if not val or isinstance(val, Option):
            continue

        options.extend(traverse_tree(val, namespace + [attr]))

    return options


def parse_env_file(envfile: Iterable[str]) -> Dict:
    """Parse the content of an iterable of lines as ``.env``.

    Return a dict of config variables.

    >>> from everett.manager import parse_env_file
    >>> parse_env_file(["DUDE=Abides"])
    {'DUDE': 'Abides'}

    """
    data = {}
    for line_no, line in enumerate(envfile):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigurationError(
                f"Env file line missing = operator (line {line_no + 1})"
            )
        k, v = line.split("=", 1)
        k = k.strip()
        if not ENV_KEY_RE.match(k):
            raise ConfigurationError(
                f"Invalid variable name {k!r} in env file (line {line_no + 1})"
            )

        v = v.strip()

        # Need to strip matching ' and " from beginning and end--but only one
        # round
        for quote in "'\"":
            if v.startswith(quote) and v.endswith(quote):
                v = v[1:-1]
                break

        data[k] = v

    return data


def parse_bool(val: str) -> bool:
    """Parse a bool value.

    Handles a series of values, but you should probably standardize on
    "true" and "false".

    >>> from everett.manager import parse_bool
    >>> parse_bool("y")
    True
    >>> parse_bool("FALSE")
    False

    """
    true_vals = ("t", "true", "yes", "y", "1", "on")
    false_vals = ("f", "false", "no", "n", "0", "off")

    val = val.lower()
    if val in true_vals:
        return True
    if val in false_vals:
        return False

    raise ValueError(f"{val!r} is not a valid bool value")


def parse_class(val: str) -> Any:
    """Parse a string, imports the module and returns the class.

    >>> from everett.manager import parse_class
    >>> parse_class("everett.manager.Option")
    <class 'everett.manager.Option'>

    """
    if "." not in val:
        raise ValueError(f"{val!r} is not a valid Python dotted-path")

    module_name, class_name = val.rsplit(".", 1)
    module = importlib.import_module(module_name)
    try:
        return getattr(module, class_name)
    except AttributeError as exc:
        raise ValueError(
            f"{class_name!r} is not a valid member of {qualname(module)}"
        ) from exc


_DATA_SIZE_METRIC_TO_MULTIPLIER = {
    "": 1,
    "b": 1,
    "kb": 1_000,
    "mb": pow(1_000, 2),
    "gb": pow(1_000, 3),
    "tb": pow(1_000, 4),
    "kib": 1_024,
    "mib": pow(1_024, 2),
    "gib": pow(1_024, 3),
    "tib": pow(1_024, 4),
}
_DATA_SIZE_RE = re.compile(
    r"^([0-9_]+)(" + "|".join(_DATA_SIZE_METRIC_TO_MULTIPLIER.keys()) + ")?$"
)


def parse_data_size(val: str) -> Any:
    """Parse a string denoting a data size into an int of bytes.

    This allows you to parse data sizes with a number and then the metric. Examples:

    * 10b - 10 bytes
    * 100kb - 100 kilobytes = 100 * 1000
    * 40gb - 40 gigabytes = 40 * 1000^3
    * 23gib - 40 gibibytes = 23 * 1024^3

    Supported metrics:

    * b - bytes
    * decimal:

      * kb - kilobytes
      * mb - megabytes
      * gb - gigabytes
      * tb - terabytes
      * pb - petabytes

    * binary:

      * kib - kibibytes
      * mib - mebibytes
      * gib - gibibytes
      * tib - tebibytes
      * pib - pebibytes

    The metrics are not case sensitive--it supports upper, lower, and mixed case.

    >>> from everett.manager import parse_data_size
    >>> parse_data_size("40_000_000")
    40000000
    >>> parse_data_size("40gb")
    40000000000
    >>> parse_data_size("20KiB")
    20480

    """
    fixed_val = val.lower().strip()
    try:
        return int(fixed_val)
    except ValueError:
        pass

    match = _DATA_SIZE_RE.match(fixed_val)
    if not match:
        raise ValueError(f"{val!r} is not a valid data size")
    amount, metric = match.groups()
    return int(amount) * _DATA_SIZE_METRIC_TO_MULTIPLIER[metric]


_TIME_UNIT_TO_MULTIPLIER = {
    "w": 7 * 24 * 60 * 60,
    "d": 24 * 60 * 60,
    "h": 60 * 60,
    "m": 60,
    "s": 1,
}
_TIME_RE = re.compile(r"([0-9_]+)([" + "".join(_TIME_UNIT_TO_MULTIPLIER.keys()) + r"])")


def parse_time_period(val: str) -> Any:
    """Parse a string denoting a time period into a number of seconds.

    Units:

    * w - week
    * d - day
    * h - hour
    * m - minute
    * s - second

    >>> from everett.manager import parse_time_period
    >>> parse_time_period("103")
    103
    >>> parse_time_period("1_000m")
    60000
    >>> parse_time_period("15m4s")
    904

    """
    fixed_val = val.lower().strip()
    try:
        return int(fixed_val)
    except ValueError:
        pass

    parts = _TIME_RE.findall(fixed_val)
    if not parts:
        raise ValueError(f"{val!r} is not a valid time period")

    total = 0
    for part in parts:
        amount, unit = part
        total = total + (int(amount) * _TIME_UNIT_TO_MULTIPLIER[unit])
    return total


def get_parser(parser: Callable) -> Callable:
    """Return a parsing function for a given parser."""
    # Special case bool so that we can explicitly give bool values otherwise
    # all values would be True since they're non-empty strings.
    if parser is bool:
        return parse_bool
    return parser


def listify(thing: Any) -> List[Any]:
    """Convert thing to a list.

    If thing is a string, then returns a list of thing. Otherwise
    returns thing.

    :param thing: string or list of things

    :returns: list

    """
    if thing is None:
        return []
    if isinstance(thing, str):
        return [thing]
    return thing


def generate_uppercase_key(key: str, namespace: Optional[List[str]] = None) -> str:
    """Given a key and a namespace, generates a final uppercase key.

    >>> generate_uppercase_key("foo")
    'FOO'
    >>> generate_uppercase_key("foo", ["namespace"])
    'NAMESPACE_FOO'
    >>> generate_uppercase_key("foo", ["namespace", "subnamespace"])
    'NAMESPACE_SUBNAMESPACE_FOO'

    """
    if namespace:
        namespace = [part for part in listify(namespace) if part]
        key = "_".join(namespace + [key])

    key = key.upper()
    return key


def get_key_from_envs(envs: Iterable[Any], key: str) -> Union[str, NoValue]:
    """Return the value of a key from the given dict respecting namespaces.

    Data can also be a list of data dicts.

    """
    # if it barks like a dict, make it a list have to use `get` since dicts and
    # lists both have __getitem__
    if hasattr(envs, "get"):
        envs = [envs]

    for env in envs:
        if key in env:
            return env[key]

    return NO_VALUE


class ListOf:
    """Parse a comma-separated list of things.

    >>> from everett.manager import ListOf
    >>> ListOf(str)('')
    []
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

    def __init__(self, parser: Callable, delimiter: str = ","):
        self.sub_parser = parser
        self.delimiter = delimiter

    def __call__(self, value: str) -> List[Any]:
        parser = get_parser(self.sub_parser)
        if value:
            return [parser(token) for token in value.split(self.delimiter)]
        else:
            return []

    def __repr__(self) -> str:
        return f"<ListOf({qualname(self.sub_parser)})>"


class ConfigOverrideEnv:
    """Override configuration layer for testing."""

    def get(
        self, key: str, namespace: Optional[List[str]] = None
    ) -> Union[str, NoValue]:
        """Retrieve value for key."""
        global _CONFIG_OVERRIDE

        # Short-circuit to reduce overhead.
        if not _CONFIG_OVERRIDE:
            return NO_VALUE
        full_key = generate_uppercase_key(key, namespace)
        logger.debug(f"Searching {self!r} for {full_key}")
        return get_key_from_envs(reversed(_CONFIG_OVERRIDE), full_key)

    def __repr__(self) -> str:
        return "<ConfigOverrideEnv>"


class ConfigObjEnv:
    """Source for pulling configuration values out of a Python object.

    This is handy for a few weird situations. For example, you can use this to
    "bridge" Everett configuration with command line arguments. The argparse
    Namespace works fine here.

    Namespace (the Everett one--not the argparse one) is prefixed. So key "foo"
    in namespace "bar" is "foo_bar".

    For example::

        import argparse

        from everett.manager import ConfigObjEnv, ConfigManager

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--debug", help="to debug or not to debug"
        )
        parsed_vals = parser.parse_known_args()[0]

        config = ConfigManager([
            ConfigObjEnv(parsed_vals)
        ])

        print config("debug", parser=bool)


    Keys are not case-sensitive--everything is converted to lowercase before
    pulling it from the object.


    .. Note::

       ConfigObjEnv has nothing to do with the library configobj.

    .. versionadded:: 0.6

    """

    def __init__(self, obj: Any, force_lower: bool = True):
        self.obj = obj

    def get(
        self, key: str, namespace: Optional[List[str]] = None
    ) -> Union[str, NoValue]:
        """Retrieve value for key."""
        full_key = generate_uppercase_key(key, namespace)
        full_key = full_key.lower()

        logger.debug(f"Searching {self!r} for {full_key}")

        # Build a map of lowercase -> actual key
        obj_keys = {
            item.lower(): item for item in dir(self.obj) if not item.startswith("__")
        }

        if full_key in obj_keys:
            val = getattr(self.obj, obj_keys[full_key])

            # If the value is None, then we're going to treat it as a non-valid
            # value.
            if val is not None:
                # This is goofy, but this allows people to specify arg parser
                # defaults, but do the right thing in Everett where everything
                # is a string until it's parsed.
                return str(val)

        return NO_VALUE

    def __repr__(self) -> str:
        return "<ConfigObjEnv>"


class ConfigDictEnv:
    """Source for pulling configuration out of a dict.

    This is handy for testing. You might also use it if you wanted to move all
    your defaults values into one centralized place.

    Keys are prefixed by namespaces and the whole thing is uppercased.

    For example, namespace "bar" for key "foo" becomes ``BAR_FOO`` in the
    dict.

    For example::

        from everett.manager import ConfigDictEnv, ConfigManager

        config = ConfigManager([
            ConfigDictEnv({
                "FOO_BAR": "someval",
                "BAT": "1",
            })
        ])

    Keys are not case sensitive. This also works::

        from everett.manager import ConfigDictEnv, ConfigManager

        config = ConfigManager([
            ConfigDictEnv({
                "foo_bar": "someval",
                "bat": "1",
            })
        ])

        print config("foo_bar")
        print config("FOO_BAR")
        print config.with_namespace("foo")("bar")


    Also, ``ConfigManager`` has a convenience classmethod for creating a
    ``ConfigManager`` with just a dict environment::

        from everett.manager import ConfigManager

        config = ConfigManager.from_dict({
            "FOO_BAR": "bat"
        })


    .. versionchanged:: 0.3
       Keys are no longer case-sensitive.

    """

    def __init__(self, cfg: Dict):
        self.cfg = {key.upper(): val for key, val in cfg.items()}

    def get(
        self, key: str, namespace: Optional[List[str]] = None
    ) -> Union[str, NoValue]:
        """Retrieve value for key."""
        full_key = generate_uppercase_key(key, namespace)
        logger.debug(f"Searching {self!r} for {full_key}")
        return get_key_from_envs(self.cfg, full_key)

    def __repr__(self) -> str:
        return f"<ConfigDictEnv: {self.cfg!r}>"


class ConfigEnvFileEnv:
    """Source for pulling configuration out of ``.env`` files.

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

        # CSP reporting
        CSP_SCRIPT_SRC="'self' www.googletagmanager.com"

    """

    def __init__(self, possible_paths: Union[str, List[str]]):
        self.data = {}
        self.path = None

        possible_paths = listify(possible_paths)
        for path in possible_paths:
            if not path:
                continue

            path = os.path.abspath(os.path.expanduser(path.strip()))
            if path and os.path.isfile(path):
                self.path = path
                with open(path) as envfile:
                    self.data = parse_env_file(envfile)
                    break

    def get(
        self, key: str, namespace: Optional[List[str]] = None
    ) -> Union[str, NoValue]:
        """Retrieve value for key."""
        full_key = generate_uppercase_key(key, namespace)
        logger.debug(f"Searching {self!r} for {full_key}")
        return get_key_from_envs(self.data, full_key)

    def __repr__(self) -> str:
        return f"<ConfigEnvFileEnv: {self.path!r}>"


class ConfigOSEnv:
    """Source for pulling configuration out of the environment.

    This source lets you specify configuration in the environment. This is
    useful for infrastructure related configuration like usernames and ports
    and secret configuration like passwords.

    Keys are prefixed by namespaces and the whole thing is uppercased.

    For example, key "foo" will be ``FOO`` in the environment.

    For example, namespace "bar" for key "foo" becomes ``BAR_FOO`` in the
    environment.

    Key and namespace can consist of alphanumeric characters and ``_``.

    .. Note::

       Unlike other config environments, this one is case sensitive in that
       keys defined in the environment **must** be all uppercase.

       For example, these are good::

           FOO=bar
           FOO_BAR=bar
           FOO_BAR1=bar


       This is bad::

           foo=bar


    To use, instantiate and toss in the source list::

        from everett.manager import ConfigOSEnv, ConfigManager

        config = ConfigManager([
            ConfigOSEnv()
        ])

    """

    def get(
        self, key: str, namespace: Optional[List[str]] = None
    ) -> Union[str, NoValue]:
        """Retrieve value for key."""
        full_key = generate_uppercase_key(key, namespace)
        logger.debug(f"Searching {self!r} for {full_key}")
        return get_key_from_envs(os.environ, full_key)

    def __repr__(self) -> str:
        return "<ConfigOSEnv>"


def _get_component_name(component: Any) -> str:
    if not inspect.isclass(component):
        cls = component.__class__
    else:
        cls = component
    return cls.__module__ + "." + cls.__name__


def get_runtime_config(
    config: "ConfigManager",
    component: Any,
    traverse: Callable = traverse_tree,
) -> List[Tuple[List[str], str, Any, Option]]:
    """Returns configuration specification and values for a component tree

    For example, if you had a tree of components instantiated, you could
    traverse the tree and log the configuration::

        from everett.manager import (
            ConfigManager,
            generate_uppercase_key,
            get_runtime_config,
            Option,
            parse_class,
        )

        class App:
            class Config:
                debug = Option(default="False", parser=bool)
                reader = Option(parser=parse_class)
                writer = Option(parser=parse_class)

            def __init__(self, config):
                self.config = config.with_options(self)

                # App has a reader and a writer each of which has configuration
                # options
                self.reader = self.config("reader")(config.with_namespace("reader"))
                self.writer = self.config("writer")(config.with_namespace("writer"))

        class Reader:
            class Config:
                input_file = Option()

            def __init__(self, config):
                self.config = config.with_options(self)

        class Writer:
            class Config:
                output_file = Option()

            def __init__(self, config):
                self.config = config.with_options(self)

        cm = ConfigManager.from_dict(
            {
                # This specifies which reader component to use. Because we
                # specified this one, we need to define a READER_INPUT_FILE
                # value.
                "READER": "__main__.Reader",
                "READER_INPUT_FILE": "input.txt",

                # Same thing for the writer component.
                "WRITER": "__main__.Writer",
                "WRITER_OUTPUT_FILE": "output.txt",
            }
        )

        my_app = App(cm)

        # This traverses the component tree starting with my_app and then
        # traversing .reader and .writer attributes.
        for namespace, key, value, option in get_runtime_config(cm, my_app):
            full_key = generate_uppercase_key(key, namespace)
            print(f"{full_key.upper()}={value or ''}")

        # This should print out:
        # DEBUG=False
        # READER=__main__.Reader
        # READER_INPUT_FILE=input.txt
        # WRITER=__main__.Writer
        # WRITER_OUTPUT_FILE=output.txt

    :param config: a configuration manager instance
    :param component: a component or tree of components
    :param traverse: the function for traversing the component tree; see
        :py:func:`everett.manager.traverse_tree` for signature

    :returns: a list of (namespace, key, value, option) tuples

    """
    runtime_config = []
    for namespace, key, option, obj in traverse(component):
        runtime_config.append(
            (
                namespace,
                key,
                config.with_namespace(namespace).with_options(obj)(
                    key, raise_error=False, raw_value=True
                ),
                option,
            )
        )
    return runtime_config


class ConfigManager:
    """Manage multiple configuration environment layers."""

    def __init__(
        self,
        environments: List[Any],
        doc: str = "",
        msg_builder: Callable = build_msg,
        with_override: bool = True,
    ):
        """Instantiate a ConfigManager.

        :param environments: list of configuration sources to look through in
            the order they should be looked through

        :param doc: help text printed to users when they encounter configuration
            errors

            .. versionadded:: 0.6

        :param msg_builder: function that takes arguments and builds an exception
            message intended to be printed or conveyed to the user

            For example::

                def build_msg(namespace, key, parser, msg="", option_doc="", config_doc=""):
                    full_key = namespace or []
                    full_key = "_".join(full_key + [key]).upper()

                    return (
                        f"{full_key} requires a value parseable by {qualname(parser)}\\n"
                        + option_doc + "\\n"
                        + config_doc + "\\n"
                    )

        :param with_override: whether or not to insert the special override
            environment used for testing as the first environment in the list
            of sources

        """
        self.with_override = with_override
        if with_override:
            # Add ConfigOverrideEnv if it's not in the environments list already
            override = [
                env for env in environments if isinstance(env, ConfigOverrideEnv)
            ]
            if not override:
                environments.insert(0, ConfigOverrideEnv())

        self.envs = environments
        self.doc = doc
        self.msg_builder = msg_builder

        self.namespace: List[str] = []

        self.bound_component: Any = None
        self.bound_component_prefix: List[str] = []
        self.bound_component_options: Mapping[str, Any] = {}

        self.original_manager = self

    @classmethod
    def basic_config(cls, env_file: str = ".env", doc: str = "") -> "ConfigManager":
        """Return a basic ConfigManager.

        This sets up a ConfigManager that will look for configuration in
        this order:

        1. environment
        2. specified ``env_file`` defaulting to ``.env``

        This is for a fast one-line opinionated setup.

        Example::

            from everett.manager import ConfigManager

            config = ConfigManager.basic_config()


        This is shorthand for::

            config = ConfigManager(
                environments=[
                    ConfigOSEnv(),
                    ConfigEnvFileEnv(['.env'])
                ]
            )


        :param env_file: the name of the env file to use
        :param doc: help text printed to users when they encounter configuration
            errors

        :returns: a :py:class:`everett.manager.ConfigManager`

        """
        return cls(environments=[ConfigOSEnv(), ConfigEnvFileEnv([env_file])], doc=doc)

    @classmethod
    def from_dict(cls, dict_config: Dict) -> "ConfigManager":
        """Create a ConfigManager with specified configuration as a Python dict.

        This is shorthand for::

            config = ConfigManager([ConfigDictEnv(dict_config)])


        This is handy for writing tests for the app you're using Everett in.

        :param dict_config: Python dict holding the configuration for this
            manager

        :returns: ConfigManager with specified configuration

        .. versionadded:: 0.3

        """
        return cls([ConfigDictEnv(dict_config)])

    def get_bound_component(self) -> Any:
        """Retrieve the bound component for this config object.

        :returns: component or None

        """
        return self.bound_component

    def get_namespace(self) -> List[str]:
        """Retrieve the complete namespace for this config object.

        :returns: namespace as a list of strings

        """
        return self.namespace

    def _get_base_config(self) -> "ConfigManager":
        return self.original_manager

    def clone(self) -> "ConfigManager":
        my_clone = ConfigManager(
            environments=list(self.envs),
            doc=self.doc,
            msg_builder=self.msg_builder,
            with_override=self.with_override,
        )
        my_clone.namespace = list(self.namespace)
        my_clone.bound_component = self.bound_component
        my_clone.bound_component_prefix = []
        my_clone.bound_component_options = self.bound_component_options

        my_clone.original_manager = self.original_manager

        return my_clone

    def with_namespace(self, namespace: Union[List[str], str]) -> "ConfigManager":
        """Apply a namespace to this configuration.

        Namespaces accumulate as you add them.

        :param namepace: namespace as a string or list of strings

        :returns: a clone of the ConfigManager instance with the namespace applied

        """
        namespace = listify(namespace)
        if not namespace:
            return self

        my_clone = self.clone()
        if my_clone.bound_component:
            my_clone.bound_component_prefix.extend(namespace)
        else:
            my_clone.namespace.extend(namespace)
        return my_clone

    def with_options(self, component: Any) -> "ConfigManager":
        """Apply options component options to this configuration.

        :param component: the instance or class with a Config to bind this
            ConfigManager to

        :returns: a clone of the ConfigManager instance bound to specified
            component

        """
        # If this is an instance, get the class
        if not inspect.isclass(component):
            component = component.__class__

        options = get_config_for_class(component)
        # NOTE(willkg): if the component has no options, then there's nothing
        # to bind to
        if not options:
            return self

        my_clone = self.clone()
        my_clone.bound_component = component
        my_clone.bound_component_prefix = []
        my_clone.bound_component_options = options

        # IF there's a bound component with a prefix, then it means someone is doing
        # something like:
        #
        # config = config.with_options(Comp).with_namespace("foo").with_options(SubComp)
        #
        # In that case, we want the namespace "foo" to be part of the namespace
        # and not part of the key prefix for SubComp.
        if self.bound_component_prefix:
            my_clone.namespace.extend(self.bound_component_prefix)

        return my_clone

    def __call__(
        self,
        key: str,
        namespace: Union[List[str], str, None] = None,
        default: Union[str, NoValue] = NO_VALUE,
        default_if_empty: bool = True,
        alternate_keys: Optional[List[str]] = None,
        doc: str = "",
        parser: Callable = str,
        raise_error: bool = True,
        raw_value: bool = False,
    ) -> Any:
        """Return a parsed value from the environment.

        :param key: the key to look up

        :param namespace: the namespace for the key--different environments
            use this differently

        :param default: the default value (if any); this must be a string that is
            parseable by the specified parser; if no default is provided, this
            will raise an error or return ``everett.NO_VALUE`` depending on
            the value of ``raise_error``

            If this ConfigManager is bound to a component, the default will be
            the default of the option in the bound component configuration.

        :param default_if_empty: if True, treat empty string values as a
            non-value and return the specified default

        :param alternate_keys: the list of alternate keys to look up;
            supports a ``root:`` key prefix which will cause this to look at
            the configuration root rather than the current namespace

            If this ConfigManager is bound to a component, the alternate_keys
            will be the alternate_keys of the option in the bound component
            configuration.

            .. versionadded:: 0.3

        :param doc: documentation for this config option

            If this ConfigManager is bound to a component, the doc will be the
            doc of the option in the bound component configuration.

            .. versionadded:: 0.6

        :param parser: the parser for converting this value to a Python object

            If this ConfigManager is bound to a component, the parser will be
            the parser of the option in the bound component configuration.

        :param raise_error: True if you want a lack of value to raise a
            ``everett.ConfigurationError``

        :param raw_value: True if you want the raw unparsed value, False otherwise

        :raises everett.ConfigurationMissingError: if the required bit of configuration
            is missing from all the environments

        :raises everett.InvalidKeyError: if the configuration key doesn't exist for
            that component

        :raises everett.InvalidValueError: if the configuration value is
            invalid in some way (not an integer, not a bool, etc)

        .. Note::

           The default value should **always** be a string that is parseable by
           the parser. This simplifies thinking about values since **all**
           values are strings that are parsed by the parser rather than default
           values do one thing and non-default values doa nother. Further, it
           simplifies documentation for the user since the default value is an
           example value.

           The parser can be any callable that takes a string value and returns
           a parsed value.

        """
        if not (default is NO_VALUE or isinstance(default, str)):
            raise ConfigurationError(f"default value {default!r} is not a string")

        # If we have a bound component, then the "namespace" is a key prefix,
        # so do that. Otherwise it's a namespace.
        if self.bound_component:
            key = "_".join(
                listify(self.bound_component_prefix) + listify(namespace) + [key]
            )
            namespace = self.namespace

        else:
            namespace = self.namespace + listify(namespace)

        # If this is a bound config, then apply everything to that
        if self.bound_component:
            try:
                option, cls = self.bound_component_options[key]
            except KeyError as exc:
                if raise_error:
                    raise InvalidKeyError(
                        f"{key!r} is not a valid key for this component"
                    ) from exc
                return None

            default = option.default
            alternate_keys = option.alternate_keys
            doc = option.doc
            parser = option.parser

        if raw_value:
            # If we're returning raw values, then we can just use str which is
            # a no-op.
            parser = str
        else:
            parser = get_parser(parser)

        # Go through all possible keys
        all_keys = [key]
        if alternate_keys:
            all_keys = all_keys + alternate_keys

        for possible_key in all_keys:
            if possible_key.startswith("root:"):
                # If this is a root-anchored key, we drop the namespace.
                possible_key = possible_key[5:]
                use_namespace = None
            else:
                use_namespace = namespace

            logger.debug(f"Looking up key: {possible_key}, namespace: {use_namespace}")

            # Go through environments in reverse order
            for env in self.envs:
                val = env.get(possible_key, use_namespace)

                # If the value is the empty string and default_if_empty is
                # True, treat it as a non-value
                if val == "" and default_if_empty:
                    val = NO_VALUE

                if val is not NO_VALUE:
                    try:
                        parsed_val = parser(val)
                        logger.debug(f"Returning raw: {val!r}, parsed: {parsed_val!r}")
                        return parsed_val
                    except ConfigurationError:
                        # Re-raise ConfigurationError and friends since that's
                        # what we want to be raising.
                        raise
                    except Exception as exc:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        exc_type_name = exc_type.__name__ if exc_type else "None"

                        msg = self.msg_builder(
                            namespace=use_namespace,
                            key=key,
                            parser=parser,
                            msg=f"{exc_type_name}: {exc_value}",
                            option_doc=doc,
                            config_doc=self.doc,
                        )

                        raise InvalidValueError(msg, namespace, key, parser) from exc

        # Return the default if there is one
        if default is not NO_VALUE:
            try:
                parsed_val = parser(default)
                logger.debug(
                    f"Returning default raw: {default!r}, parsed: {parsed_val!r}"
                )
                return parsed_val
            except ConfigurationError:
                # Re-raise ConfigurationError and friends since that's
                # what we want to be raising.
                raise
            except Exception as exc:
                # FIXME(willkg): This is a programmer error--not a user
                # configuration error. We might want to denote that better.
                exc_type, exc_value, exc_traceback = sys.exc_info()
                exc_type_name = exc_type.__name__ if exc_type else "None"

                msg = self.msg_builder(
                    namespace=use_namespace,
                    key=key,
                    parser=parser,
                    msg=f"{exc_type_name}: {exc_value} (default value)",
                    option_doc=doc,
                    config_doc=self.doc,
                )

                raise InvalidValueError(msg, namespace, key, parser) from exc

        # No value specified and no default, so raise an error to the user
        if raise_error:
            msg = self.msg_builder(
                namespace=use_namespace,
                key=key,
                parser=parser,
                option_doc=doc,
                config_doc=self.doc,
            )

            raise ConfigurationMissingError(msg, namespace, key, parser)

        logger.debug("Found nothing--returning NO_VALUE")
        # Otherwise return NO_VALUE
        return NO_VALUE

    def raise_configuration_error(self, msg: str) -> None:
        """Convenience function for raising configuration errors.

        This is helpful for situations where you need to do additional checking
        of configuration values and need to raise a configuration error for the
        user that includes the configuration documentation.

        For example::

            from everett.manager import ConfigManager

            config = ConfigManager.basic_config()
            host = config("host")
            port = config("port")

            if host is None or port is None:
                config.raise_configuration_error(
                    "Both HOST and PORT must be specified."
                )

        :param msg: the configuration error message

        """

        msg = self.msg_builder(
            namespace=None,
            key=None,
            parser=None,
            msg=msg,
            option_doc=None,
            config_doc=self.doc,
        )
        raise ConfigurationError(msg)

    def __repr__(self) -> str:
        if self.bound_component:
            name = _get_component_name(self.bound_component)
            return f"<ConfigManager({name}): namespace:{self.get_namespace()}>"
        else:
            return f"<ConfigManager: namespace:{self.get_namespace()}>"


# This is a stack of overrides to be examined in reverse order
_CONFIG_OVERRIDE = []


class ConfigOverride:
    """Handle contexts and decoration for overriding config in testing."""

    def __init__(self, **cfg: str):
        self._cfg = cfg

    def push_config(self) -> None:
        """Push ``self._cfg`` as a config layer onto the stack."""
        _CONFIG_OVERRIDE.append(self._cfg)

    def pop_config(self) -> None:
        """Pop a config layer off.

        :raises IndexError: If there are no layers to pop off

        """
        _CONFIG_OVERRIDE.pop()

    def __enter__(self) -> None:
        self.push_config()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        self.pop_config()

    def decorate(self, fun: Callable) -> Callable:
        """Decorate a function for overriding configuration."""

        @wraps(fun)
        def _decorated(*args: Any, **kwargs: Any) -> Any:
            # Push the config, run the function and pop it afterwards.
            self.push_config()
            try:
                return fun(*args, **kwargs)
            finally:
                self.pop_config()

        return _decorated

    def __call__(self, class_or_fun: Callable) -> Callable:
        if inspect.isclass(class_or_fun):
            # If class_or_fun is a class, decorate all of its methods
            # that start with 'test'.
            for attr in class_or_fun.__dict__.keys():
                prop = getattr(class_or_fun, attr)
                if attr.startswith("test") and callable(prop):
                    setattr(class_or_fun, attr, self.decorate(prop))
            return class_or_fun

        else:
            return self.decorate(class_or_fun)


def config_override(**cfg: str) -> ConfigOverride:
    """Allow you to override config for writing tests.

    This can be used as a class decorator::

        @config_override(FOO="bar", BAZ="bat")
        class FooTestClass(object):
            ...


    This can be used as a function decorator::

        @config_override(FOO="bar")
        def test_foo():
            ...


    This can also be used as a context manager::

        def test_foo():
            with config_override(FOO="bar"):
                ...

    """
    return ConfigOverride(**cfg)
