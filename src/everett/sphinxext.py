# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Sphinx extension for auto-documenting components with configuration."""

import ast
from importlib import import_module
import re
import textwrap
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Generator,
    List,
    Optional,
    Tuple,
    Union,
)

from docutils import nodes
from docutils.parsers.rst import Directive, directives
from docutils.statemachine import ViewList, StringList
from sphinx import addnodes
from sphinx.addnodes import desc_signature, pending_xref
from sphinx.directives import ObjectDescription
from sphinx.domains import Domain, ObjType
from sphinx.locale import _
from sphinx.roles import XRefRole
from sphinx.util import ws_re
from sphinx.util import logging
from sphinx.util.docfields import Field
from sphinx.util.docstrings import prepare_docstring
from sphinx.util.nodes import make_refnode

from everett import NO_VALUE, __version__
from everett.manager import qualname, get_config_for_class


if TYPE_CHECKING:
    from sphinx.builders import Builder
    from sphinx.environment import BuildEnvironment


LOGGER = logging.getLogger(__name__)


def split_clspath(clspath: str) -> List[str]:
    """Split clspath into module and class names.

    Note: This is a really simplistic implementation.

    """
    return clspath.rsplit(".", 1)


def get_module_and_objpath(path: str) -> Any:
    """Given a path, imports the module part of the path and returns the module
    and the rest of the path.

    :arg clspath: a "a.b.c.Class" style path

    :returns: "a.b.c" module and "Class"

    """
    parts = path.split(".")

    # Figure out the module
    for i in range(len(parts)):
        modpath = parts[:i]
        objpath = parts[i:]
        if not modpath:
            continue

        try:
            module = import_module(".".join(modpath))
        except ImportError:
            break

    return module, ".".join(objpath)


def import_class(clspath: str) -> Any:
    """Given a clspath, returns the class.

    Note: This is a really simplistic implementation.

    :arg clspath: a "a.b.c.Class" style path

    :returns: the Class

    """
    module, objpath = get_module_and_objpath(clspath)

    obj = module
    for part in objpath.split(","):
        obj = getattr(obj, part)

    return obj


def upper_lower_none(arg: Optional[str]) -> Union[str, None]:
    """Validate arg value as "upper", "lower", or None."""
    if not arg:
        return arg

    arg = arg.strip().lower()
    if arg in ["upper", "lower"]:
        return arg

    raise ValueError('argument must be "upper", "lower" or None')


class EverettOption(ObjectDescription):
    """An Everett config option."""

    indextemplate = "everett option; %s"

    option_spec = {
        # This is the parser for the option
        "parser": directives.unchanged_required,
        # The default for this option; no value (not NO_VALUE--that's different) is
        # treated as an empty string
        "default": directives.unchanged_required,
        # Whether or not this option is required
        "required": directives.flag,
    }

    def handle_signature(self, sig: str, signode: desc_signature) -> str:
        signode.clear()
        signode += addnodes.desc_name(sig, sig)
        name = ws_re.sub(" ", sig)
        return name

    def add_target_and_index(
        self, name: str, sig: str, signode: desc_signature
    ) -> None:
        ref = self.env.ref_context.get("everett:component")
        if ref:
            targetname = f"{self.objtype}-{ref}.{name}"
            # If this is in a component, we change the name to include the
            # component name
            name = f"{ref}.{name}"
        else:
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
                    f"duplicate description of {self.objtype} {name!r}, "
                    + f"other instance in {self.env.doc2path(objects[key][0])}",
                    line=self.lineno,
                )

            objects[key] = (self.env.docname, targetname)

        indextext = _("%s (component)") % name
        if self.indexnode is not None:
            self.indexnode["entries"].append(
                ("single", indextext, targetname, "", None)
            )

    def transform_content(self, contentnode: addnodes.desc_content) -> None:
        # We want to insert some stuff before the content

        lines = StringList()

        sourcename = "everett option"

        parser = self.options.get("parser", "str")
        default = self.options.get("default")
        is_required = ("required" in self.options) or (default is None)
        required = "Yes" if is_required else "No"

        lines.append(f":Parser: *{parser}*", sourcename)

        if default is not None:
            lines.append(f":Default: {default}", sourcename)

        lines.append(f":Required: {required}", sourcename)
        lines.append("", sourcename)

        node = nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(lines, 0, node)

        # Insert  our new nodes before the rest of the content
        contentnode.children = node.children + contentnode.children


class EverettComponent(ObjectDescription):
    """Description of an Everett component."""

    doc_field_types = [
        Field(
            "options",
            names=("option",),
            label=_("Options"),
            rolename="option",
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

    def add_target_and_index(
        self, name: str, sig: str, signode: desc_signature
    ) -> None:
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
                    f"duplicate description of {self.objtype} {name!r}, "
                    + f"other instance in {self.env.doc2path(objects[key][0])}",
                    line=self.lineno,
                )
            objects[key] = (self.env.docname, targetname)

        indextext = _("%s (component)") % name
        if self.indexnode is not None:
            self.indexnode["entries"].append(
                ("single", indextext, targetname, "", None)
            )

    def before_content(self) -> None:
        if self.names:
            self.env.ref_context["everett:component"] = self.names[-1]

    def after_content(self) -> None:
        self.env.ref_context["everett:component"] = None


class EverettDomain(Domain):
    """Everett domain for component configuration."""

    name = "everett"
    label = "Everett"

    object_types = {
        "component": ObjType(_("component"), "component"),
        "option": ObjType(_("option"), "option"),
    }
    directives = {
        "component": EverettComponent,
        "option": EverettOption,
    }
    roles = {
        "component": XRefRole(),
        "option": XRefRole(),
    }
    initial_data: Dict[str, dict] = {
        # (typ, clspath) -> sphinx document name
        "objects": {}
    }

    @property
    def objects(self) -> Dict[Tuple[str, str], Tuple[str, str]]:
        return self.data.setdefault("objects", {})

    def clear_doc(self, docname: str) -> None:
        key: Any = None
        for key, val in list(self.objects.items()):
            if val[0] == docname:
                del self.objects[key]

    # FIXME(willkg): What's the value in otherdata dict?
    def merge_domaindata(self, docnames: List[str], otherdata: Dict[str, Any]) -> None:
        for key, val in otherdata["objects"].items():
            if val[0] in docnames:
                self.objects[key] = val

    def resolve_xref(
        self,
        env: "BuildEnvironment",
        fromdocname: str,
        builder: "Builder",
        typ: str,
        target: str,
        node: pending_xref,
        contnode: nodes.Element,
    ) -> Optional[nodes.Element]:

        objtypes = self.objtypes_for_role(typ) or []
        for objtype in objtypes:
            if (objtype, target) in self.objects:
                docname, labelid = self.objects[objtype, target]
                break

        else:
            docname, labelid = "", ""

        if docname:
            return make_refnode(builder, fromdocname, docname, labelid, contnode)

        return None


class ConfigDirective(Directive):
    """Base class for generating configuration"""

    def add_line(self, line: str, source: str, *lineno: int) -> None:
        """Add a line to the result"""
        self.result.append(line, source, *lineno)
        # NOTE(willkg): This makes figuring out issues easier. Leaving it here
        # for future me.
        # if line.strip():
        #     print(f">>> {line} [{source} {lineno}]")
        # else:
        #     print(">>> ")

    def generate_docs(
        self,
        component_name: str,
        component_index: str,
        docstring: str,
        sourcename: str,
        option_data: List[Dict],
        more_content: Any,
    ) -> None:

        indent = "   "

        # Add the classname or 'Configuration'
        self.add_line(".. everett:component:: %s" % component_name, sourcename)
        self.add_line("", sourcename)

        # Add the docstring if there is one and if show-docstring
        if "show-docstring" in self.options and docstring:
            docstringlines = prepare_docstring(docstring)
            for i, line in enumerate(docstringlines):
                self.add_line(indent + line, sourcename, i)
            self.add_line("", "")

        # Add content from the directive if there was any
        if more_content:
            for line, src in zip(more_content.data, more_content.items):
                self.add_line(indent + line, src[0], src[1])
            self.add_line("", "")

        if "show-table" in self.options:
            self.add_line(indent + "Configuration summary:", sourcename)
            self.add_line("", sourcename)

            # First build a table of metric items
            table: List[List[str]] = []
            table.append(["Setting", "Parser", "Required?"])
            for option_item in option_data:
                ref = f"{component_name}.{option_item['key']}"
                table.append(
                    [
                        f":everett:option:`{option_item['key']} <{ref}>`",
                        f"*{option_item['parser']}*",
                        "Yes" if option_item["default"] is NO_VALUE else "",
                    ]
                )

            for line in build_table(table):
                self.add_line(indent + line, sourcename)

            self.add_line("", sourcename)

            self.add_line(indent + "Configuration options:", sourcename)
            self.add_line("", sourcename)

        if option_data:
            # Now list the options
            sourcename = "class definition"

            for option_item in option_data:
                key = option_item["key"]
                self.add_line(f"{indent}.. everett:option:: {key}", sourcename)

                self.add_line(
                    f"{indent}   :parser: {option_item['parser']}", sourcename
                )
                if option_item["default"] is not NO_VALUE:
                    self.add_line(
                        f"{indent}   :default: \"{option_item['default']}\"", sourcename
                    )
                else:
                    self.add_line(f"{indent}   :required:", sourcename)
                self.add_line("", sourcename)

                doc = option_item["doc"]
                for doc_line in doc.splitlines():
                    self.add_line(f"{indent}   {doc_line}", sourcename)

                self.add_line("", sourcename)
        self.add_line("", sourcename)


class AutoComponentConfigDirective(ConfigDirective):
    """Directive for documenting configuration for an Everett component."""

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
        "hide-name": directives.flag,
        # Prepend a specified namespace
        "namespace": directives.unchanged,
        # Render keys in specified case
        "case": upper_lower_none,
        # Whether or not to show a table
        "show-table": directives.flag,
    }

    def extract_configuration(
        self,
        obj: Any,
        namespace: Optional[str] = None,
        case: Optional[str] = None,
    ) -> List[Dict]:
        """Extracts configuration values from list of Everett configuration options

        :param obj: object/class to extract configuration from
        :param namespace: namespace if any that these options are in
        :param case: None, "upper", or "lower" for converting the name

        :returns: list of dicts each representing an option

        """
        config = get_config_for_class(obj)
        options: List[Dict] = []

        # Go through options and figure out relevant information
        for key, (option, cls) in config.items():
            if namespace:
                namespaced_key = namespace + "_" + key
            else:
                namespaced_key = key

            if case == "upper":
                namespaced_key = namespaced_key.upper()
            elif case == "lower":
                namespaced_key = namespaced_key.lower()

            options.append(
                {
                    "key": namespaced_key,
                    "default": option.default,
                    "parser": qualname(option.parser),
                    "doc": option.doc,
                    "meta": {},
                }
            )
        return options

    def run(self) -> List[nodes.Node]:
        self.reporter = self.state.document.reporter
        self.result = ViewList()

        clspath = self.arguments[0]

        obj = import_class(clspath)
        sourcename = "configuration of %s" % clspath

        option_data = self.extract_configuration(
            obj=obj,
            namespace=self.options.get("namespace"),
            case=self.options.get("case"),
        )

        if "hide-name" not in self.options:
            modname, clsname = split_clspath(clspath)
            component_name = clspath
            component_index = clsname
        else:
            component_name = "Configuration"
            component_index = "Configuration"

        # Add the docstring if there is one and if show-docstring
        if "show-docstring" in self.options:
            docstring_attr = self.options["show-docstring"] or "__doc__"
            docstring = getattr(obj, docstring_attr, "")
        else:
            docstring = ""

        self.generate_docs(
            component_name=component_name,
            component_index=component_index,
            docstring=docstring,
            sourcename=sourcename,
            option_data=option_data,
            more_content=self.content,
        )

        if not self.result:
            return []

        node = nodes.paragraph()
        node.document = self.state.document
        self.state.nested_parse(self.result, 0, node)
        return node.children


SETTING_RE = re.compile(r"^[A-Z_]+$")


def build_table(table: List[List[str]]) -> List[str]:
    """Generates reST for a table.

    :param table: a 2d array of rows and columns

    :returns: list of strings

    """
    output: List[str] = []

    col_size = [0] * len(table[0])
    for row in table:
        for i, col in enumerate(row):
            col_size[i] = max(col_size[i], len(col))

    col_size = [width + 2 for width in col_size]

    # Build header
    output.append("  ".join("=" * width for width in col_size))
    output.append(
        "  ".join(
            header + (" " * (width - len(header)))
            for header, width in zip(table[0], col_size)
        )
    )
    output.append("  ".join("=" * width for width in col_size))

    # Iterate through rows
    for row in table[1:]:
        output.append(
            "  ".join(
                col + (" " * (width - len(col))) for col, width in zip(row, col_size)
            )
        )
    output.append("  ".join("=" * width for width in col_size))
    return output


def get_value_from_ast_node(source: str, val: ast.AST) -> str:
    """Wrapper for ast.get_source_segment.

    NOTE(willkg): ``ast.get_source_segment()`` was implemented in Python 3.8
    and when we drop support for Python 3.7, we can drop this code, too.

    This is to get the source code for the AST node in question so that we can
    display it as is in the docs. For a wildly contrived example, if you did
    something bizarre like::

        config = ConfigManager.basic_config()
        DEBUG = config("debug, parser=bool, default="False")
        WEIRD = config("weird", parser=(bool if config("debug") else int))

    then the node for ``bool if config("debug") else int`` will be an
    ``ast.IfEq`` (or something like that) and this function will return::

       bool if config("debug") else int

    and show that as the parser in the docs.

    :param source: the complete source text for the file being parsed
    :param val: the ast node in question

    :returns: a string representation of the ast node for display in docs

    """
    if hasattr(ast, "get_source_segment"):
        return ast.get_source_segment(source, val) or "?"

    # If we have < Python 3.8, return a "?" because it's not clear what it is.
    # Python 3.6 and 3.7 don't have end_lineno and end_col_offset either, so I
    # couldn't figure out a good way to figure out the source segment to
    # return.
    return "?"


class AutoModuleConfigDirective(ConfigDirective):
    """Directive for documenting configuration for a module."""

    has_content = True
    # path/to/module.py variablename
    required_arguments = 1
    optional_arguments = 0
    final_argument_whitespace = False

    option_spec = {
        # Whether or not to show the class docstring--if None, don't show the
        # docstring, if empty string use __doc__, otherwise use the value of
        # the attribute on the class
        "show-docstring": directives.unchanged,
        # Whether or not to hide the name
        "hide-name": directives.flag,
        # Prepend a specified namespace
        "namespace": directives.unchanged,
        # Render keys in specified case
        "case": upper_lower_none,
        # Whether or not to show a table
        "show-table": directives.flag,
    }

    def _walk_ast(self, tree: ast.AST) -> Generator[ast.AST, None, None]:
        """Walks an AST returning Assign nodes

        :param tree: the tree to walk

        :returns: generator of Assign nodes

        """
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.Dict)):
                yield node

    def extract_configuration(
        self,
        filepath: str,
        variable_name: str,
        namespace: Optional[str] = None,
        case: Optional[str] = None,
    ) -> List[Dict]:
        """Extracts configuration values from a module at filepath

        :param filepath: the filepath to parse configuration from
        :param variable_name: the ConfigurationManager variable name
        :param namespace: namespace if any that these options are in
        :param case: None, "upper", or "lower" for converting the name

        :returns: list of dicts each representing an option

        """
        with open(filepath) as fp:
            source = fp.read()

        tree = ast.parse(source=source, filename=filepath, mode="exec")
        config_nodes = []

        for node in self._walk_ast(tree):
            if isinstance(node, ast.Assign):
                # Covers:
                #
                # SOMESETTING = _config("option", default="foo", ...)
                if (
                    len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name)
                    and SETTING_RE.match(node.targets[0].id)
                    and isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == variable_name
                ):
                    config_nodes.append((node.targets[0].id, node.value))

            elif isinstance(node, ast.Dict):
                # Covers:
                #
                # SOMESETTING = {
                #     "NAME": _config("option", default="foo", ...),
                #     "NAME2": _config("option2", default="foo", ...),
                # }
                for key, val in zip(node.keys, node.values):
                    if (
                        isinstance(key, ast.Str)
                        and isinstance(val, ast.Call)
                        and isinstance(val.func, ast.Name)
                        and val.func.id == variable_name
                    ):
                        config_nodes.append((key.s, val))

        CONFIG_ARGS = [
            "key",
            "default",
            "parser",
            "doc",
            "meta",
        ]

        def extract_value(source: str, val: ast.AST) -> Tuple[str, str]:
            """Returns (category, value)"""
            if isinstance(val, ast.Constant):
                return "constant", val.value
            if isinstance(val, ast.Name):
                return "name", val.id
            return "unknown", get_value_from_ast_node(source, val)

        # Using a dict here avoids the case where configuration options are
        # defined multiple times
        configuration = {}

        for name, node in config_nodes:
            args: Dict[str, Any] = {
                "key": name,
                "default": NO_VALUE,
                "parser": "str",
                "doc": "",
                "meta": {},
            }
            for i, arg in enumerate(node.args):
                cat, value = extract_value(source, arg)

                # NOTE(willkg): we're dropping the cat here; but we might want
                # to do something with the category in the future, so I'm
                # leaving the figuring in for now
                args[CONFIG_ARGS[i]] = value

            for keyword in node.keywords:
                # NOTE(willkg): mypy thinks this can be None for some reason,
                # but I'm not sure why. If it is None, we should skip it.
                if keyword.arg is None:
                    continue

                cat, value = extract_value(source, keyword.value)
                value = "" if value is None else value
                if keyword.arg == "doc":
                    value = textwrap.dedent(value)

                # NOTE(willkg): we're dropping the cat here; but we might want
                # to do something with the category in the future, so I'm
                # leaving the figuring in for now
                args[keyword.arg] = value

            key = args["key"]
            if namespace:
                namespaced_key = f"{namespace}_{key}"
            else:
                namespaced_key = str(key)

            if case == "upper":
                namespaced_key = namespaced_key.upper()
            elif case == "lower":
                namespaced_key = namespaced_key.lower()

            args["key"] = namespaced_key
            configuration[name] = args

        return list(configuration.values())

    def run(self) -> List[nodes.Node]:
        self.reporter = self.state.document.reporter
        self.result = ViewList()

        clspath = self.arguments[0]

        module, objpath = get_module_and_objpath(clspath)
        filepath = module.__file__
        variable_name = objpath

        if not variable_name:
            raise ValueError("Variable in module is unknown")

        sourcename = "configuration of %s" % clspath

        option_data = self.extract_configuration(
            filepath=filepath,
            variable_name=variable_name,
            namespace=self.options.get("namespace"),
            case=self.options.get("case"),
        )

        if "hide-name" not in self.options:
            modname, clsname = split_clspath(clspath)
            component_name = clspath
            component_index = clsname
        else:
            component_name = "Configuration"
            component_index = "Configuration"

        # Add the docstring if there is one and if show-docstring
        if "show-docstring" in self.options:
            obj = module
            docstring_attr = self.options["show-docstring"] or "__doc__"
            docstring = getattr(obj, docstring_attr, "")
        else:
            docstring = ""

        self.generate_docs(
            component_name=component_name,
            component_index=component_index,
            docstring=docstring,
            sourcename=sourcename,
            option_data=option_data,
            more_content=self.content,
        )

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
    app.add_directive("autocomponentconfig", AutoComponentConfigDirective)
    app.add_directive("automoduleconfig", AutoModuleConfigDirective)

    return {
        "version": __version__,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
