import os
import logging
from typing import Union

import grpc
import requests_mock
import pytest
import botocore
from botocore.stub import Stubber

from src import utils
from src.clients import AWSClientFactory, RPCStubFactory
from src.handler import lambda_handler
from tests.stubs.http.aws import ListObjectsV2Stub, GetObjectStub
from tests.stubs.http.hydrosphere import ListModelsStub, ListModelVersionsStub
from tests.stubs.rpc.mocker import Mocker

session = botocore.session.get_session()
s3_client = AWSClientFactory.get_client('s3', session)


@staticmethod
def get_mocked_stub(service_stub, channel: Union[grpc.Channel, None] = None):
    channel = channel or RPCStubFactory._get_channel(os.environ["HYDROSPHERE_ENDPOINT"])
    return Mocker(service_stub(channel))

RPCStubFactory.get_stub = get_mocked_stub  # Mock gRPC calls for testing purposes


S3_DATA_CAPTURE_BUCKET = os.environ['S3_DATA_CAPTURE_BUCKET']
S3_DATA_CAPTURE_PREFIX = os.environ['S3_DATA_CAPTURE_PREFIX']
S3_DATA_TRAINING_BUCKET = os.environ['S3_DATA_TRAINING_BUCKET']
S3_DATA_TRAINING_PREFIX = os.environ['S3_DATA_TRAINING_PREFIX']
HYDROSPHERE_ENDPOINT = os.environ['HYDROSPHERE_ENDPOINT']

MODEL_NAME = "DEMO-xgb-churn-pred-model-monitor-2020-03-11-12-25-04"
TRAINING_KEY = f"{S3_DATA_TRAINING_PREFIX}/{MODEL_NAME}/training-dataset-with-header.csv"
CAPTURE_KEY = f"{S3_DATA_CAPTURE_PREFIX}/{MODEL_NAME}/AllTraffic/2020/03/11/12/32-18-648-cee08c3a-02ce-4790-b8ba-3173cfc12813.jsonl"
CAPTURE_SIZE = 2776


@pytest.fixture
def s3_event():
    return {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-2",
                "eventTime": "2020-03-11T12:46:24.913Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {
                    "principalId": "AWS:AROA5XGMCUEIEM5XIA5M4:SageMaker"
                },
                "requestParameters": {
                    "sourceIPAddress": "10.1.57.30"
                },
                "responseElements": {
                    "x-amz-request-id": "665202EF5C2DCB57",
                    "x-amz-id-2": "dO6fzj/TZHJq9JvLGGGgmZt3BW9+2l26YVWcDcZpPKVvXcYKSNLbxEZXqVs5hynKxmOOHt/bbpfvYc1EpXgps3cdDfCiTOYtMO9cTdxnJMg="
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "96813b24-32d9-47fb-8766-17f96113168f",
                    "bucket": {
                        "name": S3_DATA_CAPTURE_BUCKET,
                        "ownerIdentity": {
                            "principalId": "AYOFZ9JA3UDEA"
                        },
                        "arn": f"arn:aws:s3:::{S3_DATA_CAPTURE_BUCKET}"
                    },
                    "object": {
                        "key": CAPTURE_KEY,
                        "size": CAPTURE_SIZE,
                        "eTag": "ce232e54888d676f0446cc43da864f57",
                        "sequencer": "005E68DDA0CEAB1436"
                    }
                }
            }
        ]
    }


def test_lambda_handler(caplog, s3_event: dict):
    caplog.set_level(logging.DEBUG)
    transformed_model_name = utils.transform_model_name(MODEL_NAME)

    with Stubber(s3_client) as s3_stubber:
        with requests_mock.mock() as mock:
            model_version_id = 33
            # Stub ListObjectsV2 API call to list training data
            # bucket to find the biggest csv file
            s3_stubber.add_response(
                **ListObjectsV2Stub(
                    S3_DATA_TRAINING_BUCKET,
                    f"{S3_DATA_TRAINING_PREFIX}/{MODEL_NAME}"
                ).generate_response()
            )

            # Stub GetObject API call to read first line of
            # production request data to infer schema
            s3_stubber.add_response(
                **GetObjectStub(
                    S3_DATA_CAPTURE_BUCKET,
                    CAPTURE_KEY,
                    'aws/traffic_shadowing/tests/file.jsonl'
                ).generate_response()
            )

            # Stub GetObject API call to read first line of
            # training data to adjust inferred schema
            s3_stubber.add_response(
                **GetObjectStub(
                    S3_DATA_TRAINING_BUCKET,
                    TRAINING_KEY,
                    'aws/traffic_shadowing/tests/file.csv'
                ).generate_response()
            )

            # Stub Hydrosphere API to list existing models
            mock.get(
                **ListModelsStub(transformed_model_name).generate_response()
            )

            # Stub Hydrosphere API to fetch existing model version
            mock.get(
                **ListModelVersionsStub(
                    MODEL_NAME,
                    transformed_model_name,
                    model_version_id=model_version_id,
                ).generate_response()
            )

            # Stub GetObject API call to read all file containing
            # captured requests for analysis.
            s3_stubber.add_response(
                **GetObjectStub(
                    S3_DATA_CAPTURE_BUCKET,
                    CAPTURE_KEY,
                    'aws/traffic_shadowing/tests/file.jsonl'
                ).generate_response()
            )

            result = lambda_handler(s3_event, "", session)
            assert result["statusCode"] == 200
