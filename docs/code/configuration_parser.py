from everett.manager import ConfigManager


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
