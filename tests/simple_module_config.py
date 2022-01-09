"""Simple module config."""

from everett.manager import ConfigManager


HELP = "Help attribute value."


_config = ConfigManager.from_dict({"host": "localhost"})

HOST = _config(key="host", default="localhost", doc="The host.")
