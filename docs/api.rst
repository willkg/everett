===
API
===

This is the API of functions and classes in Everett.

Configuration things:

* :py:class:`everett.manager.ConfigManager`
* :py:class:`everett.manager.Option`

Utility functions:

* :py:class:`everett.manager.get_config_for_class`
* :py:class:`everett.manager.get_runtime_config`

Testing utility functions:

* :py:class:`everett.manager.config_override`

Configuration environments:

* :py:class:`everett.manager.ConfigObjEnv`
* :py:class:`everett.manager.ConfigDictEnv`
* :py:class:`everett.manager.ConfigEnvFileEnv`
* :py:class:`everett.manager.ConfigOSEnv`
* (INI) :py:class:`everett.ext.inifile.ConfigIniEnv`
* (YAML) :py:class:`everett.ext.yamlfile.ConfigYamlEnv`

Errors:

* :py:class:`everett.ConfigurationError`
* :py:class:`everett.InvalidKeyError`
* :py:class:`everett.ConfigurationMissingError`
* :py:class:`everett.InvalidValueError`

Parsers:

* :py:func:`everett.manager.parse_bool`
* :py:func:`everett.manager.parse_class`
* :py:func:`everett.manager.parse_data_size`
* :py:func:`everett.manager.ListOf`


everett
=======

.. automodule:: everett
   :members:

everett.manager
===============

.. automodule:: everett.manager
   :members:
   :special-members: __init__, __call__

everett.ext.inifile
===================

.. automodule:: everett.ext.inifile
   :members:

everett.ext.yamlfile
====================

.. automodule:: everett.ext.yamlfile
   :members:
