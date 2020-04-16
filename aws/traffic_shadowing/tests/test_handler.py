# pylint: disable=protected-access,missing-function-docstring
import os
from typing import Union

import grpc
import requests_mock
from botocore.stub import Stubber

from src.clients import RPCStubFactory
from src.handler import lambda_handler
from tests.stubs.http.aws import ListObjectsV2Stub, GetObjectStub
from tests.stubs.http.hydrosphere import ListModelsStub, ListModelVersionsStub
from tests.stubs.rpc.mocker import Mocker
from tests.config import session, s3_client
from tests.config import (
    MODEL_NAME, VALID_MODEL_NAME, MODEL_VERSION_ID, CAPTURE_KEY, TRAIN_KEY,
    TRAIN_FILENAME, CAPTURE_FILENAME, S3_EVENT, TRAIN_BUCKET, CAPTURE_BUCKET,
    TRAIN_PREFIX,
)


@staticmethod
def create_mocked_stub(service_stub, channel: Union[grpc.Channel, None] = None):
    channel = channel or RPCStubFactory._create_channel(os.environ["HYDROSPHERE_ENDPOINT"])
    return Mocker(service_stub(channel))

RPCStubFactory.create_stub = create_mocked_stub  # Mock gRPC calls for testing purposes


def test_lambda_handler():
    with Stubber(s3_client) as s3_stubber:
        with requests_mock.mock() as mock:
            # Stub ListObjectsV2 API call to list training data
            # bucket to find the biggest csv file
            s3_stubber.add_response(
                **ListObjectsV2Stub(
                    TRAIN_BUCKET,
                    f"{TRAIN_PREFIX}/{MODEL_NAME}"
                ).generate_response()
            )

            # Stub GetObject API call to read first line of
            # production request data to infer schema
            s3_stubber.add_response(
                **GetObjectStub(
                    CAPTURE_BUCKET,
                    CAPTURE_KEY,
                    CAPTURE_FILENAME,
                ).generate_response()
            )

            # Stub GetObject API call to read first line of
            # training data to adjust inferred schema
            s3_stubber.add_response(
                **GetObjectStub(
                    TRAIN_BUCKET,
                    TRAIN_KEY,
                    TRAIN_FILENAME
                ).generate_response()
            )

            # Stub Hydrosphere API to list existing models
            mock.get(
                **ListModelsStub(VALID_MODEL_NAME).generate_response()
            )

            # Stub Hydrosphere API to fetch existing model version
            mock.get(
                **ListModelVersionsStub(
                    MODEL_NAME,
                    VALID_MODEL_NAME,
                    model_version_id=MODEL_VERSION_ID,
                ).generate_response()
            )

            # Stub GetObject API call to read all file containing
            # captured requests for analysis.
            s3_stubber.add_response(
                **GetObjectStub(
                    CAPTURE_BUCKET,
                    CAPTURE_KEY,
                    CAPTURE_FILENAME
                ).generate_response()
            )

            result = lambda_handler(S3_EVENT, "", session)
            assert result["statusCode"] == 200
