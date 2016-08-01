# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from configmanlite import NO_VALUE, ConfigurationError
from configmanlite.component import (
    RequiredConfigMixin,
    ConfigOptions,
)
from configmanlite.manager import ConfigManager, ConfigDictEnv


def test_get_required_config():
    class Component(RequiredConfigMixin):
        required_config = ConfigOptions()
        required_config.add_option('user', doc='no help')

        def __init__(self, config):
            self.config = config.with_options(self)

    required = Component.get_required_config()
    assert [op.key for op in required] == ['user']


def test_get_required_config_complex_mro():
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


# FIXME: test .with_options


# FIXME: test config() call picks up default and parsing correctly
