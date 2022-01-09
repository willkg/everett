=======
Recipes
=======

This contains some ways of solving problems I've had with applications I use
Everett in. These use cases help me to shape the Everett architecture such that
it's convenient and flexible, but not big and overbearing.

Hopefully they help you, too.

If there are things you're trying to solve and you're using Everett that aren't
covered here, add an item to the `issue tracker
<https://github.com/willkg/everett/issues>`_.


.. contents::
   :local:


Centralizing configuration specification
========================================

It's easy to set up a :py:class:`everett.manager.ConfigManager` and then call it
for configuration. However, with any non-trivial application, it's likely you're
going to refer to configuration options multiple times in different parts of the
code.

One way to do this is to pull out the configuration value and store it in a
global constant or an attribute somewhere and pass that around.

Another way to do this is to create a configuration component, define all the
configuration options there and then pass that component around.

For example, this creates an ``AppConfig`` component which has configuration
for the application:

.. literalinclude:: ../examples/recipes_appconfig.py
   :language: python


Couple of nice things here. First, is that if you do Sphinx documentation, you
can use ``autocomponentconfig`` to automatically document your configuration
based on the code. Second, you can use
:py:func:`everett.manager.get_runtime_config` to print out the runtime
configuration at startup.


Using components that share configuration by passing arguments
==============================================================

Say we have multiple components that share some configuration value that's
probably managed by another component.

For example, a "basedir" configuration value that defines the root directory for
all the things this application does things with.

Let's create an app component which creates two file system components passing
them a basedir:

.. literalinclude:: ../examples/recipes_shared.py
   :language: python


Why do it this way?

In this scenario, the ``basedir`` is defined at the app-scope and is passed to
the reader and writer components when they're created. In this way, ``basedir``
is app configuration, but not reader/writer configuration.


Using components that share configuration using alternate keys
==============================================================

Say we have two components that share a set of credentials. We don't want to
have to specify the same set of credentials twice, so instead, we use alternate
keys which let you specify other keys to look at for a configuration value.
This lets us have both components look at the same keys for their credentials
and then we only have to define them once.

Let's create a db reader and a db writer component:

.. literalinclude:: ../examples/recipes_alternate_keys.py
   :language: python
