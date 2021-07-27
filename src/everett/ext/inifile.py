# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Holds the ConfigIniEnv environment.

To use this, you must install the optional requirements::

    $ pip install 'everett[ini]'

"""

import logging
import os
from typing import Dict, List, Optional, Union

from configobj import ConfigObj

from everett import NO_VALUE, NoValue
from everett.manager import generate_uppercase_key, get_key_from_envs, listify


logger = logging.getLogger("everett")


class ConfigIniEnv:
    """Source for pulling configuration from INI files.

    This requires optional dependencies. You can install them with::

        $ pip install 'everett[ini]'

    Takes a path or list of possible paths to look for a INI file. It uses
    the first INI file it can find.

    If it finds no INI files in the possible paths, then this configuration
    source will be a no-op.

    This will expand ``~`` as well as work relative to the current working
    directory.

    This example looks just for the INI file specified in the environment::

        from everett.manager import ConfigManager
        from everett.ext.inifile import ConfigIniEnv

        config = ConfigManager([
            ConfigIniEnv(possible_paths=os.environ.get("FOO_INI"))
        ])


    If there's no ``FOO_INI`` in the environment, then the path will be
    ignored.

    Here's an example that looks for the INI file specified in the environment
    variable ``FOO_INI`` and failing that will look for ``.antenna.ini`` in the
    user's home directory::

        from everett.manager import ConfigManager
        from everett.ext.inifile import ConfigIniEnv

        config = ConfigManager([
            ConfigIniEnv(
                possible_paths=[
                    os.environ.get("FOO_INI"),
                    "~/.antenna.ini"
                ]
            )
        ])


    This example looks for a ``config/local.ini`` file which overrides values
    in a ``config/base.ini`` file both are relative to the current working
    directory::

        from everett.manager import ConfigManager
        from everett.ext.inifile import ConfigIniEnv

        config = ConfigManager([
            ConfigIniEnv(possible_paths="config/local.ini"),
            ConfigIniEnv(possible_paths="config/base.ini")
        ])


    Note how you can have multiple ``ConfigIniEnv`` files and this is how you
    can set Everett up to have values in one INI file override values in
    another INI file.

    INI files must have a "main" section. This is where keys that aren't in a
    namespace are placed.

    Minimal INI file::

        [main]


    In the INI file, namespace is a section. So key "user" in namespace "foo"
    is::

        [foo]
        user=someval


    Everett uses configobj, so it supports nested sections like this::

        [main]
        foo=bar

        [namespace]
        foo2=bar2

          [[namespace2]]
          foo3=bar3


    Which gives you these:

    * ``FOO``
    * ``NAMESPACE_FOO2``
    * ``NAMESPACE_NAMESPACE2_FOO3``

    See more details here:
    http://configobj.readthedocs.io/en/latest/configobj.html#the-config-file-format

    """

    def __init__(self, possible_paths: Union[str, List[str]]) -> None:
        """
        :param possible_paths: either a single string with a file path (e.g.
            ``"/etc/project.ini"`` or a list of strings with file paths

        """
        self.cfg = {}
        self.path = None
        possible_paths = listify(possible_paths)

        for path in possible_paths:
            if not path:
                continue

            path = os.path.abspath(os.path.expanduser(path.strip()))
            if path and os.path.isfile(path):
                self.path = path
                self.cfg.update(self.parse_ini_file(path))
                break

        if not self.path:
            logger.debug("No INI file found: %s", possible_paths)

    def parse_ini_file(self, path: str) -> Dict:
        """Parse ini file at ``path`` and return dict."""
        cfgobj = ConfigObj(path, list_values=False)

        def extract_section(namespace: List[str], d: Dict) -> Dict:
            cfg = {}
            for key, val in d.items():
                if isinstance(d[key], dict):
                    cfg.update(extract_section(namespace + [key], d[key]))
                else:
                    cfg["_".join(namespace + [key]).upper()] = val

            return cfg

        return extract_section([], cfgobj.dict())

    def get(
        self, key: str, namespace: Optional[List[str]] = None
    ) -> Union[str, NoValue]:
        """Retrieve value for key."""
        if not self.path:
            return NO_VALUE

        # NOTE(willkg): The "main" section is considered the root mainspace.
        namespace = namespace or ["main"]
        logger.debug("Searching %r for key: %s, namespace: %s", self, key, namespace)
        full_key = generate_uppercase_key(key, namespace)
        return get_key_from_envs(self.cfg, full_key)

    def __repr__(self) -> str:
        return "<ConfigIniEnv: %s>" % self.path
