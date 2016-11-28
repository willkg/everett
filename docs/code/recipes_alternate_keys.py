from everett.component import RequiredConfigMixin, ConfigOptions
from everett.manager import ConfigManager


class DBReader(RequiredConfigMixin):
    required_config = ConfigOptions()
    required_config.add_option(
        'username',
        alternate_keys=['root:db_username']
    )
    required_config.add_option(
        'password',
        alternate_keys=['root:db_password']
    )

    def __init__(self, config):
        self.config = config.with_options(self)


class DBWriter(RequiredConfigMixin):
    required_config = ConfigOptions()
    required_config.add_option(
        'username',
        alternate_keys=['root:db_username']
    )
    required_config.add_option(
        'password',
        alternate_keys=['root:db_password']
    )

    def __init__(self, config):
        self.config = config.with_options(self)


# Define a shared configuration
config = ConfigManager.from_dict({
    'DB_USERNAME': 'foo',
    'DB_PASSWORD': 'bar'
})

reader = DBReader(config.with_namespace('reader'))
assert reader.config('username') == 'foo'
assert reader.config('password') == 'bar'

writer = DBWriter(config.with_namespace('writer'))
assert writer.config('username') == 'foo'
assert writer.config('password') == 'bar'


# Or define different credentials
config = ConfigManager.from_dict({
    'READER_USERNAME': 'joe',
    'READER_PASSWORD': 'foo',

    'WRITER_USERNAME': 'pete',
    'WRITER_PASSWORD': 'bar',
})

reader = DBReader(config.with_namespace('reader'))
assert reader.config('username') == 'joe'
assert reader.config('password') == 'foo'

writer = DBWriter(config.with_namespace('writer'))
assert writer.config('username') == 'pete'
assert writer.config('password') == 'bar'
