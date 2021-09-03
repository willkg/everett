"""Basic module config."""

from everett.manager import ConfigManager


_config = ConfigManager.from_dict(
    {"debug": "False", "logging_level": "INFO", "password": "pwd", "fun": "0.0"}
)


def parse_logging_level(s: str) -> str:
    if s not in ("CRITICAL", "WARNING", "INFO", "ERROR"):
        raise ValueError("invalid logging level value")
    return s


DEBUG = _config(key="debug", parser=bool, default="False", doc="Debug mode.")

LOGGING_LEVEL = _config(key="logging_level", parser=parse_logging_level, doc="Level.")

PASSWORD = _config(key="password", doc="Password field.\n\nMust be provided.")

FUN = _config(key="fun", parser=(int if 0 else float), doc="Woah.")
