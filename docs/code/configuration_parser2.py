from everett.manager import ConfigManager, get_parser


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
