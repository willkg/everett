# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os

from everett import NO_VALUE
from everett.ext.inifile import ConfigIniEnv


class TestConfigIniEnv:
    def test_basic_usage(self, datadir):
        ini_filename = os.path.join(datadir, "config_test.ini")
        cie = ConfigIniEnv([ini_filename])
        assert cie.get("foo") == "bar"
        assert cie.get("FOO") == "bar"
        assert cie.get("foo", namespace="nsbaz") == "bat"
        assert cie.get("foo", namespace=["nsbaz"]) == "bat"
        assert cie.get("foo", namespace=["nsbaz", "nsbaz2"]) == "bat2"

        cie = ConfigIniEnv(["/a/b/c/bogus/filename"])
        assert cie.get("foo") == NO_VALUE

    def test_multiple_files(self, datadir):
        ini_filename = os.path.join(datadir, "config_test.ini")
        ini_filename_original = os.path.join(datadir, "config_test_original.ini")
        cie = ConfigIniEnv([ini_filename, ini_filename_original])
        # Only the first found file is loaded, so foo_original does not exist
        assert cie.get("foo_original") == NO_VALUE
        cie = ConfigIniEnv([ini_filename_original])
        # ... but it is there if only the original is loaded (safety check)
        assert cie.get("foo_original") == "original"

    def test_does_not_parse_lists(self, datadir):
        ini_filename = os.path.join(datadir, "config_test.ini")
        cie = ConfigIniEnv([ini_filename])
        assert cie.get("bar") == "test1,test2"
