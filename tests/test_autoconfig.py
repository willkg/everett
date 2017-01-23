from textwrap import dedent

from sphinx.application import Sphinx

from everett.component import (
    RequiredConfigMixin,
    ConfigOptions,
)
from everett.manager import ListOf, parse_class


class FakeSphinx(Sphinx):
    """Fake Sphinx app that has better defaults"""
    def __init__(self, tmpdir):
        srcdir = tmpdir
        confdir = tmpdir
        outdir = tmpdir / '_build' / 'text'
        doctreedir = tmpdir / 'doctree'

        with open(str(confdir / 'conf.py'), 'w') as fp:
            fp.write('master_doc = "index"')

        super(FakeSphinx, self).__init__(
            srcdir=str(srcdir),
            confdir=str(confdir),
            outdir=str(outdir),
            doctreedir=str(doctreedir),
            buildername='text',
            freshenv=True,
        )


def parse(tmpdir, text):
    fakesphinx = FakeSphinx(tmpdir)
    fakesphinx.setup_extension('everett.sphinx_autoconfig')

    text = 'BEGINBEGIN\n\n%s\n\nENDEND' % text

    with open(str(tmpdir / 'index.rst'), 'w') as fp:
        fp.write(text)

    fakesphinx.builder.build_all()

    with open(str(tmpdir / '_build/text/index.txt'), 'r') as fp:
        data = fp.read()

    # index.text has a bunch of stuff in it. BEGINBEGIN and ENDEND are markers,
    # so we just return the bits in between.
    data = data[data.find('BEGINBEGIN') + 10:data.find('ENDEND')]
    # Strip the whitespace, but add a \n to make tests easier to read.
    data = data.strip() + '\n'
    return data


def test_infrastructure(tmpdir):
    # Verify parsing is working at all. This seems like a no-op, but really
    # it's going through all the Sphinx stuff to generate the text that it
    # started off with.
    assert (
        parse(tmpdir, '*foo*') ==
        dedent('''\
        *foo*
        ''')
    )


class ComponentDefaults(RequiredConfigMixin):
    required_config = ConfigOptions()
    required_config.add_option('user')

    def __init__(self, config):
        self.config = config.with_options(self)


# Test defaults


def test_defaults(tmpdir):
    rst = dedent('''\
    .. autoconfig:: test_autoconfig.ComponentDefaults
    ''')

    assert (
        parse(tmpdir, rst) ==
        dedent('''\
        class test_autoconfig.ComponentDefaults

           Configuration:

              "user"
                 default:
                 parser:
                    str
        ''')
    )


# Test classname


def test_hide_classname(tmpdir):
    rst = dedent('''\
    .. autoconfig:: test_autoconfig.ComponentDefaults
       :hide-classname:

    ''')

    assert (
        parse(tmpdir, rst) ==
        dedent('''\
        Configuration:

           "user"
              default:
              parser:
                 str
        ''')
    )


# Test namespace


def test_namespace(tmpdir):
    rst = dedent('''\
    .. autoconfig:: test_autoconfig.ComponentDefaults
       :namespace: foo

    ''')

    assert (
        parse(tmpdir, rst) ==
        dedent('''\
        class test_autoconfig.ComponentDefaults

           Configuration:

              "foo_user"
                 default:
                 parser:
                    str
        ''')
    )


# Test case


class TestKeyCase:
    def test_bad_value(self, tmpdir):
        rst = dedent('''\
        .. autoconfig:: test_autoconfig.ComponentDefaults
           :case: foo

        ''')

        # Because "foo" isn't valid, nothing ends up in the file
        assert parse(tmpdir, rst) == '\n'

        # FIXME(willkg): Verify an appropriate error was given to the user.
        # It's hard to do since it comes via stderr, but we probalby have to
        # find out where that code is and mock it directly.

    def test_lower(self, tmpdir):
        rst = dedent('''\
        .. autoconfig:: test_autoconfig.ComponentDefaults
           :case: lower

        ''')

        assert (
            parse(tmpdir, rst) ==
            dedent('''\
            class test_autoconfig.ComponentDefaults

               Configuration:

                  "user"
                     default:
                     parser:
                        str
            ''')
        )

    def test_upper(self, tmpdir):
        rst = dedent('''\
        .. autoconfig:: test_autoconfig.ComponentDefaults
           :case: upper

        ''')

        assert (
            parse(tmpdir, rst) ==
            dedent('''\
            class test_autoconfig.ComponentDefaults

               Configuration:

                  "USER"
                     default:
                     parser:
                        str
            ''')
        )


# Test docstring-related things


def test_show_docstring_class_has_no_docstring(tmpdir):
    rst = dedent('''\
    .. autoconfig:: test_autoconfig.ComponentDefaults
       :show-docstring:

    ''')

    assert (
        parse(tmpdir, rst) ==
        dedent('''\
        class test_autoconfig.ComponentDefaults

           Configuration:

              "user"
                 default:
                 parser:
                    str
        ''')
    )


class ComponentWithDocstring(RequiredConfigMixin):
    """This component is the best.

    The best!

    """
    required_config = ConfigOptions()
    required_config.add_option('user')

    def __init__(self, config):
        self.config = config.with_options(self)


def test_show_docstring(tmpdir):
    rst = dedent('''\
    .. autoconfig:: test_autoconfig.ComponentWithDocstring
       :show-docstring:

    ''')

    assert (
        parse(tmpdir, rst) ==
        dedent('''\
        class test_autoconfig.ComponentWithDocstring

           This component is the best.

           The best!

           Configuration:

              "user"
                 default:
                 parser:
                    str
        ''')
    )


class ComponentDocstringOtherAttribute(RequiredConfigMixin):
    """Programming-focused help"""

    __everett_help__ = """
        User-focused help
    """

    required_config = ConfigOptions()
    required_config.add_option('user')

    def __init__(self, config):
        self.config = config.with_options(self)


def test_show_docstring_other_attribute(tmpdir):
    rst = dedent('''\
    .. autoconfig:: test_autoconfig.ComponentDocstringOtherAttribute
       :show-docstring: __everett_help__

    ''')

    assert (
        parse(tmpdir, rst) ==
        dedent('''\
        class test_autoconfig.ComponentDocstringOtherAttribute

           User-focused help

           Configuration:

              "user"
                 default:
                 parser:
                    str
        ''')
    )


class ComponentSubclass(ComponentWithDocstring):
    """A different docstring"""


def test_show_docstring_subclass(tmpdir):
    rst = dedent('''\
    .. autoconfig:: test_autoconfig.ComponentSubclass
       :show-docstring:

    ''')

    assert (
        parse(tmpdir, rst) ==
        dedent('''\
        class test_autoconfig.ComponentSubclass

           A different docstring

           Configuration:

              "user"
                 default:
                 parser:
                    str
        ''')
    )


# Test configuration-related things


class ComponentOptionDefault(RequiredConfigMixin):
    required_config = ConfigOptions()
    required_config.add_option(
        'user',
        default='ou812'
    )


def test_option_default(tmpdir):
    rst = dedent('''\
    .. autoconfig:: test_autoconfig.ComponentOptionDefault
    ''')

    assert (
        parse(tmpdir, rst) ==
        dedent('''\
        class test_autoconfig.ComponentOptionDefault

           Configuration:

              "user"
                 default:
                    "\'ou812\'"

                 parser:
                    str
        ''')
    )


class ComponentOptionDoc(RequiredConfigMixin):
    required_config = ConfigOptions()
    required_config.add_option(
        'user',
        doc='ou812'
    )


def test_option_doc(tmpdir):
    rst = dedent('''\
    .. autoconfig:: test_autoconfig.ComponentOptionDoc
    ''')

    assert (
        parse(tmpdir, rst) ==
        dedent('''\
        class test_autoconfig.ComponentOptionDoc

           Configuration:

              "user"
                 default:
                 parser:
                    str

                 ou812
        ''')
    )


class Foo(object):
    @classmethod
    def parse_foo_class(cls, value):
        pass

    def parse_foo_instance(self, value):
        pass


class ComponentOptionParser(RequiredConfigMixin):
    required_config = ConfigOptions()
    required_config.add_option(
        'user_builtin',
        parser=int
    )
    required_config.add_option(
        'user_parse_class',
        parser=parse_class
    )
    required_config.add_option(
        'user_listof',
        parser=ListOf(str)
    )
    required_config.add_option(
        'user_class_method',
        parser=Foo.parse_foo_class
    )
    required_config.add_option(
        'user_instance_method',
        parser=Foo().parse_foo_instance
    )


def test_option_parser(tmpdir):
    rst = dedent('''\
    .. autoconfig:: test_autoconfig.ComponentOptionParser
    ''')

    assert (
        parse(tmpdir, rst) ==
        dedent('''\
        class test_autoconfig.ComponentOptionParser

           Configuration:

              "user_builtin"
                 default:
                 parser:
                    int

              "user_parse_class"
                 default:
                 parser:
                    everett.manager.parse_class

              "user_listof"
                 default:
                 parser:
                    <ListOf(str)>

              "user_class_method"
                 default:
                 parser:
                    test_autoconfig.Foo.parse_foo_class

              "user_instance_method"
                 default:
                 parser:
                    test_autoconfig.Foo.parse_foo_instance
        ''')
    )
