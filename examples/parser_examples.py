# parser_examples.py

from everett.manager import ConfigManager, get_parser


def parse_ynm(val):
    """Returns True, False or None (empty string)"""
    val = val.strip().lower()
    if not val:
        return None

    return val[0] == "y"


config = ConfigManager.from_dict(
    {"NO_ANSWER": "", "YES": "yes", "ALSO_YES": "y", "NO": "no"}
)

assert config("no_answer", parser=parse_ynm) is None
assert config("yes", parser=parse_ynm) is True
assert config("also_yes", parser=parse_ynm) is True
assert config("no", parser=parse_ynm) is False


class Pairs(object):
    def __init__(self, val_parser):
        self.val_parser = val_parser

    def __call__(self, val):
        val_parser = get_parser(self.val_parser)
        out = []
        for part in val.split(","):
            k, v = part.split(":")
            out.append((k, val_parser(v)))
        return out


config = ConfigManager.from_dict({"FOO": "a:1,b:2,c:3"})

assert config("FOO", parser=Pairs(int)) == [("a", 1), ("b", 2), ("c", 3)]
