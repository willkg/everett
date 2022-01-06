==========================
Configuration environments
==========================

.. contents::
   :local:

Dict (ConfigDictEnv)
====================

.. autoclass:: everett.manager.ConfigDictEnv
   :noindex:


Process environment (ConfigOSEnv)
=================================

.. autoclass:: everett.manager.ConfigOSEnv
   :noindex:


ENV files (ConfigEnvFileEnv)
============================

.. autoclass:: everett.manager.ConfigEnvFileEnv
   :noindex:


Python objects (ConfigObjEnv)
=============================

.. autoclass:: everett.manager.ConfigObjEnv
   :noindex:


INI files (ConfigIniEnv)
========================

.. autoclass:: everett.ext.inifile.ConfigIniEnv
   :noindex:


YAML files (ConfigYamlEnv)
==========================

.. autoclass:: everett.ext.yamlfile.ConfigYamlEnv
   :noindex:


Implementing your own configuration environments
================================================

You can implement your own configuration environments. For example, maybe you
want to pull configuration from a database or Redis or a post-it note on the
refrigerator.

They just need to implement the ``.get()`` method. A no-op implementation is
this:

.. literalinclude:: ../examples/environments.py
   :language: python


Generally, environments should return a value if the key exists in that
environment and should return ``NO_VALUE`` if and only if the key does not
exist in that environment.

For exceptions, it depends on what you want to have happen. It's ok to let
exceptions go unhandled--Everett will wrap them in a :py:class:`everett.ConfigurationError`.
If your environment promises never to throw an exception, then you should
handle them all and return ``NO_VALUE`` since with that promise all exceptions
would indicate the key is not in the environment.
