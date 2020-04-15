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


def test_get_model_strict(valid_model_name, endpoint):
    with requests_mock.mock(real_http=False) as mock:
        mock.get(
            **ListModelsStub(valid_model_name).generate_response()
        )
        mock.get(
            **ListModelVersionsStub(valid_model_name, 1).generate_response()
        )
        pool = ModelPool(endpoint)
        model = pool.get_model(valid_model_name, True)
        assert model.name == valid_model_name
        assert model.version == 1


def test_get_model_strict_fail(valid_model_name, model_name, endpoint):
    with requests_mock.mock(real_http=False) as mock:
        mock.get(
            **ListModelsStub(valid_model_name).generate_response()
        )
        mock.get(
            **ListModelVersionsStub(valid_model_name, 1).generate_response()
        )
        with pytest.raises(ModelNotFound):
            pool = ModelPool(endpoint)
            pool.get_model(model_name, True)


def test_get_model_non_strict(valid_model_name, model_name, endpoint):
    with requests_mock.mock(real_http=False) as mock:
        mock.get(
            **ListModelsStub(valid_model_name).generate_response()
        )
        mock.get(
            **ListModelVersionsStub(valid_model_name, 1).generate_response()
        )
        pool = ModelPool(endpoint)
        model = pool.get_model(model_name, False)
        assert model.name == valid_model_name
        assert model.version == 1


def test_get_model_non_strict_fail(endpoint):
    with requests_mock.mock(real_http=False) as mock:
        mock.get(**ListModelsStub().generate_response())
        with pytest.raises(ModelNotFound):
            pool = ModelPool(endpoint)
            pool.get_model("not-exists", False)


def test_register_model(valid_model_name, schema, endpoint):
    with requests_mock.mock(real_http=False) as mock:
        model_version_id = 1
        mock.post(**RegisterExternalModelStub(
            valid_model_name,
            model_version_id=model_version_id,
        ).generate_response())
        pool = ModelPool(endpoint)
        response = pool._register_model(valid_model_name, schema, {})
        assert response["id"] == model_version_id


def test_upload_training_data(training_file_uri, endpoint):
    with requests_mock.mock(real_http=False) as mock:
        model_version_id = 1
        mock.post(**UploadTrainingDataStub(
            training_file_uri,
            model_version_id=model_version_id,
        ).generate_response())
        pool = ModelPool(endpoint)
        result = pool._upload_training_data(model_version_id, training_file_uri)
        assert result.status_code == 200


def test_upload_training_data_fail(training_file_uri, endpoint):
    with requests_mock.mock(real_http=False) as mock:
        model_version_id = 1
        mock.post(**UploadTrainingDataStub(
            training_file_uri,
            model_version_id=model_version_id,
        ).generate_client_error())
        with pytest.raises(DataUploadFailed):
            pool = ModelPool(endpoint)
            pool._upload_training_data(model_version_id, training_file_uri)


def test_wait_training_data_processed(endpoint):
    with requests_mock.mock(real_http=False) as mock:
        model_version_id = 1
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Success",
            model_version_id=model_version_id,
        ).generate_response())
        pool = ModelPool(endpoint)
        result = pool._wait_for_data_processing(model_version_id)
        assert result.status_code == 200


def test_wait_training_data_processed_timeout(endpoint):
    with requests_mock.mock(real_http=False) as mock:
        model_version_id = 1
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Processing",
            model_version_id=model_version_id,
        ).generate_response())
        with pytest.raises(TimeOut):
            pool = ModelPool(endpoint)
            pool._wait_for_data_processing(model_version_id, timeout=1, retry=0)


def test_wait_training_data_processed_fail(endpoint):
    with requests_mock.mock(real_http=False) as mock:
        model_version_id = 1
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Failure",
            model_version_id=model_version_id,
        ).generate_response())
        with pytest.raises(DataUploadFailed):
            pool = ModelPool(endpoint)
            pool._wait_for_data_processing(model_version_id, timeout=1, retry=0)


def test_wait_training_data_processed_not_registered(endpoint):
    with requests_mock.mock(real_http=False) as mock:
        model_version_id = 1
        mock.get(**WaitTrainingDataProcessingStub(
            kind="NotRegistered",
            model_version_id=model_version_id,
        ).generate_response())
        with pytest.raises(DataUploadFailed):
            pool = ModelPool(endpoint)
            pool._wait_for_data_processing(model_version_id, timeout=1, retry=0)


def test_wait_training_data_processed_unavailable(endpoint):
    with requests_mock.mock(real_http=False) as mock:
        model_version_id = 1
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Success",
            model_version_id=model_version_id,
        ).generate_client_error())
        with pytest.raises(ApiNotAvailable):
            pool = ModelPool(endpoint)
            pool._wait_for_data_processing(model_version_id, timeout=1, retry=0)


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
