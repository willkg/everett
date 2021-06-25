import os

from everett.manager import ConfigManager, Option, parse_class


class App:
    class Config:
        basedir = Option()
        reader = Option(parser=parse_class)
        writer = Option(parser=parse_class)

    def __init__(self, config):
        self.config = config.with_options(self)

        self.basedir = self.config("basedir")
        self.reader = self.config("reader")(config, self.basedir)
        self.writer = self.config("writer")(config, self.basedir)


class FilesystemReader:
    class Config:
        file_type = Option(default="json")

    def __init__(self, config, basedir):
        self.config = config.with_options(self)
        self.read_dir = os.path.join(basedir, "read")


class FilesystemWriter:
    class Config:
        file_type = Option(default="json")

    def __init__(self, config, basedir):
        self.config = config.with_options(self)
        self.write_dir = os.path.join(basedir, "write")


config = ConfigManager.from_dict(
    {
        "BASEDIR": "/tmp",
        "READER": "__main__.FilesystemReader",
        "WRITER": "__main__.FilesystemWriter",
        "READER_FILE_TYPE": "json",
        "WRITER_FILE_TYPE": "yaml",
    }
)


app = App(config)
assert app.reader.read_dir == "/tmp/read"
assert app.writer.write_dir == "/tmp/write"
