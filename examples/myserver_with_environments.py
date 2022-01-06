# myserver_with_environments.py

"""
Minimal example showing how to use configuration for a web app that pulls
configuration from specified environments.
"""

import os
from everett.ext.inifile import ConfigIniEnv
from everett.manager import ConfigManager, ConfigOSEnv, ConfigDictEnv

config = ConfigManager(
    [
        # Pull from the OS environment first
        ConfigOSEnv(),
        # Fall back to the file specified by the FOO_INI OS environment
        # variable if such file exists
        ConfigIniEnv(os.environ.get("FOO_INI")),
        # Fall back to this dict of defaults
        ConfigDictEnv({"FOO_VAR": "bar"}),
    ],
    doc="Check https://example.com/configuration for documentation.",
)

host = config("host", default="localhost")
port = config("port", default="8000", parser=int)
debug_mode = config(
    "debug",
    default="False",
    parser=bool,
    doc="Set to True for debugmode; False for regular mode",
)

print(f"host: {host}")
print(f"port: {port}")
print(f"debug_mode: {debug_mode}")
