# component_appconfig.py

from everett.manager import ConfigManager, Option


# Central class holding configuration information
class AppConfig:
    class Config:
        debug = Option(
            parser=bool,
            default="false",
            doc="Switch debug mode on and off.",
        )


# Build a ConfigManger to look at the process environment for
# configuration and bound to the configuration options specified in
# AppConfig


def get_config():
    manager = ConfigManager.basic_config(
        doc="Check https://example.com/configuration for docs."
    )

    # Bind the configuration manager to the AppConfig component so that
    # it handles option properties like defaults, parsers, documentation,
    # and so on.
    return manager.with_options(AppConfig())


config = get_config()

debug = config("debug")
print(f"debug: {debug}")
