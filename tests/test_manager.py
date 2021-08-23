# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import os

import pytest

from everett import (
    ConfigurationError,
    InvalidValueError,
    ConfigurationMissingError,
    NO_VALUE,
)
import everett.manager
from everett.manager import (
    ConfigDictEnv,
    ConfigEnvFileEnv,
    ConfigManager,
    ConfigOSEnv,
    ConfigObjEnv,
    ListOf,
    Option,
    config_override,
    generate_uppercase_key,
    get_config_for_class,
    get_key_from_envs,
    get_parser,
    get_runtime_config,
    listify,
    parse_bool,
    parse_class,
    parse_env_file,
    qualname,
)


@pytest.mark.parametrize(
    "thing, expected",
    [
        # built-in
        (str, "str"),
        # function in a module
        (qualname, "everett.manager.qualname"),
        # module
        (everett.manager, "everett.manager"),
        # class
        (ConfigManager, "everett.manager.ConfigManager"),
        # class method
        (ConfigManager.basic_config, "everett.manager.ConfigManager.basic_config"),
        # instance
        (ListOf(bool), "<ListOf(bool)>"),
        # instance method
        (ConfigOSEnv().get, "everett.manager.ConfigOSEnv.get"),
    ],
)
def test_qualname(thing, expected):
    assert qualname(thing) == expected


def test_get_config_for_class():
    """Verify that get_config_for_class works for a trivial class"""

    class Component:
        class Config:
            user = Option(doc="no help")

    options = get_config_for_class(Component)
    assert list(options.keys()) == ["user"]


def test_get_config_for_class_complex_mro():
    """Verify get_config_for_class with an MRO that has a diamond shape to it.

    The goal here is to make sure the C class has the right options from the
    right components and in the right order.

    """

    class ComponentBase:
        pass

    class A(ComponentBase):
        class Config:
            a = Option(default="a")

    class B(ComponentBase):
        class Config:
            b = Option(default="b")
            bd = Option(default="b")

    class C(B, A):
        class Config:
            # Note: This overrides B's b.
            b = Option(default="c")
            c = Option(default="c")

    options = get_config_for_class(C)
    assert list(
        sorted([(key, opt.default) for key, (opt, cls) in options.items()])
    ) == [
        ("a", "a"),  # from A
        ("b", "c"),  # from C (overrides B's)
        ("bd", "b"),  # from B
        ("c", "c"),  # from C
    ]


def test_no_value():
    assert bool(NO_VALUE) is False
    assert NO_VALUE is not True
    assert str(NO_VALUE) == "NO_VALUE"


def test_parse_bool_error():
    with pytest.raises(ValueError):
        parse_bool("")


@pytest.mark.parametrize(
    "data,expected",
    [
        (None, []),
        ("", [""]),
        ([], []),
        ("foo", ["foo"]),
        (["foo"], ["foo"]),
        (["foo", "bar"], ["foo", "bar"]),
    ],
)
def test_listify(data, expected):
    assert listify(data) == expected


@pytest.mark.parametrize(
    "data", ["t", "true", "True", "TRUE", "y", "yes", "YES", "1", "on", "On", "ON"]
)
def test_parse_bool_true(data):
    assert parse_bool(data) is True


@pytest.mark.parametrize(
    "data",
    ["f", "false", "False", "FALSE", "n", "no", "No", "NO", "0", "off", "Off", "OFF"],
)
def test_parse_bool_false(data):
    assert parse_bool(data) is False


def test_parse_bool_with_config():
    config = ConfigManager.from_dict({"foo": "bar"})

    # Test key is there, but value is bad
    with pytest.raises(InvalidValueError) as excinfo:
        config("foo", parser=bool)
    assert str(excinfo.value) == (
        "ValueError: 'bar' is not a valid bool value\n"
        "FOO requires a value parseable by everett.manager.parse_bool"
    )

    # Test key is not there and default is bad
    with pytest.raises(InvalidValueError) as excinfo:
        config("phil", default="foo", parser=bool)
    assert str(excinfo.value) == (
        "ValueError: 'foo' is not a valid bool value (default value)\n"
        "PHIL requires a value parseable by everett.manager.parse_bool"
    )


def test_parse_missing_class():
    with pytest.raises(ImportError):
        parse_class("doesnotexist.class")

    with pytest.raises(ValueError):
        parse_class("hashlib.doesnotexist")


def test_parse_class():
    from hashlib import md5

    assert parse_class("hashlib.md5") == md5


def test_parse_class_config():
    config = ConfigManager.from_dict(
        {"foo_cls": "hashlib.doesnotexist", "bar_cls": "doesnotexist.class"}
    )

    with pytest.raises(InvalidValueError) as exc_info:
        config("foo_cls", parser=parse_class)
    assert str(exc_info.value) == (
        "ValueError: 'doesnotexist' is not a valid member of hashlib\n"
        "FOO_CLS requires a value parseable by everett.manager.parse_class"
    )

    with pytest.raises(InvalidValueError) as exc_info:
        config("bar_cls", parser=parse_class)
    assert str(exc_info.value) == (
        "ModuleNotFoundError: No module named 'doesnotexist'\n"
        "BAR_CLS requires a value parseable by everett.manager.parse_class"
    )


def test_get_parser():
    assert get_parser(bool) == parse_bool
    assert get_parser(str) == str

    # Note: I'd like to do this with a lambda, but flake8 has a bug where it
    # complains about assigning lambdas to a varaible and doing "noqa" doesn't
    # work.
    def foo():
        pass

    assert get_parser(foo) == foo


def test_ListOf():
    assert ListOf(str)("") == []
    assert ListOf(str)("foo") == ["foo"]
    assert ListOf(bool)("t,f") == [True, False]
    assert ListOf(int)("1,2,3") == [1, 2, 3]
    assert ListOf(int, delimiter=":")("1:2") == [1, 2]


def test_ListOf_error():
    config = ConfigManager.from_dict({"bools": "t,f,badbool"})
    with pytest.raises(InvalidValueError) as exc_info:
        config("bools", parser=ListOf(bool))

    assert str(exc_info.value) == (
        "ValueError: 'badbool' is not a valid bool value\n"
        "BOOLS requires a value parseable by <ListOf(bool)>"
    )


class TestConfigObjEnv:
    def test_basic(self):
        class Namespace:
            pass

        obj = Namespace()
        setattr(obj, "foo", "bar")
        setattr(obj, "foo_baz", "bar")

        coe = ConfigObjEnv(obj)
        assert coe.get("foo") == "bar"
        assert coe.get("FOO") == "bar"
        assert coe.get("FOO_BAZ") == "bar"

    def test_with_argparse(self):
        parser = argparse.ArgumentParser()
        parser.add_argument("--debug", help="to debug or not to debug")
        parsed_vals = parser.parse_known_args([])[0]

        config = ConfigManager([ConfigObjEnv(parsed_vals)])

        assert config("debug", parser=bool, raise_error=False) is NO_VALUE

        parsed_vals = parser.parse_known_args(["--debug=y"])[0]

        config = ConfigManager([ConfigObjEnv(parsed_vals)])

        assert config("debug", parser=bool) is True

    def test_with_argparse_actions(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--debug", help="to debug or not to debug", action="store_true"
        )
        parsed_vals = parser.parse_known_args([])[0]

        config = ConfigManager([ConfigObjEnv(parsed_vals)])

        # What happens is that argparse doesn't see an arg, so saves
        # debug=False. ConfigObjEnv converts that to "False". That gets parsed
        # as False by the Everett parse_bool function. That's kind of
        # roundabout but "works" for some/most cases.
        assert config("debug", parser=bool) is False

        parsed_vals = parser.parse_known_args(["--debug"])[0]

        config = ConfigManager([ConfigObjEnv(parsed_vals)])

        assert config("debug", parser=bool) is True


def test_ConfigDictEnv():
    cde = ConfigDictEnv(
        {"FOO": "bar", "A_FOO": "a_bar", "A_B_FOO": "a_b_bar", "lower_foo": "bar"}
    )
    assert cde.get("foo") == "bar"
    assert cde.get("foo", namespace=["a"]) == "a_bar"
    assert cde.get("foo", namespace=["a", "b"]) == "a_b_bar"
    assert cde.get("FOO", namespace=["a"]) == "a_bar"
    assert cde.get("foo", namespace=["A"]) == "a_bar"
    assert cde.get("FOO", namespace=["A"]) == "a_bar"

    cde = ConfigDictEnv({"foo": "bar"})
    assert cde.get("foo") == "bar"
    assert cde.get("FOO") == "bar"


def test_ConfigOSEnv():
    os.environ["EVERETT_TEST_FOO"] = "bar"
    os.environ["EVERETT_TEST_FOO"] = "bar"
    cose = ConfigOSEnv()

    assert cose.get("everett_test_foo") == "bar"
    assert cose.get("EVERETT_test_foo") == "bar"
    assert cose.get("foo", namespace=["everett", "test"]) == "bar"


def test_ConfigEnvFileEnv(datadir):
    env_filename = os.path.join(datadir, ".env")
    cefe = ConfigEnvFileEnv(["/does/not/exist/.env", env_filename])
    assert cefe.get("not_a", namespace="youre") == "golfer"
    assert cefe.get("loglevel") == "walter"
    assert cefe.get("LOGLEVEL") == "walter"
    assert cefe.get("missing") is NO_VALUE
    assert cefe.data == {
        "LOGLEVEL": "walter",
        "DEBUG": "True",
        "YOURE_NOT_A": "golfer",
        "DATABASE_URL": "sqlite:///kahlua.db",
    }

    cefe = ConfigEnvFileEnv(env_filename)
    assert cefe.get("not_a", namespace="youre") == "golfer"

    cefe = ConfigEnvFileEnv("/does/not/exist/.env")
    assert cefe.get("loglevel") is NO_VALUE


def test_parse_env_file():
    assert parse_env_file(["PLAN9=outerspace"]) == {"PLAN9": "outerspace"}
    with pytest.raises(ConfigurationError) as exc_info:
        parse_env_file(["3AMIGOS=infamous"])
    assert str(exc_info.value) == "Invalid variable name '3AMIGOS' in env file (line 1)"
    with pytest.raises(ConfigurationError) as exc_info:
        parse_env_file(["INVALID-CHAR=value"])
    assert str(exc_info.value) == (
        "Invalid variable name 'INVALID-CHAR' in env file (line 1)"
    )
    with pytest.raises(ConfigurationError) as exc_info:
        parse_env_file(["", "MISSING-equals"])
    assert str(exc_info.value) == "Env file line missing = operator (line 2)"


@pytest.mark.parametrize(
    "key, ns, expected",
    [
        ("k", None, "K"),
        ("a_b", None, "A_B"),
        ("k", "ns", "NS_K"),
        ("k", ["ns1", "ns2"], "NS1_NS2_K"),
        ("k", ["ns1", "", "ns2"], "NS1_NS2_K"),
    ],
)
def test_generate_uppercase_key(key, ns, expected):
    full_key = generate_uppercase_key(key, ns)
    assert full_key == expected


def test_get_key_from_envs():
    assert get_key_from_envs({"K": "v"}, "K") == "v"
    assert get_key_from_envs([{"K": "v"}, {"L": "w"}], "L") == "w"
    assert get_key_from_envs({"K": "v"}, "Q") is NO_VALUE
    # first match wins
    envs = [{"K": "v"}, {"L": "w"}, {"K": "z"}]
    assert get_key_from_envs(envs, "K") == "v"
    # works with reversed iterator
    envs = reversed([{"L": "v"}, {"L": "w"}])
    assert get_key_from_envs(envs, "L") == "w"
    # works with os.environ
    os.environ["DUDE_ABIDES"] = "yeah, man"
    assert get_key_from_envs(os.environ, "DUDE_ABIDES") == "yeah, man"


def test_config():
    config = ConfigManager([])

    # Don't raise an error and no default yields NO_VALUE
    assert config("DOESNOTEXISTNOWAY", raise_error=False) is NO_VALUE

    # Defaults to raising an error
    with pytest.raises(ConfigurationMissingError) as exc_info:
        config("DOESNOTEXISTNOWAY")
    assert str(exc_info.value) == "DOESNOTEXISTNOWAY requires a value parseable by str"

    # Raises an error if raise_error is True
    with pytest.raises(ConfigurationMissingError) as exc_info:
        config("DOESNOTEXISTNOWAY", raise_error=True)
    assert str(exc_info.value) == "DOESNOTEXISTNOWAY requires a value parseable by str"

    # With a default, returns the default
    assert config("DOESNOTEXISTNOWAY", default="ohreally") == "ohreally"

    # Test doc
    with pytest.raises(ConfigurationMissingError) as exc_info:
        config("DOESNOTEXISTNOWAY", doc="Nothing to see here.")
    assert str(exc_info.value) == (
        "DOESNOTEXISTNOWAY requires a value parseable by str\n"
        "DOESNOTEXISTNOWAY docs: Nothing to see here."
    )


def test_invalidvalueerror():
    config = ConfigManager.from_dict({"foo_bar": "bat"})
    with pytest.raises(InvalidValueError) as excinfo:
        config("bar", namespace="foo", parser=bool)

        assert excinfo.value.namespace == "foo"
        assert excinfo.value.key == "bar"
        assert excinfo.value.parser == bool


def test_configurationmissingerror():
    # Verify ConfigurationMissingError has the right values
    config = ConfigManager([])

    # Defaults to raising an error
    with pytest.raises(ConfigurationMissingError) as exc_info:
        config("DOESNOTEXISTNOWAY", namespace="foo")

    assert (
        exc_info.value.args[0]
        == "FOO_DOESNOTEXISTNOWAY requires a value parseable by str"
    )
    assert exc_info.value.namespace == "foo"
    assert exc_info.value.key == "DOESNOTEXISTNOWAY"
    assert exc_info.value.parser == str


def test_config_from_dict():
    config = ConfigManager.from_dict({})

    assert config("FOO", raise_error=False) is NO_VALUE

    config = ConfigManager.from_dict({"FOO": "bar"})

    assert config("FOO", raise_error=False) == "bar"


def test_basic_config(datadir):
    os.environ["EVERETT_BASIC_CONFIG_TEST"] = "foo"
    env_filename = os.path.join(datadir, ".env")
    config = ConfigManager.basic_config(env_filename)

    # This doesn't exist in either the environment or the env file
    assert config("FOO", raise_error=False) is NO_VALUE

    # This exists in the environment
    assert config("EVERETT_BASIC_CONFIG_TEST") == "foo"

    # This exists in the env file
    assert config("LOGLEVEL") == "walter"


def test_basic_config_with_docs(datadir):
    config = ConfigManager.basic_config(doc="foo")

    assert config.doc == "foo"


def test_config_manager_doc():
    config = ConfigManager(
        [ConfigDictEnv({"foo": "bar"})], doc="See http://example.com/configuration"
    )

    # Test ConfigManager doc shows up
    with pytest.raises(ConfigurationError) as exc_info:
        config("foo", parser=int)
    assert str(exc_info.value) == (
        "ValueError: invalid literal for int() with base 10: 'bar'\n"
        "FOO requires a value parseable by int\n"
        "Project docs: See http://example.com/configuration"
    )

    # Test config doc and ConfigManager doc show up
    with pytest.raises(ConfigurationError) as exc_info:
        config("foo", parser=int, doc="Port to listen on.")
    assert str(exc_info.value) == (
        "ValueError: invalid literal for int() with base 10: 'bar'\n"
        "FOO requires a value parseable by int\n"
        "FOO docs: Port to listen on.\n"
        "Project docs: See http://example.com/configuration"
    )


def test_config_override():
    config = ConfigManager([])

    # Make sure the key doesn't exist
    assert config("DOESNOTEXISTNOWAY", raise_error=False) is NO_VALUE

    # Try one override
    with config_override(DOESNOTEXISTNOWAY="bar"):
        assert config("DOESNOTEXISTNOWAY") == "bar"

    # Try nested overrides--innermost one rules supreme!
    with config_override(DOESNOTEXISTNOWAY="bar"):
        with config_override(DOESNOTEXISTNOWAY="bat"):
            assert config("DOESNOTEXISTNOWAY") == "bat"


def test_default_must_be_string():
    config = ConfigManager([])

    with pytest.raises(ConfigurationError):
        assert config("DOESNOTEXIST", default=True)


def test_with_namespace():
    config = ConfigManager(
        [ConfigDictEnv({"FOO_BAR": "foobaz", "BAR": "baz", "BAT": "bat"})]
    )

    # Verify the values first
    assert config("bar", namespace=["foo"]) == "foobaz"
    assert config("bar") == "baz"
    assert config("bat") == "bat"

    # Create the namespaced config
    config_with_namespace = config.with_namespace("foo")
    assert config_with_namespace("bar") == "foobaz"

    # Verify 'bat' is not available because it's not in the namespace
    with pytest.raises(ConfigurationError):
        config_with_namespace("bat")


def test_get_namespace():
    config = ConfigManager.from_dict(
        {"FOO": "abc", "FOO_BAR": "abc", "FOO_BAR_BAZ": "abc"}
    )
    assert config.get_namespace() == []

    ns_foo_config = config.with_namespace("foo")
    assert ns_foo_config.get_namespace() == ["foo"]

    ns_foo_bar_config = ns_foo_config.with_namespace("bar")
    assert ns_foo_bar_config.get_namespace() == ["foo", "bar"]


@pytest.mark.parametrize(
    "key,alternate_keys,expected",
    [
        # key, alternate keys, expected
        ("FOO", [], "foo_abc"),
        ("FOO", ["FOO_BAR"], "foo_abc"),
        ("BAD_KEY", ["FOO_BAR"], "foo_bar_abc"),
        ("BAD_KEY", ["BAD_KEY1", "BAD_KEY2", "FOO_BAR_BAZ"], "foo_bar_baz_abc"),
    ],
)
def test_alternate_keys(key, alternate_keys, expected):
    config = ConfigManager.from_dict(
        {"FOO": "foo_abc", "FOO_BAR": "foo_bar_abc", "FOO_BAR_BAZ": "foo_bar_baz_abc"}
    )

    assert config(key, alternate_keys=alternate_keys) == expected


@pytest.mark.parametrize(
    "key,alternate_keys,expected",
    [
        # key, alternate keys, expected
        ("BAR", [], "foo_bar_abc"),
        ("BAD_KEY", ["BAD_KEY1", "BAR_BAZ"], "foo_bar_baz_abc"),
        ("bad_key", ["bad_key1", "bar_baz"], "foo_bar_baz_abc"),
        ("bad_key", ["root:common_foo"], "common_foo_abc"),
    ],
)
def test_alternate_keys_with_namespace(key, alternate_keys, expected):
    config = ConfigManager.from_dict(
        {
            "COMMON_FOO": "common_foo_abc",
            "FOO": "foo_abc",
            "FOO_BAR": "foo_bar_abc",
            "FOO_BAR_BAZ": "foo_bar_baz_abc",
        }
    )

    config = config.with_namespace("FOO")

    assert config(key, alternate_keys=alternate_keys) == expected


def test_raw_value():
    config = ConfigManager.from_dict({"FOO_BAR": "1"})
    assert config("FOO_BAR", parser=int) == 1
    assert config("FOO_BAR", parser=int, raw_value=True) == "1"

    assert str(config("NOEXIST", parser=int, raise_error=False)) == "NO_VALUE"

    config = config.with_namespace("FOO")
    assert config("BAR", parser=int) == 1
    assert config("BAR", parser=int, raw_value=True) == "1"


def test_with_options():
    """Verify .with_options() restricts configuration"""
    config = ConfigManager(
        [ConfigDictEnv({"FOO_BAR": "a", "FOO_BAZ": "b", "BAR": "c", "BAZ": "d"})]
    )

    class SomeComponent:
        class Config:
            baz = Option(default="", doc="some help here", parser=str)

        def __init__(self, config):
            self.config = config.with_options(self)

    # Create the component with regular config
    comp = SomeComponent(config)
    assert comp.config("baz") == "d"
    with pytest.raises(ConfigurationError):
        # This is not a valid option for this component
        comp.config("bar")

    # Create the component with config in the "foo" namespace
    comp2 = SomeComponent(config.with_namespace("foo"))
    assert comp2.config("baz") == "b"
    with pytest.raises(ConfigurationError):
        # This is not a valid option for this component
        comp2.config("bar")


def test_nested_options():
    """Verify nested BoundOptions works."""
    config = ConfigManager.from_dict({})

    class Foo:
        class Config:
            option1 = Option(default="opt1default", parser=str)

    class Bar:
        class Config:
            option2 = Option(default="opt2default", parser=str)

    config = ConfigManager.basic_config()
    config = config.with_options(Foo)
    config = config.with_options(Bar)

    assert config("option2") == "opt2default"
    with pytest.raises(ConfigurationError):
        config("option1")


def test_default_comes_from_options():
    """Verify that the default is picked up from options"""
    config = ConfigManager([])

    class SomeComponent:
        class Config:
            foo = Option(default="abc")

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config)
    assert comp.config("foo") == "abc"


def test_parser_comes_from_options():
    """Verify the parser is picked up from options"""
    config = ConfigManager([ConfigDictEnv({"FOO": "1"})])

    class SomeComponent:
        class Config:
            foo = Option(parser=int)

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config)
    assert comp.config("foo") == 1


def test_component_get_namespace():
    config = ConfigManager.from_dict(
        {"FOO": "abc", "FOO_BAR": "abc", "FOO_BAR_BAZ": "abc"}
    )
    assert config.get_namespace() == []

    class SomeComponent:
        class Config:
            foo = Option(parser=int)

        def __init__(self, config):
            self.config = config.with_options(self)

        def my_namespace_is(self):
            return self.config.get_namespace()

    comp = SomeComponent(config)
    assert comp.my_namespace_is() == []

    comp = SomeComponent(config.with_namespace("foo"))
    assert comp.my_namespace_is() == ["foo"]


def test_component_alternate_keys():
    config = ConfigManager.from_dict(
        {"COMMON": "common_abc", "FOO": "abc", "FOO_BAR": "abc", "FOO_BAR_BAZ": "abc"}
    )

    class SomeComponent:
        class Config:
            bad_key = Option(alternate_keys=["root:common"])

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config)

    # The key is invalid, so it tries the alternate keys
    assert comp.config("bad_key") == "common_abc"


def test_component_doc():
    config = ConfigManager.from_dict({"FOO_BAR": "bat"})

    class SomeComponent:
        class Config:
            foo_bar = Option(parser=int, doc="omg!")

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config)

    try:
        # This throws an exception becase "bat" is not an int
        comp.config("foo_bar")
    except Exception as exc:
        # We're going to lazily assert that omg! is in exc msg because if it
        # is, it came from the option and that's what we want to know.
        assert "omg!" in str(exc)


def test_component_raw_value():
    config = ConfigManager.from_dict({"FOO_BAR": "1"})

    class SomeComponent:
        class Config:
            foo_bar = Option(parser=int)

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config)

    assert comp.config("foo_bar") == 1
    assert comp.config("foo_bar", raw_value=True) == "1"

    class SomeComponent:
        class Config:
            bar = Option(parser=int)

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config.with_namespace("foo"))

    assert comp.config("bar") == 1
    assert comp.config("bar", raw_value=True) == "1"


class TestGetRuntimeConfig:
    def test_bound_config(self):
        config = ConfigManager.from_dict({"foo": 12345})

        class ComponentA:
            class Config:
                foo = Option(parser=int)
                bar = Option(parser=int, default="1")

            def __init__(self, config):
                self.config = config.with_options(self)

        comp = ComponentA(config)
        assert list(get_runtime_config(config, comp)) == [
            ([], "foo", "12345", Option(parser=int)),
            ([], "bar", "1", Option(parser=int, default="1")),
        ]

    def test_tree_with_specified_namespace(self):
        config = ConfigManager.from_dict({})

        class ComponentB:
            class Config:
                foo = Option(parser=int, default="2")
                bar = Option(parser=int, default="1")

            def __init__(self, config):
                self.config = config.with_options(self)

        class ComponentA:
            class Config:
                baz = Option(default="abc")

            def __init__(self, config):
                self.config = config.with_options(self)
                self.biff = ComponentB(config.with_namespace("biff"))

        comp = ComponentA(config)

        assert list(get_runtime_config(config, comp)) == [
            ([], "baz", "abc", Option(default="abc")),
            (["biff"], "foo", "2", Option(parser=int, default="2")),
            (["biff"], "bar", "1", Option(parser=int, default="1")),
        ]

    def test_tree_inferred_namespace(self):
        """Test get_runtime_config can pull namespace from config."""
        config = ConfigManager.from_dict({})

        class ComponentB:
            class Config:
                foo = Option(parser=int, default="2")
                bar = Option(parser=int, default="1")

            def __init__(self, config):
                self.config = config.with_options(self)

        class ComponentA:
            class Config:
                baz = Option(default="abc")

            def __init__(self, config):
                self.config = config.with_options(self)
                self.boff = ComponentB(config.with_namespace("boff"))

        comp = ComponentA(config)

        assert list(get_runtime_config(config, comp)) == [
            ([], "baz", "abc", Option(default="abc")),
            (["boff"], "foo", "2", Option(parser=int, default="2")),
            (["boff"], "bar", "1", Option(parser=int, default="1")),
        ]

    def test_slots(self):
        """Test get_runtime_config works with classes using slots."""
        config = ConfigManager.from_dict({})

        class Base:
            __slots__ = ("_slotattr",)

        class ComponentA(Base):
            class Config:
                key = Option(default="abc")

            def __init__(self, config_manager):
                self.config = config_manager.with_options(self)

        comp = ComponentA(config)

        assert list(get_runtime_config(config, comp)) == [
            ([], "key", "abc", Option(default="abc"))
        ]
