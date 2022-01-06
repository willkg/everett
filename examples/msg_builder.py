# msg_builder.py

from everett.manager import ConfigManager, ConfigOSEnv


def build_msg_for_ini(namespace, key, parser, msg="", option_doc="", config_doc=""):
    namespace = namespace or ["main"]
    namespace = "_".join(namespace)

    return f"Dear user. {key} in section [{namespace}] is not correct. Please fix it."


config = ConfigManager(
    environments=[ConfigOSEnv()],
    msg_builder=build_msg_for_ini,
)

config("debug", default="false", parser=bool)
