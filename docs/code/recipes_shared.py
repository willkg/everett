import os

from everett.component import RequiredConfigMixin, ConfigOptions
from everett.manager import ConfigManager, parse_class


class App(RequiredConfigMixin):
    required_config = ConfigOptions()
    required_config.add_option(
        'basedir'
    )
    required_config.add_option(
        'reader',
        parser=parse_class
    )
    required_config.add_option(
        'writer',
        parser=parse_class
    )

    def __init__(self, config):
        self.config = config.with_options(self)

        self.basedir = self.config('basedir')
        self.reader = self.config('reader')(config, self.basedir)
        self.writer = self.config('writer')(config, self.basedir)


class FSReader(RequiredConfigMixin):
    required_config = ConfigOptions()
    required_config.add_option(
        'file_type',
        default='json'
    )

    def __init__(self, config, basedir):
        self.config = config.with_options(self)
        self.read_dir = os.path.join(basedir, 'read')


class FSWriter(RequiredConfigMixin):
    required_config = ConfigOptions()
    required_config.add_option(
        'file_type',
        default='json'
    )

    def __init__(self, config, basedir):
        self.config = config.with_options(self)
        self.write_dir = os.path.join(basedir, 'write')


config = ConfigManager.from_dict({
    'BASEDIR': '/tmp',
    'READER': '__main__.FSReader',
    'WRITER': '__main__.FSWriter',

    'READER_FILE_TYPE': 'json',

    'WRITER_FILE_TYPE': 'yaml'
})


app = App(config)
assert app.reader.read_dir == '/tmp/read'
assert app.writer.write_dir == '/tmp/write'
