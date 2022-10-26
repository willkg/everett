# recipes_djangosettings.py

from everett.manager import ConfigManager


_config = ConfigManager.basic_config()


DEBUG = _config(
    "debug", parser=bool, default="False", doc="Whether or not DEBUG mode is enabled."
)

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyMemcacheCache",
        "LOCATION": _config(
            "cache_location", default="127.0.0.1:11211", doc="Memcache cache location."
        ),
        "TIMEOUT": _config(
            "cache_timeout",
            default="500",
            parser=int,
            doc="Timeout to use when accessing cache.",
        ),
        "KEY_PREFIX": _config(
            "cache_key_prefix",
            default="socorro",
            doc="Key prefix to use for all cache keys.",
        ),
    }
}
