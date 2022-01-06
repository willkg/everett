# testdebug.py

"""
Minimal example showing how to override configuration values when testing.
"""

import unittest

from everett.manager import ConfigManager, config_override


class App:
    def __init__(self):
        config = ConfigManager.basic_config()
        self.debug = config("debug", default="False", parser=bool)


class TestDebug(unittest.TestCase):
    def test_debug_on(self):
        with config_override(DEBUG="on"):
            app = App()
            self.assertTrue(app.debug)

    def test_debug_off(self):
        with config_override(DEBUG="off"):
            app = App()
            self.assertFalse(app.debug)


if __name__ == "__main__":
    unittest.main()
