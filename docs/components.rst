.. NOTE: Make sure to edit the template for this file in docs_tmpl/ and
.. not the cog-generated version.

==========
Components
==========

.. contents::
   :local:


.. versionchanged:: 2.0

   This is redone for v2.0.0 and simplified.


Configuration components
========================

Everett supports configuration components.

There are two big use cases for this:

1. Centralizing configuration specification for your application into a single
   class.

2. Component architectures.


Centralizing configuration
--------------------------

Instead of having configuration-related bits defined across your codebase, you
can define it in a class.

Here's an example with an ``AppConfig``:

.. literalinclude:: ../examples/component_appconfig.py
   :language: python

Let's run it with the defaults:

.. [[[cog
   import cog
   import os
   import subprocess
   if os.path.exists(".env"):
       os.remove(".env")
   ret = subprocess.run(["python", "examples/component_appconfig.py"], capture_output=True)
   cog.outl("\n::\n")
   cog.outl("   $ python component_appconfig.py")
   for line in ret.stdout.decode("utf-8").splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   ]]]

::

   $ python component_appconfig.py
   debug: False

.. [[[end]]]

Now with ``DEBUG=true``:

.. [[[cog
   import cog
   import os
   import subprocess
   if os.path.exists(".env"):
       os.remove(".env")
   os.environ["DEBUG"] = "true"
   ret = subprocess.run(["python", "examples/component_appconfig.py"], capture_output=True)
   cog.outl("\n::\n")
   cog.outl("   $ DEBUG=true python component_appconfig.py")
   for line in ret.stdout.decode("utf-8").splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   del os.environ["DEBUG"]
   ]]]

::

   $ DEBUG=true python component_appconfig.py
   debug: True

.. [[[end]]]

Let's run a Python shell and do some other things with it:

.. doctest::

   >>> import component_appconfig
   debug: False
   >>> config = component_appconfig.get_config()
   >>> config("badkey")
   Traceback (most recent call last):
       ...
   everett.InvalidKeyError: 'badkey' is not a valid key for this component

Notice how you can't use configuration keys that aren't specified in the bound
component.

Centrally defining configuration like this helps in a few ways:

1. You can reduce some bugs that occur as your application evolves over time.
   Every time you use configuration, the ``ConfigManager`` will enforce that
   the key is a valid option.

2. Your application configuration is centralized in one place instead
   of spread out across your code base.

3. You can automatically document your configuration using the
   ``everett.sphinxext`` Sphinx extension and ``autocomponentconfig`` directive::

       .. autocomponentconfig:: path.to.AppConfig

   Because it's automatically documented, your documentation is always
   up-to-date.


Component architectures
-----------------------

Everett configuration supports component architectures. Say your app needs to
connect to RabbitMQ. With Everett, you can define the component's configuration
needs in the component class.

Here's an example:

.. literalinclude:: ../examples/componentapp.py
   :language: python


That's not wildly exciting, but if the component was in a library of
components, then you can string them together using configuraiton.

For example, what if the destination wasn't a single bucket, but rather
a set of buckets?

::

    dest_config = config("pipeline", default="dest", parser=ListOf(str))

    dest_buckets = []
    for name in dest_config:
        dest_buckets.append(S3Bucket(s3_config.with_namespace(name)))

You can autogenerate configuration documentation for this component in your
Sphinx docs by including the ``everett.sphinxext`` Sphinx extension and
using the ``autocomponentconfig`` directive::

    .. autocomponentconfig:: myapp.S3Bucket


Subclassing
===========

You can subclass components and override configuration options.

For example:

.. literalinclude:: ../examples/components_subclass.py
   :language: python

That prints:

.. [[[cog
   import cog
   import os
   import subprocess
   if os.path.exists(".env"):
       os.remove(".env")
   ret = subprocess.run(["python", "examples/components_subclass.py"], capture_output=True)
   cog.outl("\n::\n")
   cog.outl("   $ python components_subclass.py")
   for line in ret.stdout.decode("utf-8").splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   ]]]

::

   $ python components_subclass.py
   foo_from_b
   bar_from_a

.. [[[end]]]


Getting configuration information for components
================================================

You can get the configuration options for a component class using
:py:func:`everett.manager.get_config_for_class`. This returns a dict of
``configuration key -> (option, class)``. This helps with debugging which
option came from which class.

.. autofunction:: everett.manager.get_config_for_class
   :noindex:


You can get the runtime configuration for a component or tree of components
using :py:func:`everett.manager.get_runtime_config`. This returns a list of
``(namespace, key, value, option, class)`` tuples. The value is the computed
runtime value taking into account the environments specified in the
``ConfigManager`` and class hierarchies.

It'll traverse any instance attributes that are components with options.

.. autofunction:: everett.manager.get_runtime_config
   :noindex:
