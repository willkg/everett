# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


__author__ = 'Will Kahn-Greene'
__email__ = 'willkg@mozilla.com'

# yyyymmdd
__releasedate__ = '20190107'
# x.y.z or x.y.z.dev0
__version__ = '1.0.0'


# NoValue instances are always false
class NoValue(object):
    def __nonzero__(self):
        return False

    def __bool__(self):
        return False

    def __repr__(self):
        return 'NO_VALUE'


# Singleton indicating a non-value
NO_VALUE = NoValue()


class ConfigurationError(Exception):
    """Configuration error base class"""
    pass


class InvalidKeyError(ConfigurationError):
    """Indicates the key is not valid for this component"""
    pass


class DetailedConfigurationError(ConfigurationError):
    """Base class for configuration errors that have a msg, namespace, key, and parser"""
    def __init__(self, *args, **kwargs):
        self.namespace = args[1]
        self.key = args[2]
        self.parser = args[3]
        super(DetailedConfigurationError, self).__init__(*args, **kwargs)

    def __str__(self):
        return self.args[0]


class ConfigurationMissingError(DetailedConfigurationError):
    """Indicates that required configuration is missing"""
    pass


class InvalidValueError(DetailedConfigurationError):
    """Indicates that the value is not valid"""
    pass
