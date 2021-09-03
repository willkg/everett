# recipes_djangosettings.py

from everett.manager import ConfigManager


_config = ConfigManager.basic_config()


DEBUG = _config(
    "debug", parser=bool, default="False", doc="Whether or not DEBUG mode is enabled."
)
