# pylint: disable=protected-access,missing-function-docstring
import pytest
import requests_mock
from src.model_pool import ModelPool
from src.errors import (
    ModelNotFound, DataUploadFailed, TimeOut, ApiNotAvailable
)
from tests.stubs.http.hydrosphere import (
    ListModelsStub, ListModelVersionsStub, RegisterExternalModelStub,
    UploadTrainingDataStub, WaitTrainingDataProcessingStub,
)
from tests.config import (
    VALID_MODEL_NAME, MODEL_NAME, HYDROSPHERE_ENDPOINT, MODEL_VERSION_ID,
    SCHEMA, TRAIN_KEY_FULL
)


def test_get_model_strict():
    with requests_mock.mock(real_http=False) as mock:
        mock.get(
            **ListModelsStub(VALID_MODEL_NAME).generate_response()
        )
        mock.get(
            **ListModelVersionsStub(VALID_MODEL_NAME).generate_response()
        )
        pool = ModelPool(HYDROSPHERE_ENDPOINT)
        model = pool.get_model(VALID_MODEL_NAME, True)
        assert model.name == VALID_MODEL_NAME


def test_get_model_strict_fail():
    with requests_mock.mock(real_http=False) as mock:
        mock.get(
            **ListModelsStub(VALID_MODEL_NAME).generate_response()
        )
        mock.get(
            **ListModelVersionsStub(VALID_MODEL_NAME).generate_response()
        )
        with pytest.raises(ModelNotFound):
            pool = ModelPool(HYDROSPHERE_ENDPOINT)
            pool.get_model(MODEL_NAME, True)


def test_get_model_non_strict():
    with requests_mock.mock(real_http=False) as mock:
        mock.get(
            **ListModelsStub(VALID_MODEL_NAME).generate_response()
        )
        mock.get(
            **ListModelVersionsStub(VALID_MODEL_NAME).generate_response()
        )
        pool = ModelPool(HYDROSPHERE_ENDPOINT)
        model = pool.get_model(MODEL_NAME, False)
        assert model.name == VALID_MODEL_NAME


def test_get_model_non_strict_fail():
    with requests_mock.mock(real_http=False) as mock:
        mock.get(**ListModelsStub().generate_response())
        with pytest.raises(ModelNotFound):
            pool = ModelPool(HYDROSPHERE_ENDPOINT)
            pool.get_model("not-exists", False)


def test_register_model():
    with requests_mock.mock(real_http=False) as mock:
        mock.post(**RegisterExternalModelStub(
            VALID_MODEL_NAME,
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        pool = ModelPool(HYDROSPHERE_ENDPOINT)
        response = pool._register_model(VALID_MODEL_NAME, SCHEMA, {})
        assert response["id"] == MODEL_VERSION_ID


def test_upload_training_data():
    with requests_mock.mock(real_http=False) as mock:
        mock.post(**UploadTrainingDataStub(
            TRAIN_KEY_FULL,
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        pool = ModelPool(HYDROSPHERE_ENDPOINT)
        result = pool._upload_training_data(MODEL_VERSION_ID, TRAIN_KEY_FULL)
        assert result.status_code == 200


def test_upload_training_data_fail():
    with requests_mock.mock(real_http=False) as mock:
        mock.post(**UploadTrainingDataStub(
            TRAIN_KEY_FULL,
            model_version_id=MODEL_VERSION_ID,
        ).generate_client_error())
        with pytest.raises(DataUploadFailed):
            pool = ModelPool(HYDROSPHERE_ENDPOINT)
            pool._upload_training_data(MODEL_VERSION_ID, TRAIN_KEY_FULL)


def test_wait_training_data_processed():
    with requests_mock.mock(real_http=False) as mock:
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Success",
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        pool = ModelPool(HYDROSPHERE_ENDPOINT)
        result = pool._wait_for_data_processing(MODEL_VERSION_ID)
        assert result.status_code == 200


def test_wait_training_data_processed_timeout():
    with requests_mock.mock(real_http=False) as mock:
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Processing",
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        with pytest.raises(TimeOut):
            pool = ModelPool(HYDROSPHERE_ENDPOINT)
            pool._wait_for_data_processing(MODEL_VERSION_ID, timeout=1, retry=0)


def test_wait_training_data_processed_fail():
    with requests_mock.mock(real_http=False) as mock:
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Failure",
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        with pytest.raises(DataUploadFailed):
            pool = ModelPool(HYDROSPHERE_ENDPOINT)
            pool._wait_for_data_processing(MODEL_VERSION_ID, timeout=1, retry=0)


def test_wait_training_data_processed_not_registered():
    with requests_mock.mock(real_http=False) as mock:
        mock.get(**WaitTrainingDataProcessingStub(
            kind="NotRegistered",
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        with pytest.raises(DataUploadFailed):
            pool = ModelPool(HYDROSPHERE_ENDPOINT)
            pool._wait_for_data_processing(MODEL_VERSION_ID, timeout=1, retry=0)


def test_wait_training_data_processed_unavailable():
    with requests_mock.mock(real_http=False) as mock:
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Success",
            model_version_id=MODEL_VERSION_ID,
        ).generate_client_error())
        with pytest.raises(ApiNotAvailable):
            pool = ModelPool(HYDROSPHERE_ENDPOINT)
            pool._wait_for_data_processing(MODEL_VERSION_ID, timeout=1, retry=0)


def test_create_model():
    with requests_mock.mock(real_http=False) as mock:
        mock.post(**RegisterExternalModelStub(
            VALID_MODEL_NAME,
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        mock.post(**UploadTrainingDataStub(
            TRAIN_KEY_FULL,
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Success",
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        pool = ModelPool(HYDROSPHERE_ENDPOINT)
        model = pool.create_model(VALID_MODEL_NAME, SCHEMA, TRAIN_KEY_FULL)
        assert model.model_version_id == MODEL_VERSION_ID


def test_get_or_create_model():
    with requests_mock.mock(real_http=False) as mock:
        mock.get(**ListModelsStub().generate_response())
        mock.get(**ListModelVersionsStub(
            VALID_MODEL_NAME,
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        mock.post(**RegisterExternalModelStub(
            VALID_MODEL_NAME,
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        mock.post(**UploadTrainingDataStub(
            TRAIN_KEY_FULL,
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())
        mock.get(**WaitTrainingDataProcessingStub(
            kind="Success",
            model_version_id=MODEL_VERSION_ID,
        ).generate_response())

        pool = ModelPool(HYDROSPHERE_ENDPOINT)
        model = pool.get_or_create_model(MODEL_NAME, SCHEMA, TRAIN_KEY_FULL)
        assert model.name == VALID_MODEL_NAME
        assert model.model_version_id == MODEL_VERSION_ID
