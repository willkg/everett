from textwrap import dedent

from sphinx.cmd.build import main as sphinx_main

from everett.manager import ListOf, Option, parse_class


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
    .. everett:component:: test_sphinxext.ComponentDefaults

       :option str opt1: First option. Defaults to "foo".

    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentDefaults

           Options:
              **opt1** ("str") -- First option. Defaults to "foo".
        """
    )
    captured = capsys.readouterr()
    assert "WARNING" not in captured.out
    assert "WARNING" not in captured.err


class ComponentDefaults:
    class Config:
        user = Option()


def test_autocomponent_defaults(tmpdir):
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentDefaults
    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentDefaults

           Options:
              **user** ("str") --
        """
    )


def test_hide_classname(tmpdir):
    # Test classname
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentDefaults
       :hide-classname:

    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        Configuration

           Options:
              **user** ("str") --
        """
    )


def test_namespace(tmpdir):
    # Test namespace
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentDefaults
       :namespace: foo

    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentDefaults

           Options:
              **foo_user** ("str") --
        """
    )


class TestKeyCase:
    # Test case
    def test_bad_value(self, tmpdir):
        rst = dedent(
            """\
        .. autocomponent:: test_sphinxext.ComponentDefaults
           :case: foo

        """
        )

        # Because "foo" isn't valid, nothing ends up in the file
        assert run_sphinx(tmpdir, rst) == "\n"

        # FIXME(willkg): Verify an appropriate error was given to the user.
        # It's hard to do since it comes via stderr, but we probalby have to
        # find out where that code is and mock it directly.

    def test_lower(self, tmpdir):
        rst = dedent(
            """\
        .. autocomponent:: test_sphinxext.ComponentDefaults
           :case: lower

        """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component test_sphinxext.ComponentDefaults

               Options:
                  **user** ("str") --
            """
        )

    def test_upper(self, tmpdir):
        rst = dedent(
            """\
        .. autocomponent:: test_sphinxext.ComponentDefaults
           :case: upper

        """
        )

        assert run_sphinx(tmpdir, rst) == dedent(
            """\
            component test_sphinxext.ComponentDefaults

               Options:
                  **USER** ("str") --
            """
        )


def test_show_docstring_class_has_no_docstring(tmpdir):
    # Test docstring-related things
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentDefaults
       :show-docstring:

    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentDefaults

           Options:
              **user** ("str") --
        """
    )


class ComponentWithDocstring:
    """This component is the best.

    The best!

    """

    class Config:
        user = Option()


def test_show_docstring(tmpdir):
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentWithDocstring
       :show-docstring:

    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentWithDocstring

           This component is the best.

           The best!

           Options:
              **user** ("str") --
        """
    )


class ComponentDocstringOtherAttribute:
    """Programming-focused help"""

    __everett_help__ = """
        User-focused help
    """

    class Config:
        user = Option()


def test_show_docstring_other_attribute(tmpdir):
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentDocstringOtherAttribute
       :show-docstring: __everett_help__

    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentDocstringOtherAttribute

           User-focused help

           Options:
              **user** ("str") --
        """
    )


class ComponentSubclass(ComponentWithDocstring):
    """A different docstring"""


def test_show_docstring_subclass(tmpdir):
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentSubclass
       :show-docstring:

    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentSubclass

           A different docstring

           Options:
              **user** ("str") --
        """
    )


class ComponentOptionDefault:
    class Config:
        user = Option(default="ou812")


def test_option_default(tmpdir):
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentOptionDefault
    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentOptionDefault

           Options:
              **user** ("str") -- Defaults to "\'ou812\'".
        """
    )


class ComponentOptionDoc:
    class Config:
        user = Option(doc="ou812")


def test_option_doc(tmpdir):
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentOptionDoc
    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentOptionDoc

           Options:
              **user** ("str") -- ou812
        """
    )


class ComponentOptionDocMultiline:
    class Config:
        user = Option(doc="ou812")
        password = Option(doc="First ``paragraph``.\n\nSecond paragraph.")


def test_option_doc_multiline(tmpdir):
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentOptionDocMultiline
    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentOptionDocMultiline

           Options:
              * **user** ("str") -- ou812

              * **password** ("str") --

                First "paragraph".

                Second paragraph.
        """
    )


class ComponentOptionDocDefault:
    class Config:
        user = Option(doc="This is some docs.", default="ou812")


def test_option_doc_default(tmpdir):
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentOptionDocDefault
    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentOptionDocDefault

           Options:
              **user** ("str") --

              This is some docs.

              Defaults to "\'ou812\'".
        """
    )


class Foo:
    @classmethod
    def parse_foo_class(cls, value):
        pass

    def parse_foo_instance(self, value):
        pass


class ComponentOptionParser:
    class Config:
        user_builtin = Option(parser=int)
        user_parse_class = Option(parser=parse_class)
        user_listof = Option(parser=ListOf(str))
        user_class_method = Option(parser=Foo.parse_foo_class)
        user_instance_method = Option(parser=Foo().parse_foo_instance)


def test_option_parser(tmpdir):
    rst = dedent(
        """\
    .. autocomponent:: test_sphinxext.ComponentOptionParser
    """
    )

    assert run_sphinx(tmpdir, rst) == dedent(
        """\
        component test_sphinxext.ComponentOptionParser

           Options:
              * **user_builtin** ("int") --

              * **user_parse_class** ("everett.manager.parse_class") --

              * **user_listof** ("<ListOf(str)>") --

              * **user_class_method** ("test_sphinxext.Foo.parse_foo_class")
                --

              * **user_instance_method**
                ("test_sphinxext.Foo.parse_foo_instance") --
        """
    )
