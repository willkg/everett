# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Sphinx extension for auto-documenting components with configuration.

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

Use it like this in an reStructuredText file to document a component::

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
from typing import Any, Dict, List, Optional, Union

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
from everett.manager import qualname, get_config_for_class


def split_clspath(clspath: str) -> List[str]:
    """Split clspath into module and class names.

    Note: This is a really simplistic implementation.

    """
    return clspath.rsplit(".", 1)


def import_class(clspath: str) -> Any:
    """Given a clspath, returns the class.

    Note: This is a really simplistic implementation.

    """
    modpath, clsname = split_clspath(clspath)
    __import__(modpath)
    module = sys.modules[modpath]
    return getattr(module, clsname)


def upper_lower_none(arg: Optional[str]) -> Union[str, None]:
    """Validate arg value as "upper", "lower", or None."""
    if not arg:
        return arg

    arg = arg.strip().lower()
    if arg in ["upper", "lower"]:
        return arg

    raise ValueError('argument must be "upper", "lower" or None')


class EverettComponent(ObjectDescription):
    """Description of an Everett component."""

    doc_field_types = [
        TypedField(
            "options",
            label=_("Options"),
            names=("option", "opt"),
            typerolename="parser",
            typenames=("parser",),
            can_collapse=True,
        )
    ]

    allow_nesting = False

    # FIXME(willkg): What's the signode here?
    def handle_signature(self, sig: str, signode: Any) -> str:
        """Create a signature for this thing."""
        if sig != "Configuration":
            signode.clear()

            # Add "component" which is the type of this thing
            signode += addnodes.desc_annotation("component ", "component ")

            if "." in sig:
                modname, clsname = sig.rsplit(".", 1)
            else:
                modname, clsname = "", sig

            # If there's a module name, then we add the module
            if modname:
                signode += addnodes.desc_addname(modname + ".", modname + ".")

            # Add the class name
            signode += addnodes.desc_name(clsname, clsname)
        else:
            # Add just "Configuration"
            signode += addnodes.desc_name(sig, sig)

        return sig

    # FIXME(willkg): What's the signode here?
    def add_target_and_index(self, name: str, sig: str, signode: Any) -> None:
        """Add a target and index for this thing."""
        targetname = f"{self.objtype}-{name}"

        if targetname not in self.state.document.ids:
            signode["names"].append(targetname)
            signode["ids"].append(targetname)
            signode["first"] = not self.names
            self.state.document.note_explicit_target(signode)

            objects = self.env.domaindata["everett"]["objects"]
            key = (self.objtype, name)
            if key in objects:
                self.state_machine.reporter.warning(
                    f"duplicate description of {self.objtype} {name}, "
                    + "other instance in "
                    + self.env.doc2path(objects[key]),
                    line=self.lineno,
                )
            objects[key] = self.env.docname

        indextext = _("%s (component)") % name
        self.indexnode["entries"].append(("single", indextext, targetname, "", None))


class EverettDomain(Domain):
    """Everett domain for component configuration."""

    name = "everett"
    label = "Everett"

    object_types = {"component": ObjType(_("component"), "comp")}
    directives = {"component": EverettComponent}
    roles = {
        "component": XRefRole(),
        "comp": XRefRole(),
        "option": XRefRole(),
        "parser": XRefRole(),
    }
    initial_data: Dict[str, dict] = {
        # (typ, clspath) -> sphinx document name
        "objects": {}
    }

    def clear_doc(self, docname: str) -> None:
        for (typ, name), doc in list(self.data["objects"].items()):
            if doc == docname:
                del self.data["objects"][typ, name]

    # FIXME(willkg): What's the value in otherdata dict?
    def merge_domaindata(self, docnames: List[str], otherdata: Dict[str, Any]) -> None:
        for (typ, name), doc in otherdata["objects"].items():
            if doc in docnames:
                self.data["objects"][typ, name] = doc

    # FIXME(willkg): what're args and return type here?
    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):  # type: ignore
        objects = self.data["objects"]
        objtypes = self.objtypes_for_role(typ) or []

        for objtype in objtypes:
            for (typ, clspath) in objects:
                # Look up using the full classpath
                if (objtype, target) == (typ, clspath):
                    return make_refnode(
                        builder,
                        fromdocname,
                        objects[typ, clspath],
                        objtype + "-" + target,
                        contnode,
                        target + " " + objtype,
                    )

                # Try looking it up by the class name--this lets people use
                # shorthand in their roles
                if "." in clspath:
                    modname, clsname = split_clspath(clspath)
                    if (objtype, target) == (typ, clsname):
                        return make_refnode(
                            builder,
                            fromdocname,
                            objects[typ, clspath],
                            objtype + "-" + clspath,
                            contnode,
                            target + " " + objtype,
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
        "show-docstring": directives.unchanged,
        # Whether or not to hide the class name
        "hide-classname": directives.flag,
        # Prepend a specified namespace
        "namespace": directives.unchanged,
        # Render keys in specified case
        "case": upper_lower_none,
    }

    def add_line(self, line: str, source: str, *lineno: int) -> None:
        """Add a line to the result"""
        self.result.append(line, source, *lineno)

    # FIXME(willkg): what is more_content?
    def generate_docs(self, clspath: str, more_content: Any) -> None:
        """Generate documentation for this configman class"""
        obj = import_class(clspath)
        sourcename = "docstring of %s" % clspath
        all_options = []
        indent = "    "
        config = get_config_for_class(obj)

        if config:
            # Go through options and figure out relevant information
            for key, (option, cls) in config.items():
                if "namespace" in self.options:
                    namespaced_key = self.options["namespace"] + "_" + key
                else:
                    namespaced_key = key

                if "case" in self.options:
                    if self.options["case"] == "upper":
                        namespaced_key = namespaced_key.upper()
                    elif self.options["case"] == "lower":
                        namespaced_key = namespaced_key.lower()

                all_options.append(
                    {
                        "key": namespaced_key,
                        "parser": qualname(option.parser),
                        "doc": option.doc,
                        "default": option.default,
                    }
                )

        if "hide-classname" not in self.options:
            modname, clsname = split_clspath(clspath)
            component_name = clspath
            component_index = clsname
        else:
            component_name = "Configuration"
            component_index = "Configuration"

        if all_options:
            # Add index entries for options first so they link to the right
            # place; we do it this way so that we don't have to make options a
            # real object type and then we don't get to use TypedField
            # formatting
            self.add_line(".. index::", sourcename)
            for option_item in all_options:
                self.add_line(
                    "   single: {}; ({})".format(option_item["key"], component_index),
                    sourcename,
                )
            self.add_line("", "")

        # Add the classname or 'Configuration'
        self.add_line(".. everett:component:: %s" % component_name, sourcename)
        self.add_line("", sourcename)

        # Add the docstring if there is one and if show-docstring
        if "show-docstring" in self.options:
            docstring_attr = self.options["show-docstring"] or "__doc__"
            docstring = getattr(obj, docstring_attr, None)
            if docstring:
                docstringlines = prepare_docstring(docstring)
                for i, line in enumerate(docstringlines):
                    self.add_line(indent + line, sourcename, i)
                self.add_line("", "")

        # Add content from the directive if there was any
        if more_content:
            for line, src in zip(more_content.data, more_content.items):
                self.add_line(indent + line, src[0], src[1])
            self.add_line("", "")

        if all_options:
            # Now list the options
            sourcename = "class definition"

            for option_item in all_options:
                self.add_line(
                    "{}:option {} {}:".format(
                        indent, option_item["parser"], option_item["key"]
                    ),
                    sourcename,
                )
                for doc_line in option_item["doc"].splitlines():
                    self.add_line(f"{indent}    {doc_line}", sourcename)
                if option_item["default"] is not NO_VALUE:
                    self.add_line("", "")
                    self.add_line(
                        "{}    Defaults to ``{!r}``.".format(
                            indent, option_item["default"]
                        ),
                        sourcename,
                    )
                self.add_line("", "")

    # FIXME(willkg): this returns a list of nodes
    def run(self) -> List[Any]:
        self.reporter = self.state.document.reporter
        self.result = ViewList()

        self.generate_docs(self.arguments[0], self.content)

        if not self.result:
            return []

        node = nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(self.result, 0, node)
        return node.children


# FIXME(willkg): this takes a Sphinx app
def setup(app: Any) -> Dict[str, Any]:
    """Register domain and directive in Sphinx."""
    app.add_domain(EverettDomain)
    app.add_directive("autocomponent", AutoComponentDirective)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
