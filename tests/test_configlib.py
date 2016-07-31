# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

import mock
import pytest

from antenna.configlib import (
    config_override,
    ConfigDictEnv,
    ConfigIniEnv,
    ConfigOSEnv,
    ConfigManager,
    ConfigurationError,
    get_parser,
    parse_bool,
    parse_class,
    ListOf,
)


def test_parse_bool_error():
    with pytest.raises(ValueError):
        parse_bool('')


@pytest.mark.parametrize('data', [
    't',
    'true',
    'True',
    'TRUE',
    'y',
    'yes',
    'YES',
    '1',
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
    cde = ConfigDictEnv({'FOO': 'bar', 'NAMESPACE_FOO': 'baz'})
    assert cde.get('foo') == 'bar'
    assert cde.get('foo', namespace='namespace') == 'baz'


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
        assert cose.get('foo', namespace='namespace') == 'baz'
        os_environ_mock.__getitem__.assert_called_with('NAMESPACE_FOO')


def test_ConfigIniEnv(datadir):
    ini_filename = os.path.join(datadir, 'config_test.ini')
    cie = ConfigIniEnv(ini_filename)
    assert cie.get('foo') == 'bar'
    assert cie.get('foo', namespace='namespacebaz') == 'bat'


def test_config_ini_file_does_not_exist():
    with mock.patch('os.environ') as os_environ_mock:
        os_environ_mock.__contains__.return_value = True
        os_environ_mock.get.return_value = 'doesnotexist.ini'

        with pytest.raises(ConfigurationError):
            # Raises a configuration error because "doesnotexist.ini" is not a
            # file that exists.
            ConfigManager()


def test_config():
    config = ConfigManager()

    assert config('DOESNOTEXISTNOWAY', raise_error=False) is None
    with pytest.raises(ConfigurationError):
        config('DOESNOTEXISTNOWAY')
    with pytest.raises(ConfigurationError):
        config('DOESNOTEXISTNOWAY', raise_error=True)
    assert config('DOESNOTEXISTNOWAY', default='ohreally') == 'ohreally'


def test_config_override():
    config = ConfigManager()

    # Make sure the key doesn't exist
    assert config('DOESNOTEXISTNOWAY', raise_error=False) is None

    # Try one override
    with config_override(DOESNOTEXISTNOWAY='bar'):
        assert config('DOESNOTEXISTNOWAY') == 'bar'

    # Try nested overrides--innermost one rules supreme!
    with config_override(DOESNOTEXISTNOWAY='bar'):
        with config_override(DOESNOTEXISTNOWAY='bat'):
            assert config('DOESNOTEXISTNOWAY') == 'bat'


def test_default_must_be_string():
    config = ConfigManager()

    with pytest.raises(ConfigurationError):
        assert config('DOESNOTEXIST', default=True)
