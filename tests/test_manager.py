# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import mock
import pytest

from everett import NO_VALUE, ConfigurationError
from everett.manager import (
    ConfigDictEnv,
    ConfigEnvFileEnv,
    ConfigIniEnv,
    ConfigManager,
    ConfigOSEnv,
    ListOf,
    config_override,
    get_key_from_envs,
    get_parser,
    listify,
    parse_bool,
    parse_class,
    parse_env_file,
)


def test_no_value():
    assert bool(NO_VALUE) is False
    assert NO_VALUE is not True


def test_parse_bool_error():
    with pytest.raises(ValueError):
        parse_bool('')


def test_listify():
    assert listify('foo') == ['foo']
    assert listify('') == ['']

    assert listify([]) == []
    assert listify(['foo']) == ['foo']
    assert listify(['foo', 'bar']) == ['foo', 'bar']


@pytest.mark.parametrize('data', [
    't',
    'true',
    'True',
    'TRUE',
    'y',
    'yes',
    'YES',
    '1',
    'on',
    'On',
    'ON',
])
def test_parse_bool_true(data):
    assert parse_bool(data) is True


@pytest.mark.parametrize('data', [
    'f',
    'false',
    'False',
    'FALSE',
    'n',
    'no',
    'No',
    'NO',
    '0',
    'off',
    'Off',
    'OFF',
])
def test_parse_bool_false(data):
    assert parse_bool(data) is False


def test_parse_missing_class():
    with pytest.raises(ImportError):
        parse_class('doesnotexist.class')

    with pytest.raises(ValueError):
        parse_class('hashlib.doesnotexist')


def test_parse_class():
    from hashlib import md5
    assert parse_class('hashlib.md5') == md5


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
    assert ListOf(str)('foo') == ['foo']
    assert ListOf(bool)('t,f') == [True, False]
    assert ListOf(int)('1,2,3') == [1, 2, 3]
    assert ListOf(int, delimiter=':')('1:2') == [1, 2]


def test_ConfigDictEnv():
    cde = ConfigDictEnv({
        'FOO': 'bar',
        'A_FOO': 'a_bar',
        'A_B_FOO': 'a_b_bar',
    })
    assert cde.get('foo') == 'bar'
    assert cde.get('foo', namespace=['a']) == 'a_bar'
    assert cde.get('foo', namespace=['a', 'b']) == 'a_b_bar'
    assert cde.get('FOO', namespace=['a']) == 'a_bar'
    assert cde.get('foo', namespace=['A']) == 'a_bar'
    assert cde.get('FOO', namespace=['A']) == 'a_bar'

    cde = ConfigDictEnv({
        'foo': 'bar',
    })
    assert cde.get('foo') == 'bar'
    assert cde.get('FOO') == 'bar'


def test_ConfigOSEnv():
    with mock.patch('os.environ') as os_environ_mock:
        os_environ_mock.__contains__.return_value = True
        os_environ_mock.__getitem__.return_value = 'baz'
        cose = ConfigOSEnv()
        assert cose.get('foo') == 'baz'
        os_environ_mock.__getitem__.assert_called_with('FOO')

    with mock.patch('os.environ') as os_environ_mock:
        os_environ_mock.__contains__.return_value = True
        os_environ_mock.__getitem__.return_value = 'baz'
        cose = ConfigOSEnv()
        assert cose.get('foo', namespace=['a']) == 'baz'
        os_environ_mock.__getitem__.assert_called_with('A_FOO')
    # FIXME: add multi-tier namespace


def test_ConfigIniEnv(datadir):
    ini_filename = os.path.join(datadir, 'config_test.ini')
    cie = ConfigIniEnv([ini_filename])
    assert cie.get('foo') == 'bar'
    assert cie.get('foo', namespace='namespacebaz') == 'bat'
    # FIXME: Add multi-tier namespace

    cie = ConfigIniEnv(['/a/b/c/bogus/filename'])
    assert cie.get('foo') == NO_VALUE


def test_ConfigEnvFileEnv(datadir):
    env_filename = os.path.join(datadir, '.env')
    cefe = ConfigEnvFileEnv(['/does/not/exist/.env', env_filename])
    assert cefe.get('not_a', namespace='youre') == 'golfer'
    assert cefe.get('loglevel') == 'walter'
    assert cefe.get('missing') is NO_VALUE
    assert cefe.data == {
        'LOGLEVEL': 'walter',
        'DEBUG': 'True',
        'YOURE_NOT_A': 'golfer',
        'DATABASE_URL': 'sqlite:///kahlua.db',
    }

    cefe = ConfigEnvFileEnv('/does/not/exist/.env')
    assert cefe.get('loglevel') is NO_VALUE


def test_parse_env_file():
    assert parse_env_file(['PLAN9=outerspace']) == {'PLAN9': 'outerspace'}
    with pytest.raises(ConfigurationError):
        parse_env_file(['3AMIGOS=infamous'])
    with pytest.raises(ConfigurationError):
        parse_env_file(['INVALID-CHAR=value'])
    with pytest.raises(ConfigurationError):
        parse_env_file(['MISSING-equals'])


def test_get_key_from_envs():
    assert get_key_from_envs({'K': 'v'}, 'k') == 'v'
    assert get_key_from_envs([{'K': 'v'},
                              {'L': 'w'}], 'l') == 'w'
    assert get_key_from_envs({'T_T': 'sad'},
                             't', namespace='t') == 'sad'
    assert get_key_from_envs({'O_A_O': 'strange'},
                             'o', namespace=['o', 'a']) == 'strange'
    assert get_key_from_envs({'K': 'v'}, 'q') is NO_VALUE
    # first match wins
    assert get_key_from_envs([
        {'K': 'v'},
        {'L': 'w'},
        {'K': 'z'},
    ], 'k') == 'v'
    # works with reversed iterator
    assert get_key_from_envs(reversed([
        {'L': 'v'}, {'L': 'w'},
    ]), 'l') == 'w'
    # works with os.environ
    os.environ['DUDE_ABIDES'] = 'yeah, man'
    assert get_key_from_envs(os.environ,
                             'abides', namespace='dude') == 'yeah, man'


def test_config():
    config = ConfigManager([])

    assert config('DOESNOTEXISTNOWAY', raise_error=False) is NO_VALUE
    with pytest.raises(ConfigurationError):
        config('DOESNOTEXISTNOWAY')
    with pytest.raises(ConfigurationError):
        config('DOESNOTEXISTNOWAY', raise_error=True)
    assert config('DOESNOTEXISTNOWAY', default='ohreally') == 'ohreally'


def test_config_from_dict():
    config = ConfigManager.from_dict({})

    assert config('FOO', raise_error=False) is NO_VALUE

    config = ConfigManager.from_dict({
        'FOO': 'bar'
    })

    assert config('FOO', raise_error=False) == 'bar'


def test_config_override():
    config = ConfigManager([])

    # Make sure the key doesn't exist
    assert config('DOESNOTEXISTNOWAY', raise_error=False) is NO_VALUE

    # Try one override
    with config_override(DOESNOTEXISTNOWAY='bar'):
        assert config('DOESNOTEXISTNOWAY') == 'bar'

    # Try nested overrides--innermost one rules supreme!
    with config_override(DOESNOTEXISTNOWAY='bar'):
        with config_override(DOESNOTEXISTNOWAY='bat'):
            assert config('DOESNOTEXISTNOWAY') == 'bat'


def test_default_must_be_string():
    config = ConfigManager([])

    with pytest.raises(ConfigurationError):
        assert config('DOESNOTEXIST', default=True)


def test_with_namespace():
    config = ConfigManager([
        ConfigDictEnv({
            'FOO_BAR': 'foobaz',
            'BAR': 'baz',
            'BAT': 'bat',
        })
    ])

    # Verify the values first
    assert config('bar', namespace=['foo']) == 'foobaz'
    assert config('bar') == 'baz'
    assert config('bat') == 'bat'

    # Create the namespaced config
    config_with_namespace = config.with_namespace('foo')
    assert config_with_namespace('bar') == 'foobaz'

    # Verify 'bat' is not available because it's not in the namespace
    with pytest.raises(ConfigurationError):
        config_with_namespace('bat')


def test_get_namespace():
    config = ConfigManager.from_dict({
        'FOO': 'abc',
        'FOO_BAR': 'abc',
        'FOO_BAR_BAZ': 'abc',
    })
    assert config.get_namespace() == []

    ns_foo_config = config.with_namespace('foo')
    assert ns_foo_config.get_namespace() == ['foo']

    ns_foo_bar_config = ns_foo_config.with_namespace('bar')
    assert ns_foo_bar_config.get_namespace() == ['foo', 'bar']


@pytest.mark.parametrize('key,alternate_keys,expected', [
    # key, alternate keys, expected
    ('FOO', [], 'foo_abc'),
    ('FOO', ['FOO_BAR'], 'foo_abc'),
    ('BAD_KEY', ['FOO_BAR'], 'foo_bar_abc'),
    ('BAD_KEY', ['BAD_KEY1', 'BAD_KEY2', 'FOO_BAR_BAZ'], 'foo_bar_baz_abc'),
])
def test_alternate_keys(key, alternate_keys, expected):
    config = ConfigManager.from_dict({
        'FOO': 'foo_abc',
        'FOO_BAR': 'foo_bar_abc',
        'FOO_BAR_BAZ': 'foo_bar_baz_abc',
    })

    assert config(key, alternate_keys=alternate_keys) == expected


@pytest.mark.parametrize('key,alternate_keys,expected', [
    # key, alternate keys, expected
    ('BAR', [], 'foo_bar_abc'),
    ('BAD_KEY', ['BAD_KEY1', 'BAR_BAZ'], 'foo_bar_baz_abc'),
    ('bad_key', ['bad_key1', 'bar_baz'], 'foo_bar_baz_abc'),
    ('bad_key', ['root:common_foo'], 'common_foo_abc')
])
def test_alternate_keys_with_namespace(key, alternate_keys, expected):
    config = ConfigManager.from_dict({
        'COMMON_FOO': 'common_foo_abc',
        'FOO': 'foo_abc',
        'FOO_BAR': 'foo_bar_abc',
        'FOO_BAR_BAZ': 'foo_bar_baz_abc',
    })

    config = config.with_namespace('FOO')

    assert config(key, alternate_keys=alternate_keys) == expected
