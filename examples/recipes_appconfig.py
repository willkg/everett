import logging

from everett.manager import ConfigManager, Option


TEXT_TO_LOGGING_LEVEL = {
    "CRITICAL": 50,
    "ERROR": 40,
    "WARNING": 30,
    "INFO": 20,
    "DEBUG": 10,
}


def parse_loglevel(value):
    try:
        return TEXT_TO_LOGGING_LEVEL[value.upper()]
    except KeyError:
        raise ValueError(
            f'"{value}" is not a valid logging level. Try CRITICAL, ERROR, '
            "WARNING, INFO, DEBUG"
        )


class AppConfig:
    class Config:
        debug = Option(
            parser=bool,
            default="false",
            doc="Turns on debug mode for the application",
        )
        loglevel = Option(
            parser=parse_loglevel,
            default="INFO",
            doc=(
                "Log level for the application; CRITICAL, ERROR, WARNING, INFO, "
                "DEBUG"
            ),
        )


def init_app():
    manager = ConfigManager.from_dict({})
    config = manager.with_options(AppConfig())

    logging.basicConfig(level=config("loglevel"))

    if config("debug"):
        logging.info("debug mode!")


if __name__ == "__main__":
    init_app()
