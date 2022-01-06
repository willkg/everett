# myserver.py

"""
Minimal example showing how to use configuration for a web app.
"""

from everett.manager import ConfigManager

config = ConfigManager.basic_config(
    doc="Check https://example.com/configuration for documentation."
)

host = config("host", default="localhost")
port = config("port", default="8000", parser=int)
debug_mode = config(
    "debug",
    default="False",
    parser=bool,
    doc="Set to True for debugmode; False for regular mode",
)

print(f"host: {host}")
print(f"port: {port}")
print(f"debug_mode: {debug_mode}")
