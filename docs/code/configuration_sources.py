import os
from everett.ext.inifile import ConfigIniEnv
from everett.manager import ConfigDictEnv, ConfigManager, ConfigOSEnv

config = ConfigManager(
    [
        # Pull from the OS environment first
        ConfigOSEnv(),
        # Fall back to the file specified by the FOO_INI OS environment
        # variable if such file exists
        ConfigIniEnv(os.environ.get("FOO_INI")),
        # Fall back to this dict of defaults
        ConfigDictEnv({"FOO_VAR": "bar"}),
    ]
)

assert config("foo_var") == "bar"
