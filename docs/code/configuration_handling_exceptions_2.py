#!/usr/bin/env python2

import logging

from everett.manager import ConfigManager

logging.basicConfig()

config = ConfigManager.from_dict({
    'debug_mode': 'monkey'
})

try:
    some_val = config('debug_mode', parser=bool)
except Exception:
    # The "debug_mode" configuration value is probably
    # incorrect, but it could be something else--alert user
    # in the logs.
    logging.exception('gah!')
