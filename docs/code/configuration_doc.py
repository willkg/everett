from everett.manager import ConfigManager, ConfigOSEnv


def main():
    config = ConfigManager(
        environments=[ConfigOSEnv()],
        doc="For configuration help, see https://example.com/configuration",
    )

    debug_mode = config(
        "debug",
        default="false",
        parser=bool,
        doc="True to put the app in debug mode. Don't use this in production!",
    )

    if debug_mode:
        print("Debug mode is on!")
    else:
        print("Debug mode off.")


if __name__ == "__main__":
    main()
