# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Test sphinxext directives."""

import sys
from textwrap import dedent

import pytest
from sphinx.cmd.build import main as sphinx_main


def run_sphinx(docsdir, text, builder="text"):
    # set up conf.py
    with open(str(docsdir / "conf.py"), "w") as fp:
        fp.write('master_doc = "index"\n')
        fp.write('extensions = ["everett.sphinxext"]\n')

    # set up index.rst file
    text = "BEGINBEGIN\n\n%s\n\nENDEND" % text
    with open(str(docsdir / "index.rst"), "w") as fp:
        fp.write(text)

    args = ["-b", builder, "-v", "-E", str(docsdir), str(docsdir / "_build" / builder)]
    print(args)
    if sphinx_main(args):
        raise RuntimeError("Sphinx build failed")

    extension = "txt" if builder == "text" else "html"
    with open(
        str(docsdir / "_build" / builder / f"index.{extension}"), encoding="utf8"
    ) as fp:
        data = fp.read()

    # index.text has a bunch of stuff in it. BEGINBEGIN and ENDEND are markers,
    # so we just return the bits in between.
    data = data[data.find("BEGINBEGIN") + 10 : data.find("ENDEND")]
    # Strip the whitespace, but add a \n to make tests easier to read.
    data = data.strip() + "\n"
    return data


def test_infrastructure(tmpdir):
    # Verify parsing is working at all. This seems like a no-op, but really
    # it's going through all the Sphinx stuff to generate the text that it
    # started off with.
    assert run_sphinx(tmpdir, "*foo*") == dedent(
        """\
        *foo*
        """
    )


def test_everett_component(tmpdir, capsys):
    # Test .. everett:component:: with an option and verify Sphinx isn't
    # spitting out warnings
    rst = dedent(
        """\
    .. everett:component:: mymodule.ComponentBasic

       .. everett:option:: opt1
          :parser: str
          :default: "foo"

          First option.

    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component mymodule.ComponentBasic

           opt1

              Parser:
                 *str*

              Default:
                 "foo"

              Required:
                 No

              First option.
        """
    )
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert "WARNING" not in captured.err


class Test_autocomponentconfig:
    def test_basic(self, tmpdir, capsys):
        rst = dedent(
            """\
        .. autocomponentconfig:: basic_component_config.ComponentBasic
        """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentBasic

               user

                  Parser:
                     *str*

                  Required:
                     Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_hide_name(self, tmpdir, capsys):
        # Test hide-name
        rst = dedent(
            """\
        .. autocomponentconfig:: basic_component_config.ComponentBasic
           :hide-name:

        """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            Configuration

               user

                  Parser:
                     *str*

                  Required:
                     Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_namespace(self, tmpdir, capsys):
        rst = dedent(
            """\
        .. autocomponentconfig:: basic_component_config.ComponentBasic
           :namespace: foo

        """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentBasic

               foo_user

                  Parser:
                     *str*

                  Required:
                     Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_case_bad_value(self, tmpdir, capsys):
        rst = dedent(
            """\
        .. autocomponentconfig:: basic_component_config.ComponentBasic
           :case: foo

        """
        )

        # Because "foo" isn't valid, nothing ends up in the file
        assert run_sphinx(tmpdir, rst) == "\n"
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert 'argument must be "upper", "lower" or None.' in captured.err

    def test_case_lower(self, tmpdir, capsys):
        rst = dedent(
            """\
        .. autocomponentconfig:: basic_component_config.ComponentBasic
           :case: lower

        """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentBasic

               user

                  Parser:
                     *str*

                  Required:
                     Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_case_upper(self, tmpdir, capsys):
        rst = dedent(
            """\
        .. autocomponentconfig:: basic_component_config.ComponentBasic
           :case: upper

        """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentBasic

               USER

                  Parser:
                     *str*

                  Required:
                     Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_show_docstring_class_has_no_docstring(self, tmpdir, capsys):
        # Test docstring-related things
        rst = dedent(
            """\
            .. autocomponentconfig:: basic_component_config.ComponentBasic
               :show-docstring:

            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentBasic

               Basic component.

               Multiple lines.

               user

                  Parser:
                     *str*

                  Required:
                     Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_show_docstring(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. autocomponentconfig:: basic_component_config.ComponentWithDocstring
               :show-docstring:

            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentWithDocstring

               This component is the best.

               The best!

               user

                  Parser:
                     *str*

                  Required:
                     Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_show_docstring_other_attribute(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. autocomponentconfig:: basic_component_config.ComponentDocstringOtherAttribute
               :show-docstring: __everett_help__

            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentDocstringOtherAttribute

               User-focused help

               user

                  Parser:
                     *str*

                  Required:
                     Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_show_docstring_subclass(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. autocomponentconfig:: basic_component_config.ComponentSubclass
               :show-docstring:

        """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentSubclass

               A different docstring.

               user

                  Parser:
                     *str*

                  Required:
                     Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_option_default(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. autocomponentconfig:: basic_component_config.ComponentOptionDefault
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentOptionDefault

               user

                  Parser:
                     *str*

                  Default:
                     "ou812"

                  Required:
                     No
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_option_doc(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. autocomponentconfig:: basic_component_config.ComponentOptionDoc
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentOptionDoc

               user

                  Parser:
                     *str*

                  Required:
                     Yes

                  ou812
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_option_doc_multiline(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. autocomponentconfig:: basic_component_config.ComponentOptionDocMultiline
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentOptionDocMultiline

               user

                  Parser:
                     *str*

                  Required:
                     Yes

                  ou812

               password

                  Parser:
                     *str*

                  Required:
                     Yes

                  First "paragraph".

                  Second paragraph.
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_option_doc_default(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. autocomponentconfig:: basic_component_config.ComponentOptionDocDefault
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentOptionDocDefault

               user

                  Parser:
                     *str*

                  Default:
                     "ou812"

                  Required:
                     No

                  This is some docs.
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_option_parser(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. autocomponentconfig:: basic_component_config.ComponentOptionParser
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_component_config.ComponentOptionParser

               user_builtin

                  Parser:
                     *int*

                  Required:
                     Yes

               user_parse_class

                  Parser:
                     *everett.manager.parse_class*

                  Required:
                     Yes

               user_listof

                  Parser:
                     *<ListOf(str)>*

                  Required:
                     Yes

               user_class_method

                  Parser:
                     *basic_component_config.Foo.parse_foo_class*

                  Required:
                     Yes

               user_instance_method

                  Parser:
                     *basic_component_config.Foo.parse_foo_instance*

                  Required:
                     Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err


@pytest.mark.skipif(
    # NOTE(willkg): The automodule stuff doesn't work with Python < 3.8 because
    # ast.get_source_segment() isn't available.
    sys.version_info < (3, 8),
    reason="requires Python 3.8 or higher",
)
class Test_automoduleconfig:
    def test_basic(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. automoduleconfig:: basic_module_config._config
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component basic_module_config._config

               debug

                  Parser:
                     *bool*

                  Default:
                     "False"

                  Required:
                     No

                  Debug mode.

               logging_level

                  Parser:
                     *parse_logging_level*

                  Required:
                     Yes

                  Level.

               password

                  Parser:
                     *str*

                  Required:
                     Yes

                  Password field.

                  Must be provided.

               fun

                  Parser:
                     *int if 0 else float*

                  Required:
                     Yes

                  Woah.
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_hide_name(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. automoduleconfig:: simple_module_config._config
               :hide-name:
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            Configuration

               host

                  Parser:
                     *str*

                  Default:
                     "localhost"

                  Required:
                     No

                  The host.
            """
        )

    def test_namespace(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. automoduleconfig:: simple_module_config._config
               :namespace: app
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component simple_module_config._config

               app_host

                  Parser:
                     *str*

                  Default:
                     "localhost"

                  Required:
                     No

                  The host.
            """
        )

    def test_case_upper(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. automoduleconfig:: simple_module_config._config
               :case: upper
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component simple_module_config._config

               HOST

                  Parser:
                     *str*

                  Default:
                     "localhost"

                  Required:
                     No

                  The host.
            """
        )

    def test_case_lower(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. automoduleconfig:: simple_module_config._config
               :case: lower
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component simple_module_config._config

               host

                  Parser:
                     *str*

                  Default:
                     "localhost"

                  Required:
                     No

                  The host.
            """
        )

    def test_show_table(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. automoduleconfig:: simple_module_config._config
               :show-table:
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component simple_module_config._config

               Configuration summary:

               +--------------------------------------------------------------+----------+-------------+
               | Setting                                                      | Parser   | Required?   |
               |==============================================================|==========|=============|
               | "host"                                                       | *str*    |             |
               +--------------------------------------------------------------+----------+-------------+

               Configuration options:

               host

                  Parser:
                     *str*

                  Default:
                     "localhost"

                  Required:
                     No

                  The host.
            """
        )

    def test_show_docstring(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. automoduleconfig:: simple_module_config._config
               :show-docstring:
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component simple_module_config._config

               Simple module config.

               host

                  Parser:
                     *str*

                  Default:
                     "localhost"

                  Required:
                     No

                  The host.
            """
        )

    def test_show_docstring_by_attribute(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. automoduleconfig:: simple_module_config._config
               :show-docstring: HELP
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component simple_module_config._config

               Help attribute value.

               host

                  Parser:
                     *str*

                  Default:
                     "localhost"

                  Required:
                     No

                  The host.
            """
        )


class Test_everett_option:
    def test_basic(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. everett:option:: debug
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            debug

               Parser:
                  *str*

               Required:
                  Yes
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err

    def test_thorough(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. everett:option:: debug
               :parser: bool
               :default: "false"

               Set to "true" for debug mode
            """
        )
        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            debug

               Parser:
                  *bool*

               Default:
                  "false"

               Required:
                  No

               Set to "true" for debug mode
            """
        )

    def test_no_default_means_required(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. everett:option:: debug
               :parser: bool

               Set to "true" for debug mode
            """
        )
        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            debug

               Parser:
                  *bool*

               Required:
                  Yes

               Set to "true" for debug mode
            """
        )


class Test_everett_component:
    def test_basic(self, tmpdir, capsys):
        rst = dedent(
            """\
            .. everett:component:: MyClass

               Some details about my class.

               .. everett:option:: debug
                  :parser: bool

                  Set to "true" for debug mode
            """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component MyClass

               Some details about my class.

               debug

                  Parser:
                     *bool*

                  Required:
                     Yes

                  Set to "true" for debug mode
            """
        )
        captured = capsys.readouterr()
        assert "WARNING" not in captured.out
        assert "WARNING" not in captured.err
