import logging

from everett import InvalidValueError
from everett.manager import ConfigManager, ConfigDictEnv, qualname

logging.basicConfig()


def build_msg_for_ini(namespace, key, parser, msg="", option_doc="", config_doc=""):
    namespace = namespace or ["main"]
    namespace = "_".join(namespace)

    return (
        f"{key} in section [{namespace}] requires a value parseable by {qualname(parser)}\n"
        + f"{key} in [{namespace}] docs: {option_doc}\n"
        + f"Project docs: {config_doc}"
    )


config = ConfigManager(
    environments=[ConfigDictEnv({"debug": "lizard"})],
    msg_builder=build_msg_for_ini,
)

try:
    debug_mode = config(
        "debug",
        default="false",
        parser=bool,
        doc="Set DEBUG=True to put the app in debug mode. Don't use this in production!",
    )
except InvalidValueError:
    logging.exception("logged exception gah!")
