#!/usr/bin/env python3

import logging

from everett import InvalidValueError
from everett.manager import ConfigManager

logging.basicConfig()

config = ConfigManager.from_dict({"debug_mode": "monkey"})

try:
    some_val = config("debug_mode", parser=bool, doc="set debug mode")
except InvalidValueError:
    # The "debug_mode" configuration value is incorrect--alert
    # user in the logs.
    logging.exception("logged exception gah!")
