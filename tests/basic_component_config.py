"""Basic component config."""

from everett.manager import ListOf, Option, parse_class


class ComponentBasic:
    """Basic component.

    Multiple lines.

    """

    HELP = "Help attribute value."

    class Config:
        user = Option()


class ComponentSubclass(ComponentBasic):
    """A different docstring."""


class ComponentOptionDefault:
    class Config:
        user = Option(default="ou812")


class ComponentOptionDoc:
    class Config:
        user = Option(doc="ou812")


class ComponentOptionDocMultiline:
    class Config:
        user = Option(doc="ou812")
        password = Option(doc="First ``paragraph``.\n\nSecond paragraph.")


class ComponentOptionDocDefault:
    class Config:
        user = Option(doc="This is some docs.", default="ou812")


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


class ComponentWithDocstring:
    """This component is the best.

    The best!

    """

    class Config:
        user = Option()


class ComponentDocstringOtherAttribute:
    """Programming-focused help"""

    __everett_help__ = """
        User-focused help
    """

    class Config:
        user = Option()
