.. NOTE: Make sure to edit the template for this file in docs_tmpl/ and
.. not the cog-generated version.

=======
Everett
=======

**Status 2025-10-15: This project is deprecated.**

Everett is a Python configuration library for your app.

:Code:          https://github.com/willkg/everett
:Issues:        https://github.com/willkg/everett/issues
:License:       MPL v2
:Documentation: https://everett.readthedocs.io/


Goals
=====

Goals of Everett:

1. flexible configuration from multiple configured environments
2. easy testing with configuration
3. easy automated documentation of configuration for users

From that, Everett has the following features:

* is flexible for your configuration environment needs and supports
  process environment, env files, dicts, INI files, YAML files,
  and writing your own configuration environments
* facilitates helpful error messages for users trying to configure your
  software
* has a Sphinx extension for documenting configuration including
  ``autocomponentconfig`` and ``automoduleconfig`` directives for
  automatically generating configuration documentation
* facilitates testing of configuration values
* supports parsing values of a variety of types like bool, int, lists of
  things, classes, and others and lets you write your own parsers
* supports key namespaces
* supports component architectures
* works with whatever you're writing--command line tools, web sites, system
  daemons, etc

Everett is inspired by
`python-decouple <https://github.com/henriquebastos/python-decouple>`__
and `configman <https://configman.readthedocs.io/en/latest/>`__.


Install
=======

Run::

    $ pip install everett

Some configuration environments require additional dependencies::


    # For INI support
    $ pip install 'everett[ini]'

    # for YAML support
    $ pip install 'everett[yaml]'


Quick start
===========

Example:

.. [[[cog
   import cog
   with open("examples/myserver.py", "r") as fp:
       cog.outl("\n::\n")
       for line in fp.readlines():
           if line.strip():
               cog.out(f"   {line}")
           else:
               cog.outl()
   cog.outl()
   ]]]

::

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

.. [[[end]]]

Then you can run it:

.. [[[cog
   import cog
   import os
   import subprocess
   if os.path.exists(".env"):
       os.remove(".env")
   ret = subprocess.run(["python", "examples/myserver.py"], capture_output=True)
   cog.outl("\n::\n") 
   cog.outl("   $ python myserver.py")
   for line in ret.stdout.decode("utf-8").splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   ]]]

::

   $ python myserver.py
   host: localhost
   port: 8000
   debug_mode: False

.. [[[end]]]

You can set environment variables to affect configuration:

.. [[[cog
   import cog
   import os
   import subprocess
   if os.path.exists(".env"):
       os.remove(".env")
   os.environ["PORT"] = "7000"
   cog.outl("\n::\n")
   cog.outl("   $ PORT=7000 python myserver.py")
   ret = subprocess.run(["python", "examples/myserver.py"], capture_output=True)
   for line in ret.stdout.decode("utf-8").splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   del os.environ["PORT"]
   ]]]

::

   $ PORT=7000 python myserver.py
   host: localhost
   port: 7000
   debug_mode: False

.. [[[end]]]

It checks a ``.env`` file in the current directory:

.. [[[cog
   import cog
   import os
   import subprocess
   if os.path.exists(".env"):
       os.remove(".env")
   with open(".env", "w") as fp:
       fp.write("HOST=127.0.0.1")
   cog.outl("\n::\n")
   cog.outl("   $ echo \"HOST=127.0.0.1\" > .env")
   cog.outl("   $ python myserver.py")
   ret = subprocess.run(["python", "examples/myserver.py"], capture_output=True)
   for line in ret.stdout.decode("utf-8").splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   ]]]

::

   $ echo "HOST=127.0.0.1" > .env
   $ python myserver.py
   host: 127.0.0.1
   port: 8000
   debug_mode: False

.. [[[end]]]

It spits out useful error information if configuration is wrong:

.. [[[cog
   import cog
   import os
   import subprocess
   if os.path.exists(".env"):
       os.remove(".env")
   os.environ["DEBUG"] = "foo"
   ret = subprocess.run(["python", "examples/myserver.py"], capture_output=True)
   stderr = ret.stderr.decode("utf-8").strip()
   stderr = stderr[stderr.find("everett.InvalidValueError"):]
   cog.outl("\n::\n")
   cog.outl("   $ DEBUG=foo python myserver.py")
   cog.outl("   <traceback>")
   for line in stderr.splitlines():
      cog.outl(f"   {line}")
   cog.outl()
   ]]]

::

   $ DEBUG=foo python myserver.py
   <traceback>
   everett.InvalidValueError: ValueError: 'foo' is not a valid bool value
   DEBUG requires a value parseable by everett.manager.parse_bool
   DEBUG docs: Set to True for debugmode; False for regular mode
   Project docs: Check https://example.com/configuration for documentation.

.. [[[end]]]

You can test your code using ``config_override`` in your tests to test various
configuration values:

.. [[[cog
   import cog
   cog.outl("\n::\n")
   with open("examples/testdebug.py", "r") as fp:
       for line in fp.readlines():
           cog.out(f"   {line}")
   cog.outl()
   ]]]

::

   # testdebug.py
   
   """
   Minimal example showing how to override configuration values when testing.
   """
   
   import unittest
   
   from everett.manager import ConfigManager, config_override
   
   
   class App:
       def __init__(self):
           config = ConfigManager.basic_config()
           self.debug = config("debug", default="False", parser=bool)
   
   
   class TestDebug(unittest.TestCase):
       def test_debug_on(self):
           with config_override(DEBUG="on"):
               app = App()
               self.assertTrue(app.debug)
   
       def test_debug_off(self):
           with config_override(DEBUG="off"):
               app = App()
               self.assertFalse(app.debug)
   
   
   if __name__ == "__main__":
       unittest.main()

.. [[[end]]]

Run that:

.. [[[cog
   import cog
   import os
   import subprocess
   ret = subprocess.run(["python", "examples/testdebug.py"], capture_output=True)
   stderr = ret.stderr.decode("utf-8").strip()
   cog.outl("\n::\n")
   cog.outl("   $ python testdebug.py")
   for line in stderr.splitlines():
       cog.outl(f"   {line}")
   cog.outl()
   ]]]

::

   $ python testdebug.py
   ..
   ----------------------------------------------------------------------
   Ran 2 tests in 0.000s
   
   OK

.. [[[end]]]

That's perfectly fine for a `12-Factor <https://12factor.net/>`__ app.

When you outgrow that or need different variations of it, you can switch to
creating a ``ConfigManager`` instance that meets your needs.


Why not other libs?
===================

Most other libraries I looked at had one or more of the following issues:

* were tied to a specific web app framework
* didn't allow you to specify configuration sources
* provided poor error messages when users configure things wrong
* had a global configuration object
* made it really hard to override specific configuration when writing tests
* had no facilities for autogenerating configuration documentation
