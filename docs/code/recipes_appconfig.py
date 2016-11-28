import logging

from everett.component import ConfigOptions, RequiredConfigMixin
from everett.manager import ConfigManager


def parse_loglevel(value):
    text_to_level = {
        'CRITICAL': 50,
        'ERROR': 40,
        'WARNING': 30,
        'INFO': 20,
        'DEBUG': 10
    }
    try:
        return text_to_level[value.upper()]
    except KeyError:
        raise ValueError(
            '"%s" is not a valid logging level. Try CRITICAL, ERROR, '
            'WARNING, INFO, DEBUG' % value
        )


class AppConfig(RequiredConfigMixin):
    required_config = ConfigOptions()
    required_config.add_option(
        'debug',
        parser=bool,
        default='false',
        doc='Turns on debug mode for the applciation'
    )
    required_config.add_option(
        'loglevel',
        parser=parse_loglevel,
        default='INFO',
        doc='Log level for the application'
    )

    def __init__(self, config):
        self.raw_config = config
        self.config = config.with_options(self)

    def __call__(self, *args, **kwargs):
        return self.config(*args, **kwargs)


def init_app():
    config = ConfigManager.from_dict({})
    app_config = AppConfig(config)

    logging.basicConfig(loglevel=app_config('loglevel'))

    if app_config('debug'):
        logging.info('debug mode!')


if __name__ == '__main__':
    init_app()
