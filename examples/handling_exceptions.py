# handling_exceptions.py

import logging

from everett import InvalidValueError
from everett.manager import ConfigManager

logging.basicConfig()

config = ConfigManager.from_dict({"debug_mode": "monkey"})

try:
    some_val = config("debug_mode", parser=bool, doc="set debug mode")
except InvalidValueError:
    print("I'm sorry dear user, but DEBUG_MODE must be 'true' or 'false'.")
