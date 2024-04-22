# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.


"""Everett is a Python library for configuration."""

from importlib.metadata import (
    version as importlib_version,
    PackageNotFoundError,
)
from typing import Callable, List, Union


try:
    __version__ = importlib_version("everett")
except PackageNotFoundError:
    __version__ = "unknown"


__all__ = [
    "NO_VALUE",
    "ConfigurationError",
    "DetailedConfigurationError",
    "InvalidKeyError",
    "ConfigurationMissingError",
]


# NoValue instances are always false
class NoValue:
    def __nonzero__(self) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "NO_VALUE"


#: Singleton indicating a non-value.
NO_VALUE = NoValue()


class ConfigurationError(Exception):
    """Configuration error base class."""

    pass


class InvalidKeyError(ConfigurationError):
    """Error that indicates the key is not valid for this component."""

    pass


class DetailedConfigurationError(ConfigurationError):
    """Base class for configuration errors that have a msg, namespace, key, and parser."""

    def __init__(
        self, msg: str, namespace: Union[List[str], None], key: str, parser: Callable
    ):
        self.msg = msg
        self.namespace = namespace
        self.key = key
        self.parser = parser
        super().__init__(msg, namespace, key, parser)

    def __str__(self) -> str:
        return self.msg


class ConfigurationMissingError(DetailedConfigurationError):
    """Error that indicates that required configuration is missing."""

    pass


class InvalidValueError(DetailedConfigurationError):
    """Error that indicates that the value is not valid."""

    pass
