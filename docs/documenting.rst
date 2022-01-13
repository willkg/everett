=========================
Documenting configuration
=========================

.. contents::
   :local:

It's hard to keep configuration documentation up-to-date as projects change
over time.

Everett comes with a `Sphinx <https://http://www.sphinx-doc.org/en/stable/>`_
extension for documenting configuration. It has ``autocomponentconfig`` and
``automoduleconfig`` directives for automatically generating documentation. It
also has ``everett:component`` and ``everett:option`` directives for manually
documenting configuration. It also comes with ``:everett:option:`` and
``:everett:component:`` roles letting you create links to specific
configuration things in your documentation.

Configuration options are added to the index and have unique links making it
easier to find and point people to specific configuration documentation.

.. versionchanged:: 3.0.0
   Complete rewrite of Sphinx directives.


Directives
==========

.. rst:directive:: automoduleconfig

   **Requires Python 3.8 or higher.**

   Automatically documents the configuration options set in a Python module
   using the specified :py:class:`everett.manager.ConfigManager`.

   The argument is the Python dotted path to the
   :py:class:`everett.manager.ConfigManager` instance.

   .. Note::

      The automoduleconfig directive works by parsing the Python module as an
      AST and then traverses the AST.

      It does not execute the module, so it doesn't evaluate any values.

   .. Note::

      ``automoduleconfig`` requires Python 3.8 or higher.

      If you're using ReadTheDocs, it defaults to Python 3.7. You'll need to
      configure the version of Python to use by adding a configuration file.

      See `ReadTheDocs configuration file documentation
      <https://docs.readthedocs.io/en/stable/config-file/v2.html>`_ for more
      details.

   .. rubric:: Options

   .. rst:directive:option:: show-table
      :type: no value

      If set, will create a table summarizing the options in this module with
      links to the option details.

   .. rst:directive:option:: hide-name
      :type: no value

      If set, this will hide the name derived from the Python dotted path
      and use "Configuration" instead.

      This affects how the options are indexed. If you're documenting multiple
      modules this way, options that exist in multiple modules will create a
      conflict.

   .. rst:directive:option:: show-docstring
      :type: str, empty str, or omitted

      If omitted, this does nothing.

      If set, but with no value, this will include the module docstring in
      the documentation.

      If set with a value of the name of an attribute in the module, this will
      include the value of that attribute in the documentation.

      Example to include the module ``__doc__``:

      ::

          .. automoduleconfig:: myproject.settings._config
             :show-docstring:
    
      Example to include the value of the value of the ``HELP`` attribute:

      ::

          .. automoduleconfig:: myproject.settings._config
             :show-docstring: HELP

   .. rst:directive:option:: namespace
      :type: str

      If set, this prefixes all the option keys with the specified namespace.
      
      For example, if you set namespace to ``source_db``, then key ``host``
      would result in ``source_db_host`` being documented. (Case is dependent
      on the "case" directive option.)

   .. rst:directive:option:: case
      :type: "upper", "lower", or omitted

      Specifies whether to convert the full namespaced key to all uppercase,
      all lowercase, or leave it as is.


.. rst:directive:: autocomponentconfig

   Automatically documents the configuration options for the specified class
   and its superclasses.

   The argument is the Python dotted path to the class.

   .. Warning::

      ``autocomponentconfig`` **imports** the code to be documented. If any of
      the imported modules have side-effects at import, they will be executed
      when building the documentation.

   .. rubric:: Options

   .. rst:directive:option:: show-table
      :type: no value

      If set, will create a table summarizing the options in this component
      with links to the option details.

   .. rst:directive:option:: hide-name
      :type: no value

      If set, this will hide the name of the class and use "Configuration"
      instead.

      This affects how the options are indexed. If you're documenting multiple
      classes this way, options that exist in multiple classes will create a
      conflict.

   .. rst:directive:option:: show-docstring
      :type: str, empty str, or omitted

      If omitted, this does nothing.

      If set, but with no value, this will include the class docstring in the
      documentation.

      If set with a value of the name of an attribute of the class, this will
      include the value of that attribute in the documentation.

      Example to include the class docstring:

      ::

          .. automoduleconfig:: myproject.MyClass
             :show-docstring:
    
      Example to include the value of the value of the ``HELP`` attribute:

      ::

          .. automoduleconfig:: myproject.MyClass
             :show-docstring: HELP

   .. rst:directive:option:: namespace
      :type: str

      If set, this prefixes all the option keys with the specified namespace.
      
      For example, if you set namespace to ``source_db``, then key ``host``
      would result in ``source_db_host`` being documented. (Case is dependent
      on the "case" directive option.)

   .. rst:directive:option:: case
      :type: "upper", "lower", or omitted

      Specifies whether to convert the full namespaced key to all uppercase,
      all lowercase, or leave it as is.


.. rst:directive:: everett:component

   Defines an Everett component which is any Python class that has an inner
   class named ``Config`` which defines configuration options.

   The argument is the Python dotted path to the class.

   Add ``everett:option`` as part of the description.


.. rst:directive:: everett:option

   Defines an Everett configuration option.

   The argument is the option key.

   .. rubric:: Options

   .. rst:directive:option:: parser
      :type: str

      The name of the parser for this option.

   .. rst:directive:option:: default
      :type: str

      If not set, the default is ``NO_VALUE`` which means that this option has
      no default value.

      If set, this is the default value. Enclose the value in double-quotes
      because all default values must be strings.

   .. rst:directive:option:: required
      :type: no value

      If set, this option is required.

      If not set and the option has a default, then this option is not
      required.

      If not set and the option has no default, then this option is required.

      This option is not required::

          .. everett:option:: HOST
             :default: localhost

      These two options are required::

          .. everett:option:: USERNAME
             
          .. everett:option:: PASSWORD
             :required:


Examples
========

Documenting component configuration
-----------------------------------

Here's an example Everett component:

.. literalinclude:: ../examples/recipes_appconfig.py


You can use the ``autocomponentconfig`` directive to extract the configuration
information from the ``AppConfig`` class and document it::

    .. autocomponentconfig:: recipes_appconfig.AppConfig
       :case: upper
       :show-table:


That gives you something that looks like this:

.. autocomponentconfig:: recipes_appconfig.AppConfig
   :case: upper
   :show-table:


You can link to components with the ``:everett:component:`` role and options
using the ``:everett:option:`` role.

Example component link::

    Component link: :everett:component:`recipes_appconfig.AppConfig`


Component link: :everett:component:`recipes_appconfig.AppConfig`

Example option link::

    Option link: :everett:option:`recipes_appconfig.AppConfig.DEBUG`


Option link: :everett:option:`recipes_appconfig.AppConfig.DEBUG`



Documenting module configuration
--------------------------------

You can use ``automoduleconfig`` to document configuration that's set at module
import. This is helpful for Django settings modules.

Example configuration code that sets up a
:py:class:`everett.manager.ConfigManager` and calls it ``_config``:

.. literalinclude:: ../examples/recipes_djangosettings.py
   :language: python

Example documentation directive::

    .. automoduleconfig:: recipes_djangosettings._config
       :hide-name:
       :case: upper
       :show-table:

That gives you this:

.. automoduleconfig:: recipes_djangosettings._config
   :hide-name:
   :case: upper
   :show-table:
