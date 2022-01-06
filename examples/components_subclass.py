# components_subclass.py

from everett.manager import ConfigManager, Option


class ComponentA:
    class Config:
        foo = Option(default="foo_from_a")
        bar = Option(default="bar_from_a")


class ComponentB(ComponentA):
    class Config:
        foo = Option(default="foo_from_b")

    def __init__(self, config):
        self.config = config.with_options(self)


config = ConfigManager.basic_config()
compb = ComponentB(config)

print(compb.config("foo"))
print(compb.config("bar"))
