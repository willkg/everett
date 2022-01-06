# namespaces.py

from everett.manager import ConfigManager


def open_connection(config):
    username = config("username")
    password = config("password")
    port = config("port", default="5432", parser=int)

    print(f"Opened database with {username}/{password} on port {port}")


config = ConfigManager.from_dict(
    {
        "DB_USERNAME": "admin",
        "DB_PASSWORD": "ou812",
    }
)

# Database configuration keys are all prefixed with "db", so we want to
# retrieve database configuration keys with the "db" namespace
db_config = config.with_namespace("db")

open_connection(db_config)
