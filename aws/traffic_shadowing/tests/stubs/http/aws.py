# pylint: disable=missing-function-docstring,missing-class-docstring
import os
import datetime
from io import BytesIO
from dateutil.tz import tzutc
from botocore.response import StreamingBody
from tests.stubs.http.base import StubBase


class ListObjectsV2Stub(StubBase):
    method = 'list_objects_v2'

    def __init__(self, bucket: str, prefix: str):
        self.bucket = bucket
        self.prefix = prefix

    @property
    def expected_params(self) -> dict:
        return {
            "Bucket": self.bucket,
            "Prefix": self.prefix,
        }

    @property
    def service_response(self) -> dict:
        return {
            'IsTruncated': False,
            'Contents': [
                {
                    'Key': f'{self.prefix}/file.csv',
                    'LastModified': datetime.datetime(2020, 3, 11, 12, 33, 25, tzinfo=tzutc()),
                    'ETag': '"0ddd8b2d8653a3ad0cf6472ac79de46f"',
                    'Size': 1010,
                    'StorageClass': 'STANDARD'
                },
            ],
            'Name': self.bucket,
            'Prefix': self.prefix,
            'MaxKeys': 1000,
            'EncodingType': 'url',
            'KeyCount': 1
        }


class GetObjectStub(StubBase):
    method = 'get_object'

    def __init__(self, bucket: str, key: str, filename: str):
        self.bucket = bucket
        self.key = key
        self.filename = filename

    @property
    def expected_params(self) -> dict:
        return {
            "Bucket": self.bucket,
            "Key": self.key,
        }

    @property
    def service_response(self) -> dict:
        with open(self.filename, 'rb') as file:
            raw_stream = StreamingBody(
                BytesIO(file.read()),
                os.stat(self.filename).st_size
            )
        return {
            'Body': raw_stream
        }
