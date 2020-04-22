import os
import boto3
from src.clients import AWSClientFactory
from src.data import SchemaDescription, ColumnDescription


session = boto3.session.Session()
s3_client = AWSClientFactory.get_or_create_client('s3', session)

HYDROSPHERE_ENDPOINT = os.environ["HYDROSPHERE_ENDPOINT"]
MODEL_NAME = "DEMO-xgb-churn-pred-model-monitor-2020-03-11-12-25-04"
VALID_MODEL_NAME = "demo-xgb-churn-pred-model-monitor-2020-03-11-12-25-04"
MODEL_VERSION_ID = 33
CAPTURE_BUCKET = os.environ['S3_DATA_CAPTURE_BUCKET']
CAPTURE_PREFIX = os.environ['S3_DATA_CAPTURE_PREFIX']
TRAIN_BUCKET = os.environ['S3_DATA_TRAINING_BUCKET']
TRAIN_PREFIX = os.environ['S3_DATA_TRAINING_PREFIX']
CAPTURE_KEY = f"{CAPTURE_PREFIX}/{MODEL_NAME}/file.jsonl"
CAPTURE_SIZE = 760
CAPTURE_FILENAME = "aws/traffic_shadowing/tests/file.jsonl"
TRAIN_KEY = f"{TRAIN_PREFIX}/{MODEL_NAME}/file.csv"
TRAIN_KEY_FULL = f"s3://{TRAIN_BUCKET}/{TRAIN_PREFIX}/{MODEL_NAME}/file.csv"
TRAIN_FILENAME = "aws/traffic_shadowing/tests/file.csv"


S3_EVENT = {
    "Records": [
        {
            "eventVersion": "2.1",
            "eventSource": "aws:s3",
            "awsRegion": "us-east-2",
            "eventTime": "2020-03-11T12:46:24.913Z",
            "eventName": "ObjectCreated:Put",
            "userIdentity": {
                "principalId": "AWS:xxxxxxxxxxxxxxxxxxxx:SageMaker"
            },
            "requestParameters": {
                "sourceIPAddress": "192.168.0.1"
            },
            "responseElements": {
                "x-amz-request-id": "xxxxxxxxxxxxxxxx",
                "x-amz-id-2": "xxxxxx/xxxxxxxxxxxxxxxxxxxx+xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx="
            },
            "s3": {
                "s3SchemaVersion": "1.0",
                "configurationId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
                "bucket": {
                    "name": CAPTURE_BUCKET,
                    "ownerIdentity": {
                        "principalId": "xxxxxxxxxxxxx"
                    },
                    "arn": f"arn:aws:s3:::{CAPTURE_BUCKET}"
                },
                "object": {
                    "key": CAPTURE_KEY,
                    "size": CAPTURE_SIZE,
                    "eTag": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
                    "sequencer": "xxxxxxxxxxxxxxxxxx"
                }
            }
        }
    ]
}

SCHEMA = SchemaDescription(
    inputs=[
        ColumnDescription(
            name="Account Length",
            dtype="int64",
            htype="DT_INT64",
            shape=()
        ),
        ColumnDescription(
            name="VMail Message",
            dtype="float64",
            htype="DT_DOUBLE",
            shape=()
        ),
        ColumnDescription(
            name="Day Mins",
            dtype="float64",
            htype="DT_DOUBLE",
            shape=()
        ),
        ColumnDescription(
            name="Day Calls",
            dtype="int64",
            htype="DT_INT64",
            shape=()
        )
    ],
    outputs=[
        ColumnDescription(
            name="Churn",
            dtype="float64",
            htype="DT_DOUBLE",
            shape=()
        )
    ]
)
