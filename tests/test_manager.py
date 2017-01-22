# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import argparse
import os

import pytest
import six

from everett import (
    ConfigurationError,
    InvalidValueError,
    ConfigurationMissingError,
    NO_VALUE,
)
from everett.manager import (
    ConfigDictEnv,
    ConfigEnvFileEnv,
    ConfigIniEnv,
    ConfigManager,
    ConfigObjEnv,
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
    assert str(NO_VALUE) == 'NOVALUE'


def test_parse_bool_error():
    with pytest.raises(ValueError):
        parse_bool('')


@pytest.mark.parametrize('data,expected', [
    (None, []),
    ('', ['']),
    ([], []),
    ('foo', ['foo']),
    (['foo'], ['foo']),
    (['foo', 'bar'], ['foo', 'bar'])
])
def test_listify(data, expected):
    assert listify(data) == expected


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


def test_parse_bool_with_config():
    config = ConfigManager.from_dict({
        'foo': 'bar'
    })

    # Test key is there, but value is bad
    if six.PY3:
        with pytest.raises(InvalidValueError) as excinfo:
            config('foo', parser=bool)
    else:
        with pytest.raises(ValueError) as excinfo:
            config('foo', parser=bool)
    assert (
        str(excinfo.value) ==
        'ValueError: "bar" is not a valid bool value\n'
        'namespace=None key=foo requires a value parseable by everett.manager.parse_bool'
    )

    # Test key is not there and default is bad
    if six.PY3:
        with pytest.raises(InvalidValueError) as excinfo:
            config('phil', default='foo', parser=bool)
    else:
        with pytest.raises(ValueError) as excinfo:
            config('phil', default='foo', parser=bool)
    assert (
        str(excinfo.value) ==
        'ValueError: "foo" is not a valid bool value\n'
        'namespace=None key=phil requires a default value parseable by everett.manager.parse_bool'
    )


def test_parse_missing_class():
    with pytest.raises(ImportError):
        parse_class('doesnotexist.class')

    with pytest.raises(ValueError):
        parse_class('hashlib.doesnotexist')


def test_parse_class():
    from hashlib import md5
    assert parse_class('hashlib.md5') == md5


def test_parse_class_config():
    config = ConfigManager.from_dict({
        'foo_cls': 'hashlib.doesnotexist',
        'bar_cls': 'doesnotexist.class',
    })

    if six.PY3:
        with pytest.raises(InvalidValueError) as exc_info:
            config('foo_cls', parser=parse_class)
    else:
        with pytest.raises(ValueError) as exc_info:
            config('foo_cls', parser=parse_class)
    assert (
        str(exc_info.value) ==
        'ValueError: "doesnotexist" is not a valid member of hashlib\n'
        'namespace=None key=foo_cls requires a value parseable by everett.manager.parse_class'
    )

    if six.PY3:
        with pytest.raises(InvalidValueError) as exc_info:
            config('bar_cls', parser=parse_class)
    else:
        with pytest.raises(ImportError) as exc_info:
            config('bar_cls', parser=parse_class)
    assert (
        str(exc_info.value) in
        [
            # Python 2
            'ImportError: No module named doesnotexist\n'
            'namespace=None key=bar_cls requires a value parseable by everett.manager.parse_class',
            # Python 3
            'ImportError: No module named \'doesnotexist\'\n'
            'namespace=None key=bar_cls requires a value parseable by everett.manager.parse_class',
            # Python 3.6
            'ModuleNotFoundError: No module named \'doesnotexist\'\n'
            'namespace=None key=bar_cls requires a value parseable by everett.manager.parse_class'
        ]
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
    assert ListOf(str)('') == []
    assert ListOf(str)('foo') == ['foo']
    assert ListOf(bool)('t,f') == [True, False]
    assert ListOf(int)('1,2,3') == [1, 2, 3]
    assert ListOf(int, delimiter=':')('1:2') == [1, 2]


def test_ListOf_error():
    config = ConfigManager.from_dict({
        'bools': 't,f,badbool'
    })
    if six.PY3:
        with pytest.raises(InvalidValueError) as exc_info:
            config('bools', parser=ListOf(bool))
    else:
        with pytest.raises(ValueError) as exc_info:
            config('bools', parser=ListOf(bool))

    assert (
        str(exc_info.value) ==
        'ValueError: "badbool" is not a valid bool value\n'
        'namespace=None key=bools requires a value parseable by <ListOf(bool)>'
    )


class TestConfigObjEnv:
    def test_basic(self):
        class Namespace(object):
            pass

        obj = Namespace()
        setattr(obj, 'foo', 'bar')
        setattr(obj, 'foo_baz', 'bar')

        coe = ConfigObjEnv(obj)
        assert coe.get('foo') == 'bar'
        assert coe.get('FOO') == 'bar'
        assert coe.get('FOO_BAZ') == 'bar'

    def test_with_argparse(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--debug', help='to debug or not to debug'
        )
        parsed_vals = parser.parse_known_args([])[0]

        config = ConfigManager([
            ConfigObjEnv(parsed_vals)
        ])

        assert config('debug', parser=bool, raise_error=False) is NO_VALUE

        parsed_vals = parser.parse_known_args(['--debug=y'])[0]

        config = ConfigManager([
            ConfigObjEnv(parsed_vals)
        ])

        assert config('debug', parser=bool) is True

    def test_with_argparse_actions(self):
        parser = argparse.ArgumentParser()
        parser.add_argument(
            '--debug', help='to debug or not to debug', action='store_true'
        )
        parsed_vals = parser.parse_known_args([])[0]

        config = ConfigManager([
            ConfigObjEnv(parsed_vals)
        ])

        # What happens is that argparse doesn't see an arg, so saves
        # debug=False. ConfigObjEnv converts that to "False". That gets parsed
        # as False by the Everett parse_bool function. That's kind of
        # roundabout but "works" for some/most cases.
        assert config('debug', parser=bool) is False

        parsed_vals = parser.parse_known_args(['--debug'])[0]

        config = ConfigManager([
            ConfigObjEnv(parsed_vals)
        ])

        assert config('debug', parser=bool) is True


def test_ConfigDictEnv():
    cde = ConfigDictEnv({
        'FOO': 'bar',
        'A_FOO': 'a_bar',
        'A_B_FOO': 'a_b_bar',
        'lower_foo': 'bar'
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
    os.environ['EVERETT_TEST_FOO'] = 'bar'
    os.environ['EVERETT_TEST_FOO'] = 'bar'
    cose = ConfigOSEnv()

    assert cose.get('everett_test_foo') == 'bar'
    assert cose.get('EVERETT_test_foo') == 'bar'
    assert cose.get('foo', namespace=['everett', 'test']) == 'bar'


def test_ConfigIniEnv(datadir):
    ini_filename = os.path.join(datadir, 'config_test.ini')
    cie = ConfigIniEnv([ini_filename])
    assert cie.get('foo') == 'bar'
    assert cie.get('FOO') == 'bar'
    assert cie.get('foo', namespace='nsbaz') == 'bat'
    assert cie.get('foo', namespace=['nsbaz']) == 'bat'
    assert cie.get('foo', namespace=['nsbaz', 'nsbaz2']) == 'bat2'

    cie = ConfigIniEnv(['/a/b/c/bogus/filename'])
    assert cie.get('foo') == NO_VALUE


def test_ConfigEnvFileEnv(datadir):
    env_filename = os.path.join(datadir, '.env')
    cefe = ConfigEnvFileEnv(['/does/not/exist/.env', env_filename])
    assert cefe.get('not_a', namespace='youre') == 'golfer'
    assert cefe.get('loglevel') == 'walter'
    assert cefe.get('LOGLEVEL') == 'walter'
    assert cefe.get('missing') is NO_VALUE
    assert cefe.data == {
        'LOGLEVEL': 'walter',
        'DEBUG': 'True',
        'YOURE_NOT_A': 'golfer',
        'DATABASE_URL': 'sqlite:///kahlua.db',
    }

    cefe = ConfigEnvFileEnv(env_filename)
    assert cefe.get('not_a', namespace='youre') == 'golfer'

    cefe = ConfigEnvFileEnv('/does/not/exist/.env')
    assert cefe.get('loglevel') is NO_VALUE


def test_parse_env_file():
    assert parse_env_file(['PLAN9=outerspace']) == {'PLAN9': 'outerspace'}
    with pytest.raises(ConfigurationError) as exc_info:
        parse_env_file(['3AMIGOS=infamous'])
    assert (
        str(exc_info.value) ==
        'Invalid variable name "3AMIGOS" in env file (line 1)'
    )
    with pytest.raises(ConfigurationError) as exc_info:
        parse_env_file(['INVALID-CHAR=value'])
    assert (
        str(exc_info.value) ==
        'Invalid variable name "INVALID-CHAR" in env file (line 1)'
    )
    with pytest.raises(ConfigurationError) as exc_info:
        parse_env_file(['', 'MISSING-equals'])
    assert (
        str(exc_info.value) ==
        'Env file line missing = operator (line 2)'
    )


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

    # Don't raise an error and no default yields NO_VALUE
    assert config('DOESNOTEXISTNOWAY', raise_error=False) is NO_VALUE

    # Defaults to raising an error
    with pytest.raises(ConfigurationMissingError) as exc_info:
        config('DOESNOTEXISTNOWAY')
    assert (
        str(exc_info.value) ==
        'namespace=None key=DOESNOTEXISTNOWAY requires a value parseable by str'
    )

    # Raises an error if raise_error is True
    with pytest.raises(ConfigurationMissingError) as exc_info:
        config('DOESNOTEXISTNOWAY', raise_error=True)
    assert (
        str(exc_info.value) ==
        'namespace=None key=DOESNOTEXISTNOWAY requires a value parseable by str'
    )

    # With a default, returns the default
    assert config('DOESNOTEXISTNOWAY', default='ohreally') == 'ohreally'

    # Test doc
    with pytest.raises(ConfigurationMissingError) as exc_info:
        config('DOESNOTEXISTNOWAY', doc='Nothing to see here.')
    assert (
        str(exc_info.value) ==
        'namespace=None key=DOESNOTEXISTNOWAY requires a value parseable by str\n'
        'Nothing to see here.'
    )


def test_config_from_dict():
    config = ConfigManager.from_dict({})

    assert config('FOO', raise_error=False) is NO_VALUE

    config = ConfigManager.from_dict({
        'FOO': 'bar'
    })

    assert config('FOO', raise_error=False) == 'bar'


def test_config_manager_doc():
    config = ConfigManager(
        [
            ConfigDictEnv({'foo': 'bar'}),
        ],
        doc='See http://example.com/configuration'
    )

    # Test ConfigManager doc shows up
    if six.PY3:
        with pytest.raises(ConfigurationError) as exc_info:
            config('foo', parser=int)
    else:
        with pytest.raises(ValueError) as exc_info:
            config('foo', parser=int)
    assert(
        str(exc_info.value) ==
        'ValueError: invalid literal for int() with base 10: \'bar\'\n'
        'namespace=None key=foo requires a value parseable by int\n'
        'See http://example.com/configuration'
    )

    # Test config doc and ConfigManager doc show up
    if six.PY3:
        with pytest.raises(ConfigurationError) as exc_info:
            config('foo', parser=int, doc='Port to listen on.')
    else:
        with pytest.raises(ValueError) as exc_info:
            config('foo', parser=int, doc='Port to listen on.')
    assert(
        str(exc_info.value) ==
        'ValueError: invalid literal for int() with base 10: \'bar\'\n'
        'namespace=None key=foo requires a value parseable by int\n'
        'Port to listen on.\n'
        'See http://example.com/configuration'
    )


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


def test_raw_value():
    config = ConfigManager.from_dict({
        'FOO_BAR': '1'
    })
    assert config('FOO_BAR', parser=int) == 1
    assert config('FOO_BAR', parser=int, raw_value=True) == '1'

    assert str(config('NOEXIST', parser=int, raise_error=False)) == 'NOVALUE'

    config = config.with_namespace('FOO')
    assert config('BAR', parser=int) == 1
    assert config('BAR', parser=int, raw_value=True) == '1'
