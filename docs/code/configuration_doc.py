from everett.manager import ConfigManager, ConfigOSEnv


config = ConfigManager(
    environments=[ConfigOSEnv()],
    doc='For configuration help, see https://example.com/configuration'
)
