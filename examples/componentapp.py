# componentapp.py

from everett.manager import ConfigManager, Option


class S3Bucket:
    class Config:
        region = Option(doc="AWS S3 region")
        bucket_name = Option(doc="AWS S3 bucket name")

    def __init__(self, config):
        # Bind the configuration to just the configuration this component
        # requires such that this component is self-contained
        self.config = config.with_options(self)

        self.region = self.config("region")
        self.bucket_name = self.config("bucket_name")

    def repr(self):
        return f"<S3Bucket {self.region} {self.bucket_name}>"


config = ConfigManager.from_dict(
    {
        "S3_SOURCE_REGION": "us-east-1",
        "S3_SOURCE_BUCKET_NAME": "mycompany_oldbucket",
        "S3_DEST_REGION": "us-east-1",
        "S3_DEST_BUCKET_NAME": "mycompany_newbucket",
    }
)

s3_config = config.with_namespace("s3")

source_bucket = S3Bucket(s3_config.with_namespace("source"))
dest_bucket = S3Bucket(s3_config.with_namespace("dest"))

print(repr(source_bucket))
print(repr(dest_bucket))
