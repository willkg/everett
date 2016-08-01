==========
Components
==========

.. contents::


Building components with configmanlite
======================================

configmanlite allows you to build components that specify their own
configuration as a class property.

This lets you do three things:

1. instantiate components in a specified configuration namespace
2. restrict the configuration the component uses to that specified in the
   component
3. inherit and override configuration from superclasses


FIXME: Write this

Documenting components
======================

Components can have configuration. It's important to be able to easily document
this configuration.

As such, configmanlite includes a Sphinx extension that adds a ``autoconfig``
declaration for auto-documenting configuration for components.

.. automodule:: configmanlite.sphinx_autoconfig
