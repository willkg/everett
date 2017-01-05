# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from everett import ConfigurationError
from everett.component import (
    ConfigOptions,
    Option,
    RequiredConfigMixin,
)
from everett.manager import ConfigManager, ConfigDictEnv


def test_get_required_config():
    """Verify that get_required_config works for a trivial component"""
    class Component(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option('user', doc='no help')

        def __init__(self, config):
            self.config = config.with_options(self)

    required = Component.get_required_config()
    assert [op.key for op in required] == ['user']


def test_get_required_config_complex_mro():
    """Verify get_required_config with an MRO that has a diamond shape to it.

    The goal here is to make sure the C class has the right options from the
    right components and in the right order.

    """
    class ComponentBase(RequiredConfigMixin):
        def __init__(self, config):
            self.config = config.with_options(self)

    class A(ComponentBase):
        required_config = ConfigOptions()
        required_config.add_option('a', default='')

    class B(ComponentBase):
        required_config = ConfigOptions()
        required_config.add_option('b', default='')
        required_config.add_option('bd', default='')

    class C(B, A):
        required_config = ConfigOptions()
        # Note: This overrides B's b.
        required_config.add_option('b', default='')
        required_config.add_option('c', default='')

    required = C.get_required_config()
    assert [op.key for op in required] == [
        'a',   # From A
        'bd',  # From B
        'b',   # From C (overrides B's)
        'c'    # From C
    ]


def test_with_options():
    """Verify .with_options() restricts configuration"""
    config = ConfigManager([
        ConfigDictEnv({
            'FOO_BAR': 'a',
            'FOO_BAZ': 'b',

            'BAR': 'c',
            'BAZ': 'd',
        })
    ])

    class SomeComponent(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            'baz',
            default='',
            doc='some help here',
            parser=str
        )

        def __init__(self, config):
            self.config = config.with_options(self)

    # Create the component with regular config
    comp = SomeComponent(config)
    assert comp.config('baz') == 'd'
    with pytest.raises(ConfigurationError):
        # This is not a valid option for this component
        comp.config('bar')

    # Create the component with config in the "foo" namespace
    comp2 = SomeComponent(config.with_namespace('foo'))
    assert comp2.config('baz') == 'b'
    with pytest.raises(ConfigurationError):
        # This is not a valid option for this component
        comp2.config('bar')


def test_default_comes_from_options():
    """Verify that the default is picked up from options"""
    config = ConfigManager([])

    class SomeComponent(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            'foo',
            default='abc'
        )

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config)
    assert comp.config('foo') == 'abc'


def test_parser_comes_from_options():
    """Verify the parser is picked up from options"""
    config = ConfigManager([
        ConfigDictEnv({
            'FOO': '1'
        })
    ])

    class SomeComponent(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            'foo',
            parser=int
        )

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config)
    assert comp.config('foo') == 1


def test_get_namespace():
    config = ConfigManager.from_dict({
        'FOO': 'abc',
        'FOO_BAR': 'abc',
        'FOO_BAR_BAZ': 'abc',
    })
    assert config.get_namespace() == []

    class SomeComponent(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            'foo',
            parser=int
        )

        def __init__(self, config):
            self.config = config.with_options(self)

        def my_namespace_is(self):
            return self.config.get_namespace()

    comp = SomeComponent(config)
    assert comp.my_namespace_is() == []

    comp = SomeComponent(config.with_namespace('foo'))
    assert comp.my_namespace_is() == ['foo']


def test_alternate_keys():
    config = ConfigManager.from_dict({
        'COMMON': 'common_abc',
        'FOO': 'abc',
        'FOO_BAR': 'abc',
        'FOO_BAR_BAZ': 'abc',
    })

    class SomeComponent(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            'bad_key',
            alternate_keys=['root:common']
        )

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config)

    # The key is invalid, so it tries the alternate keys
    assert comp.config('bad_key') == 'common_abc'


def test_doc():
    config = ConfigManager.from_dict({
        'FOO_BAR': 'bat'
    })

    class SomeComponent(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            'foo_bar',
            parser=int,
            doc='omg!'
        )

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config)

    try:
        # This throws an exception becase "bat" is not an int
        comp.config('foo_bar')
    except Exception as exc:
        # We're going to lazily assert that omg! is in exc msg because if it
        # is, it came from the option and that's what we want to know.
        assert 'omg!' in str(exc)


def test_raw_value():
    config = ConfigManager.from_dict({
        'FOO_BAR': '1'
    })

    class SomeComponent(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option(
            'foo_bar',
            parser=int
        )

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config)

    assert comp.config('foo_bar') == 1
    assert comp.config('foo_bar', raw_value=True) == '1'

    class SomeComponent(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option('bar', parser=int)

        def __init__(self, config):
            self.config = config.with_options(self)

    comp = SomeComponent(config.with_namespace('foo'))

    assert comp.config('bar') == 1
    assert comp.config('bar', raw_value=True) == '1'


class TestRuntimeConfig:
    def test_no_self_config(self):
        class ComponentA(RequiredConfigMixin):
            required_config = ConfigOptions()
            required_config.add_option('bar', parser=int)

            def __init__(self):
                pass

        comp = ComponentA()
        assert list(comp.get_runtime_config()) == []

    def test_not_bound_config(self):
        class ComponentA(RequiredConfigMixin):
            required_config = ConfigOptions()
            required_config.add_option('bar', parser=int)

            def __init__(self):
                self.config = 'boo'

        comp = ComponentA()
        assert list(comp.get_runtime_config()) == []

    def test_bound_config(self):
        config = ConfigManager.from_dict({
            'foo': 12345
        })

        class ComponentA(RequiredConfigMixin):
            required_config = ConfigOptions()
            required_config.add_option('foo', parser=int)
            required_config.add_option('bar', parser=int, default='1')

            def __init__(self, config):
                self.config = config.with_options(self)

        comp = ComponentA(config)
        assert (
            list(comp.get_runtime_config()) ==
            [
                ([], 'foo', '12345', Option(key='foo', parser=int)),
                ([], 'bar', '1', Option(key='bar', parser=int, default='1')),
            ]
        )

    def test_tree(self):
        config = ConfigManager.from_dict({})

        class ComponentB(RequiredConfigMixin):
            required_config = ConfigOptions()
            required_config.add_option('foo', parser=int, default='2')
            required_config.add_option('bar', parser=int, default='1')

            def __init__(self, config):
                self.config = config.with_options(self)

        class ComponentA(RequiredConfigMixin):
            required_config = ConfigOptions()
            required_config.add_option('baz', default='abc')

            def __init__(self, config):
                self.config = config.with_options(self)
                self.comp = ComponentB(config.with_namespace('biff'))

            def get_runtime_config(self, namespace=None):
                for item in super(ComponentA, self).get_runtime_config(namespace):
                    yield item

                for item in self.comp.get_runtime_config(['biff']):
                    yield item

        comp = ComponentA(config)

        assert (
            list(comp.get_runtime_config()) ==
            [
                ([], 'baz', 'abc', Option(key='baz', default='abc')),
                (['biff'], 'foo', '2', Option(key='foo', parser=int, default='2')),
                (['biff'], 'bar', '1', Option(key='bar', parser=int, default='1')),
            ]
        )
