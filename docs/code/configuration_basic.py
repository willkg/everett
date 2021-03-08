from everett.manager import ConfigManager


# basic_config() creates a ConfigManager that looks at a .env
# file and the process environment
config = ConfigManager.basic_config()

assert config("foo_var", default="bar") == "bar"
