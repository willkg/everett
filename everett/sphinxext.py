# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Contains the autocomponent Sphinx extension for auto-documenting components
with configuration.

The ``autocomponent`` declaration will pull out the class docstring as well as
configuration requirements, throw it all in a blender and spit it out.

To configure Sphinx, add ``'everett.sphinxext'`` to the ``extensions`` in
``conf.py``::

    extensions = [
        ...
        'everett.sphinxext'
    ]


.. Note::

   You need to make sure that Everett is installed in the environment
   that Sphinx is being run in.

Use it like this in an ``.rst`` file to document a component::

    .. autocomponent:: collector.ext.s3.S3CrashStorage


You can refer to that component in other parts of your docs and get a link
by using the ``:everett:component:`` role::

    Check out the :everett:component:`collector.ext.s3.S3CrashStorage`
    configuration.


If your component class names are unique, then you can probably get away with::

    Check out the :everett:component:`S3CrashStorage` configuration.


.. versionchanged:: 0.9

   In Everett 0.8 and prior, the extension was in the
   ``everett.sphinx_autoconfig`` module and the directive was ``..
   autoconfig::``.


**Showing docstring and content**

If you want the docstring for the class, you can specify ``:show-docstring:``::

    .. autocomponent:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :show-docstring:


If you want to show help, but from a different attribute than the docstring,
you can specify any class attribute::

    .. autocomponent:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :show-docstring: __everett_help__


You can provide content as well::

    .. autocomponent:: collector.external.boto.crashstorage.BotoS3CrashStorage

       This is some content!

.. versionadded:: 0.5


**Hiding the class name**

You can hide the class name if you want::

    .. autocomponent:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :hide-classname:


This is handy for application-level configuration where you might not want to
confuse users with how it's implemented.

.. versionadded:: 0.5


**Prepending the namespace**

If you have a component that only gets used with one namespace, then it will
probably help users if the documentation includes the full configuration key
with the namespace prepended.

You can do that like this::

    .. autocomponent:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :namespace: crashstorage


Then the docs will show keys like ``crashstorage_foo`` rather than just
``foo``.

.. versionadded:: 0.8


**Showing keys as uppercased or lowercased**

If your project primarily depends on configuration from OS environment
variables, then you probably want to document those variables with the keys
shown as uppercased.

You can do that like this::

    .. autocomponent:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :case: upper


If your project primarily depends on configuration from INI files, then you
probably want to document those variables with keys shown as lowercased.

You can do that like this::

    .. autocomponent:: collector.external.boto.crashstorage.BotoS3CrashStorage
       :case: lower

.. versionadded:: 0.8

"""

import sys

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList
from sphinx import addnodes
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType
from sphinx.locale import _
from sphinx.roles import XRefRole
from sphinx.util.docfields import TypedField
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.nodes import make_refnode

from everett import NO_VALUE, __version__
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


class EverettComponent(ObjectDescription):
    """
    Description of an Everett component""
    """

    doc_field_types = [
        TypedField('options', label=_('Options'),
                   names=('option', 'opt'),
                   typerolename='obj', typenames=('parser',),
                   can_collapse=True),
    ]

    allow_nesting = False

    def handle_signature(self, sig, signode):
        if sig != 'Configuration':
            # Add "component" to the beginning if it's a specific component
            signode.clear()

            # Add "component" which is the type of this thing
            signode += addnodes.desc_annotation('component ', 'component ')

            if '.' in sig:
                modname, clsname = sig.rsplit('.', 1)
            else:
                modname, clsname = '', sig

            # If there's a module name, then we add the module
            if modname:
                signode += addnodes.desc_addname(modname + '.', modname + '.')

            # Add the class name
            signode += addnodes.desc_name(clsname, clsname)
        else:
            # Add just "Configuration"
            signode += addnodes.desc_name(sig, sig)

        return sig

    def add_target_and_index(self, name, sig, signode):
        targetname = '%s-%s' % (self.objtype, name)

        if targetname not in self.state.document.ids:
            signode['names'].append(targetname)
            signode['ids'].append(targetname)
            signode['first'] = (not self.names)
            self.state.document.note_explicit_target(signode)

            objects = self.env.domaindata['everett']['objects']
            key = (self.objtype, name)
            if key in objects:
                self.state_machine.reporter.warning(
                    'duplicate description of %s %s, ' % (self.objtype, name) +
                    'other instance in ' + self.env.doc2path(objects[key]),
                    line=self.lineno
                )
            objects[key] = self.env.docname

        indextext = _('%s (component)') % name
        self.indexnode['entries'].append(('single', indextext, targetname, '', None))


class EverettDomain(Domain):
    """Everett domain for component configuration"""
    name = 'everett'
    label = 'Everett'

    object_types = {
        'component': ObjType(_('component'), 'comp'),
    }
    directives = {
        'component': EverettComponent,
    }
    roles = {
        'component': XRefRole(),
        'comp': XRefRole(),
    }
    initial_data = {
        # (typ, clspath) -> sphinx document name
        'objects': {},
    }

    def clear_doc(self, docname):
        for (typ, name), doc in list(self.data['objects'].items()):
            if doc == docname:
                del self.data['objects'][typ, name]

    def merge_domaindata(self, docnames, otherdata):
        for (typ, name), doc in otherdata['objects'].items():
            if doc in docnames:
                self.data['objects'][typ, name] = doc

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        objects = self.data['objects']
        objtypes = self.objtypes_for_role(typ) or []

        for objtype in objtypes:
            for (typ, clspath) in objects:
                # Look up using the full classpath
                if (objtype, target) == (typ, clspath):
                    return make_refnode(
                        builder,
                        fromdocname,
                        objects[typ, clspath],
                        objtype + '-' + target,
                        contnode,
                        target + ' ' + objtype
                    )

                # Try looking it up by the class name--this lets people use
                # shorthand in their roles
                if '.' in clspath:
                    modname, clsname = split_clspath(clspath)
                    if (objtype, target) == (typ, clsname):
                        return make_refnode(
                            builder,
                            fromdocname,
                            objects[typ, clspath],
                            objtype + '-' + clspath,
                            contnode,
                            target + ' ' + objtype
                        )


class AutoComponentDirective(Directive):
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
        all_options = []
        indent = '    '
        config = obj.get_required_config()

        if config.options:
            # Go through options and figure out relevant information
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

                all_options.append({
                    'key': namespaced_key,
                    'parser': qualname(option.parser),
                    'doc': option.doc,
                    'default': option.default,
                })

        if 'hide-classname' not in self.options:
            modname, clsname = split_clspath(clspath)
            component_name = clspath
            component_index = clsname
        else:
            component_name = 'Configuration'
            component_index = 'Configuration'

        if all_options:
            # Add index entries for options first so they link to the right
            # place; we do it this way so that we don't have to make options a
            # real object type and then we don't get to use TypedField
            # formatting
            self.add_line('.. index::', sourcename)
            for option in all_options:
                self.add_line('   single: %s; (%s)' % (option['key'], component_index), sourcename)
            self.add_line('', '')

        # Add the classname or 'Configuration'
        self.add_line('.. everett:component:: %s' % component_name, sourcename)
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

        if all_options:
            # Now list the options
            sourcename = 'class definition'

            for option in all_options:
                self.add_line(
                    '%s:option %s %s:' % (indent, option['parser'], option['key']),
                    sourcename
                )
                self.add_line('%s    %s' % (indent, option['doc']), sourcename)
                if option['default'] is not NO_VALUE:
                    self.add_line('', '')
                    self.add_line(
                        '%s    Defaults to ``%r``.' % (indent, option['default']),
                        sourcename
                    )
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
    app.add_domain(EverettDomain)
    app.add_directive('autocomponent', AutoComponentDirective)

    return {
        'version': __version__,
        'parallel_read_safe': True,
        'parallel_write_safe': True
    }
