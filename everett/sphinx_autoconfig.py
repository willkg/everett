# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Contains the autoconfig Sphinx extension for auto-documenting components
with configuration.

The ``autoconfig`` declaration will pull out the class docstring as well as
configuration requirements, throw it all in a blender and spit it out.

To configure Sphinx, add ``'everett.sphinx_autoconfig'`` to the
``extensions`` in ``conf.py``::

    extensions = [
        ...
        'everett.sphinx_autoconfig'
    ]


.. Note::

   You need to make sure that Everett is installed in the environment
   that Sphinx is being run in.


Use it like this in an ``.rst`` file to document a component::

    .. autoconfig:: collector.external.boto.crashstorage.BotoS3CrashStorage


**Showing docstring and content**

If you want the docstring for the class, you can specify ``:show-docstring:``::

    .. autoconfig:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :show-docstring:


If you want to show help, but from a different attribute than the docstring,
you can specify any class attribute::

    .. autoconfig:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :show-docstring: __everett_help__


You can provide content as well::

    .. autoconfig:: collector.external.boto.crashstorage.BotoS3CrashStorage

       This is some content!

.. versionadded:: 0.5


**Hiding the class name**

You can hide the class name if you want::

    .. autoconfig:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :hide-classname:


This is handy for application-level configuration where you might not want to
confuse users with how it's implemented.

.. versionadded:: 0.5


**Prepending the namespace**

If you have a component that only gets used with one namespace, then it will
probably help users if the documentation includes the full configuration key
with the namespace prepended.

You can do that like this::

    .. autoconfig:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :namespace: crashstorage


Then the docs will show keys like ``crashstorage_foo`` rather than just
``foo``.

.. versionadded:: 0.8


**Showing keys as uppercased or lowercased**

If your project primarily depends on configuration from OS environment
variables, then you probably want to document those variables with the keys
shown as uppercased.

You can do that like this::

    .. autoconfig:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :case: upper


If your project primarily depends on configuration from INI files, then you
probably want to document those variables with keys shown as lowercased.

You can do that like this::

    .. autoconfig:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :case: lower

.. versionadded:: 0.8

"""

import sys

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx.util.docstrings import prepare_docstring

from everett import NO_VALUE
from everett.manager import qualname


def split_clspath(clspath):
    """Simple split of clspath into module and class names

    Note: This is a really simplistic implementation.

    """
    return clspath.rsplit('.', 1)


def import_class(clspath):
    """Given a clspath, returns the class

    Note: This is a really simplistic implementation.

    """
    modpath, clsname = split_clspath(clspath)
    __import__(modpath)
    module = sys.modules[modpath]
    return getattr(module, clsname)


def upper_lower_none(arg):
    if not arg:
        return arg

    arg = arg.strip().lower()
    if arg in ['upper', 'lower']:
        return arg

    raise ValueError('argument must be "upper", "lower" or None')


class AutoConfigDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    option_spec = {
        # Whether or not to show the class docstring--if None, don't show the
        # docstring, if empty string use __doc__, otherwise use the value of
        # the attribute on the class
        'show-docstring': directives.unchanged,

        # Whether or not to hide the class name
        'hide-classname': directives.flag,

        # Prepend a specified namespace
        'namespace': directives.unchanged,

        # Render keys in specified case
        'case': upper_lower_none,
    }

    def add_line(self, line, source, *lineno):
        """Add a line to the result"""
        self.result.append(line, source, *lineno)

    def generate_docs(self, clspath, more_content):
        """Generate documentation for this configman class"""
        obj = import_class(clspath)
        sourcename = 'docstring of %s' % clspath

        # Add the classname or 'Configuration'
        if 'hide-classname' not in self.options:
            modname, clsname = split_clspath(clspath)
            self.add_line('.. %s:%s:: %s.%s' % ('py', 'class', modname, clsname),
                          sourcename)
            indent = '    '
        else:
            indent = ''
        self.add_line('', sourcename)

        # Add the docstring if there is one and if show-docstring
        if 'show-docstring' in self.options:
            docstring_attr = self.options['show-docstring'] or '__doc__'
            docstring = getattr(obj, docstring_attr, None)
            if docstring:
                docstringlines = prepare_docstring(docstring, ignore=1)
                for i, line in enumerate(docstringlines):
                    self.add_line(indent + line, sourcename, i)
                self.add_line('', '')

        # Add content from the directive if there was any
        if more_content:
            for line, src in zip(more_content.data, more_content.items):
                self.add_line(indent + line, src[0], src[1])
            self.add_line('', '')

        # Add component options related content
        config = obj.get_required_config()

        if config.options:
            self.add_line(indent + 'Configuration:', '')
            self.add_line('', '')

            sourcename = 'class definition'

            for option in config:
                if 'namespace' in self.options:
                    namespaced_key = self.options['namespace'] + '_' + option.key
                else:
                    namespaced_key = option.key

                if 'case' in self.options:
                    if self.options['case'] == 'upper':
                        namespaced_key = namespaced_key.upper()
                    elif self.options['case'] == 'lower':
                        namespaced_key = namespaced_key.lower()

                self.add_line('%s    ``%s``' % (indent, namespaced_key), sourcename)
                if option.default is NO_VALUE:
                    self.add_line('%s        :default: ' % indent, sourcename)
                else:
                    self.add_line('%s        :default: ``%r``' % (indent, option.default),
                                  sourcename)

                self.add_line('%s        :parser: %s' % (indent, qualname(option.parser)),
                              sourcename)
                self.add_line('', '')
                self.add_line('%s        %s' % (indent, option.doc), sourcename)
                self.add_line('', '')

    def run(self):
        self.reporter = self.state.document.reporter
        self.result = ViewList()

        self.generate_docs(self.arguments[0], self.content)

        if not self.result:
            return []

        node = nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(self.result, 0, node)
        return node.children


def setup(app):
    app.add_directive('autoconfig', AutoConfigDirective)
