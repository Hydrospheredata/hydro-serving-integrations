# pylint: disable=redefined-outer-name
# pylint: disable=protected-access
import os
import pytest
import botocore
import requests_mock
from src.clients import AWSClientFactory
from src.model_pool import ModelPool
from src.errors import ModelNotFound, DataUploadFailed, TimeOut, ApiNotAvailable
from tests.stubs.http.hydrosphere import (
    ListModelsStub, ListModelVersionsStub, RegisterExternalModelStub,
    UploadTrainingDataStub, WaitTrainingDataProcessingStub,
)
from tests.test_data import schema # pylint: disable=unused-import


session = botocore.session.get_session()
s3_client = AWSClientFactory.get_client('s3', session)


@pytest.fixture
def model_name():
    return "Model-name"


@pytest.fixture
def valid_model_name():
    return "model-name"


@pytest.fixture
def endpoint():
    return os.environ["HYDROSPHERE_ENDPOINT"]


@pytest.fixture
def training_file_uri():
    return "s3://bucket/path/to/key.csv"


def test_create_model(valid_model_name, training_file_uri, schema, endpoint):
    with requests_mock.mock(real_http=False) as mock:
        model_version_id = 1
        mock.post(**RegisterExternalModelStub(
            valid_model_name,
            model_version_id=model_version_id,
        ).generate_response())
        mock.post(**UploadTrainingDataStub(
            training_file_uri,
            model_version_id=model_version_id,
        ).generate_response())
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Success",
            model_version_id=model_version_id,
        ).generate_response())
        pool = ModelPool(endpoint)
        model = pool.create_model(valid_model_name, schema, training_file_uri)
        assert model.model_version_id == model_version_id


def test_get_or_create_model(
        valid_model_name,
        model_name,
        training_file_uri,
        schema,
        endpoint,
):
    with requests_mock.mock(real_http=False) as mock:
        model_version_id = 1
        mock.get(**ListModelsStub().generate_response())
        mock.get(**ListModelVersionsStub(
            valid_model_name,
            model_version_id=model_version_id,
        ).generate_response())
        mock.post(**RegisterExternalModelStub(
            valid_model_name,
            model_version_id=model_version_id,
        ).generate_response())
        mock.post(**UploadTrainingDataStub(
            training_file_uri,
            model_version_id=model_version_id,
        ).generate_response())
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Success",
            model_version_id=model_version_id,
        ).generate_response())

        pool = ModelPool(endpoint)
        model = pool.get_or_create_model(model_name, schema, training_file_uri)
        assert model.name == valid_model_name
        assert model.model_version_id == model_version_id
