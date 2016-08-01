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

"""

import sys

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList
from sphinx.util.docstrings import prepare_docstring

from everett import NO_VALUE


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


class AutoConfigDirective(Directive):
    has_content = True
    required_arguments = 1
    optional_arguments = 0

    def add_line(self, line, source, *lineno):
        """Add a line to the result"""
        self.result.append(line, source, *lineno)

    def generate_docs(self, clspath, more_content):
        """Generate documentation for this configman class"""
        obj = import_class(clspath)
        sourcename = 'docstring of %s' % clspath

        # Add the header
        modname, clsname = split_clspath(clspath)
        self.add_line('.. %s:%s:: %s.%s' % ('py', 'class', modname, clsname),
                      sourcename)
        self.add_line('', sourcename)

        # Add the docstring if there is one
        docstring = getattr(obj, '__doc__', None)
        if docstring:
            docstringlines = prepare_docstring(docstring, ignore=1)
            for i, line in enumerate(docstringlines):
                self.add_line('    ' + line, sourcename, i)
            self.add_line('', '')

        # Add additional content from the directive if there was any
        if more_content:
            for line, src in zip(more_content.data, more_content.items):
                self.add_line('    ' + line, src[0], src[1])
            self.add_line('', '')

        # Add configman related content
        config = obj.get_required_config()

        if config.options:
            self.add_line('    Configuration:', '')
            self.add_line('', '')

            sourcename = 'class definition'

            for option in config:
                self.add_line('        ``%s``' % option.key, sourcename)
                if option.default is NO_VALUE:
                    self.add_line('            :default: ', sourcename)
                else:
                    self.add_line('            :default: %r' % option.default,
                                  sourcename)
                self.add_line('            :parser: %r' % option.parser,
                              sourcename)
                self.add_line('', '')
                self.add_line('            %s' % option.doc, sourcename)
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
    app.add_directive('sphinx_autoconfig', AutoConfigDirective)
