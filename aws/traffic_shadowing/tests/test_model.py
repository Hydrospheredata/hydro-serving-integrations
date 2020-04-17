# pylint: disable=missing-function-docstring
import requests_mock
from src.model_pool import ModelPool
from tests.stubs.http.hydrosphere import (
    ListModelsStub, ListModelVersionsStub, RegisterExternalModelStub,
    UploadTrainingDataStub, WaitTrainingDataProcessingStub,
)
from tests.config import (
    MODEL_NAME, VALID_MODEL_NAME, MODEL_VERSION_ID, TRAIN_KEY_FULL,
    HYDROSPHERE_ENDPOINT, SCHEMA
)


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
