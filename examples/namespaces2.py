# namespaces2.py

from everett.manager import ConfigManager


def open_connection(config):
    username = config("username")
    password = config("password")
    port = config("port", default="5432", parser=int)

    print(f"Opened database with {username}/{password} on port {port}")


config = ConfigManager.from_dict(
    {
        "SOURCE_DB_USERNAME": "admin",
        "SOURCE_DB_PASSWORD": "ou812",
        "DEST_DB_USERNAME": "admin",
        "DEST_DB_PASSWORD": "P9rwvnnj8CidECMb",
    }
)

# Database configuration keys are all prefixed with "db", so we want to
# retrieve database configuration keys with the "db" namespace
source_db_config = config.with_namespace("source_db")
dest_db_config = config.with_namespace("dest_db")

source_conn = open_connection(source_db_config)
dest_conn = open_connection(dest_db_config)
