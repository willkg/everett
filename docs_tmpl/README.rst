.. NOTE: Make sure to edit the template for this file in docs_tmpl/ and
.. not the cog-generated version.

=======
Everett
=======

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

Everett is inspired by `python-decouple
<https://github.com/henriquebastos/python-decouple>`_ and `configman
<https://configman.readthedocs.io/en/latest/>`_.


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

Example::

    [[[cog
    import cog
    with open("examples/myserver.py", "r") as fp:
        cog.outl(fp.read().strip())
    ]]]
    [[[end]]]

Then you can run it::

    $ python myserver.py
    [[[cog
    import cog
    import os
    import subprocess
    if os.path.exists(".env"):
        os.remove(".env")
    ret = subprocess.run(["python", "examples/myserver.py"], capture_output=True)
    cog.outl(ret.stdout.decode("utf-8").strip())
    ]]]
    [[[end]]]

You can set environment variables to affect configuration::

    $ PORT=7000 python myserver.py
    [[[cog
    import cog
    import os
    import subprocess
    if os.path.exists(".env"):
        os.remove(".env")
    os.environ["PORT"] = "7000"
    ret = subprocess.run(["python", "examples/myserver.py"], capture_output=True)
    cog.outl(ret.stdout.decode("utf-8").strip())
    del os.environ["PORT"]
    ]]]
    [[[end]]]

It checks a ``.env`` file in the current directory::

    $ echo "HOST=127.0.0.1" > .env
    $ python myserver.py
    [[[cog
    import cog
    import os
    import subprocess
    if os.path.exists(".env"):
        os.remove(".env")
    with open(".env", "w") as fp:
        fp.write("HOST=127.0.0.1")
    ret = subprocess.run(["python", "examples/myserver.py"], capture_output=True)
    cog.outl(ret.stdout.decode("utf-8").strip())
    ]]]
    [[[end]]]

It spits out useful error information if configuration is wrong::

    $ DEBUG=foo python myserver.py
    [[[cog
    import cog
    import os
    import subprocess
    if os.path.exists(".env"):
        os.remove(".env")
    os.environ["DEBUG"] = "foo"
    ret = subprocess.run(["python", "examples/myserver.py"], capture_output=True)
    stderr = ret.stderr.decode("utf-8").strip()
    stderr = stderr[stderr.find("everett.InvalidValueError"):]
    cog.outl("<traceback>")
    cog.outl(stderr)
    ]]]
    [[[end]]]

You can test your code using ``config_override`` in your tests to test various
configuration values::

    [[[cog
    import cog
    with open("examples/testdebug.py", "r") as fp:
        cog.outl(fp.read().strip())
    ]]]
    [[[end]]]

Run that::

    [[[cog
    import cog
    import os
    import subprocess
    ret = subprocess.run(["python", "examples/testdebug.py"], capture_output=True)
    stderr = ret.stderr.decode("utf-8").strip()
    cog.outl(stderr)
    ]]]
    [[[end]]]

That's perfectly fine for a `12-Factor <https://12factor.net/>`_ app.

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
