# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import pytest

from everett import NO_VALUE, ConfigurationError
from everett.ext.yamlfile import ConfigYamlEnv


YAML_FLAT = """\
foo: "bar"
bar: "test1,test2"
nsbaz_foo: "bat"
nsbaz_nsbaz2_foo: "bat2"
"""

YAML_FLAT_2 = """\
foo_original: "original"
"""

YAML_FLAT_CASE = """\
FOO: "bar"
NSBAZ_Foo: "bat"
"""

YAML_NON_STRING_VALUES = """\
foo: 5
"""

YAML_HIERARCHY = """\
foo: "bar"
bar: "test1,test2"
nsbaz:
    foo: "bat"
    nsbaz2:
        foo: "bat2"
"""


class TestConfigYamlEnv:
    def test_missing_file(self):
        cie = ConfigYamlEnv(["/a/b/c/bogus/filename"])
        assert cie.get("foo") == NO_VALUE

    def test_flat(self, tmpdir):
        """Test flat specification works"""
        yaml_filename = tmpdir / "config.yaml"
        yaml_filename.write(YAML_FLAT)

        cie = ConfigYamlEnv([str(yaml_filename)])
        assert cie.get("foo") == "bar"
        assert cie.get("foo", namespace="nsbaz") == "bat"
        assert cie.get("foo", namespace=["nsbaz"]) == "bat"
        assert cie.get("foo", namespace=["nsbaz", "nsbaz2"]) == "bat2"

    def test_flat_caps(self, tmpdir):
        """Test case-insensitive"""
        yaml_filename = tmpdir / "config.yaml"
        yaml_filename.write(YAML_FLAT)

        cie = ConfigYamlEnv([str(yaml_filename)])
        assert cie.get("foo") == "bar"
        assert cie.get("FOO") == "bar"
        assert cie.get("Foo") == "bar"
        assert cie.get("foo", namespace="nsbaz") == "bat"
        assert cie.get("foo", namespace="NsBaz") == "bat"
        assert cie.get("FOO", namespace="NSBAZ") == "bat"

    def test_hierarchical(self, tmpdir):
        """Test hierarchical specification works"""
        yaml_filename = tmpdir / "config.yaml"
        yaml_filename.write(YAML_HIERARCHY)

        cie = ConfigYamlEnv([str(yaml_filename)])
        assert cie.get("foo") == "bar"
        assert cie.get("foo", namespace="nsbaz") == "bat"
        assert cie.get("foo", namespace=["nsbaz"]) == "bat"
        assert cie.get("foo", namespace=["nsbaz", "nsbaz2"]) == "bat2"

    def test_multiple_files(self, tmpdir):
        """Test multiple files--uses first found"""
        yaml_filename = tmpdir / "config.yaml"
        yaml_filename.write(YAML_FLAT)

        yaml_filename_2 = tmpdir / "config2.yaml"
        yaml_filename_2.write(YAML_FLAT_2)

        cie = ConfigYamlEnv([str(yaml_filename), str(yaml_filename_2)])
        # Only the first found file is loaded, so foo_original does not exist
        assert cie.get("foo_original") == NO_VALUE

        cie = ConfigYamlEnv([str(yaml_filename_2)])
        # ... but it is there if only the original is loaded (safety check)
        assert cie.get("foo_original") == "original"

    def test_non_string_values(self, tmpdir):
        yaml_filename = tmpdir / "config.yaml"
        yaml_filename.write(YAML_NON_STRING_VALUES)

        with pytest.raises(ConfigurationError):
            ConfigYamlEnv([str(yaml_filename)])
