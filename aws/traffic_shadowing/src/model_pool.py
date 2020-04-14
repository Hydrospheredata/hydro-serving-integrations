"""This module provides interface for interacting with Hydrosphere."""
import logging
import time
import urllib.parse
from typing import Dict, List
from enum import Enum
import requests
from requests import Response
from src.utils import transform_model_name, PROFILE_CONVERSIONS
from src.data import SchemaDescription, ColumnDescription
from src.model import Model
from src import errors


class DataProfileStatus(Enum):
    # pylint: disable=missing-class-docstring
    Success = "Success"
    Failure = "Failure"
    Processing = "Processing"
    NotRegistered = "NotRegistered"


def find_model(endpoint: str, name: str) -> List[Dict]:
    """Fetch all models from Hydrosphere and filters candidates."""
    url = urllib.parse.urljoin(endpoint, "/api/v2/model")
    response = requests.get(url)
    if response.status_code == 200:
        models = response.json()
    else:
        raise errors.ApiNotAvailable(response.content)
    return list(filter(lambda x: x["name"] == name, models))


def find_model_version(endpoint: str, name: str, version: int) -> Dict:
    """
    Fetch a specific model version from Hydrosphere and returns
    a set of parameters.
    """
    url = urllib.parse.urljoin(
        endpoint, f"/api/v2/model/version/{name}/{version}")
    response = requests.get(url)
    if response.status_code == 200:
        response = response.json()
        response = {
            "name": response["model"]["name"],
            "version": response["modelVersion"],
            "model_version_id": response["id"],
        }
    else:
        raise errors.ApiNotAvailable(response.content)
    return response


class ModelPool:
    """
    Represents a pool of the models and available operations
    on top of them.
    """
    logger = logging.getLogger('main')

    def __init__(self, endpoint: str) -> 'ModelPool':
        self.endpoint = endpoint

    def get_or_create_model(
            self,
            name: str,
            schema: SchemaDescription,
            training_file: str,
            metadata: Dict = None
    ) -> Model:
        """Try to load an existing model or register a new one."""
        try:
            return self.get_model(name)
        except errors.ModelNotFound:
            return self.create_model(name, schema, training_file, metadata)

    def get_model(self, name: str, strict: bool = False) -> Model:
        """Retrieve an existing model from Hydrosphere."""
        model = None
        candidates = find_model(self.endpoint, name)
        if candidates:
            self.logger.debug(
                "Found %d candidates, picking the first one", len(candidates))
            self.logger.info(
                'Found the model "%s"', candidates[0]["name"])
            result = find_model_version(self.endpoint, candidates[0]["name"], 1)
            model = Model(
                result["name"], result["version"], result["model_version_id"])
        if not (model or strict):
            self.logger.info('Didn\'t find the exact match for "%s" model name', name)
            candidates = find_model(self.endpoint, transform_model_name(name))
            if candidates:
                self.logger.debug(
                    "Found %d candidates, picking the first one", len(candidates))
                self.logger.info(
                    'Found the model "%s"', candidates[0]["name"])
                result = find_model_version(self.endpoint, candidates[0]["name"], 1)
                model = Model(
                    result["name"], result["version"], result["model_version_id"])
        if not model:
            raise errors.ModelNotFound("Didn't find any models with similar name")
        return model

    def create_model(
            self,
            name: str,
            schema: SchemaDescription,
            training_file: str,
            metadata: Dict = None
    ) -> Model:
        """
        Register an external model in the Hydrosphere platform
        and uploads training data.
        """
        registration_response = self._register_model(name, schema, metadata)
        model = Model(
            name=registration_response["model"]["name"],
            version=registration_response["modelVersion"],
            model_version_id=registration_response["id"]
        )
        self._upload_training_data(model.model_version_id, training_file)
        self._wait_for_data_processing(model.model_version_id)
        return model

    def _wait_for_data_processing(
            self,
            model_version_id,
            timeout: int = 120,
            retry: int = 3
    ) -> Response:
        """Wait till the data gets processed."""
        url = urllib.parse.urljoin(
            self.endpoint, f"/monitoring/profiles/batch/{model_version_id}/status")

        result = None
        while True:
            result = requests.get(url)
            if result.status_code != 200:
                if retry > 0:
                    retry -= 1
                    time.sleep(5)
                    continue
                else:
                    raise errors.ApiNotAvailable(
                        "Could not fetch the status of the data processing task.")

            body = result.json()
            status = DataProfileStatus[body["kind"]]
            if status == DataProfileStatus.Processing:
                if timeout > 0:
                    seconds = min(10, timeout)
                    timeout -= seconds
                    time.sleep(seconds)
                    continue
                else:
                    raise errors.TimeOut("Data processing timed out.")
            elif status == DataProfileStatus.Success:
                break
            else:
                raise errors.DataUploadFailed(f"Failed to upload the data: {status}")
        return result

    def _upload_training_data(self, model_version_id: int, training_file: str) -> Response:
        """Upload training data for the model."""
        self.logger.info("Uploading training data at %s", training_file)
        url = urllib.parse.urljoin(
            self.endpoint, f"/monitoring/profiles/batch/{model_version_id}/s3")
        result = requests.post(url, json={"path": training_file})
        if result.status_code != 200:
            raise errors.DataUploadFailed("Failed to submit data processing task")
        return result

    def _register_model(self, name, schema, metadata) -> Model:
        """Perform registration request."""
        self.logger.debug("Registering a new model")
        metadata = metadata or {}
        metadata["original_model_name"] = name

        url = urllib.parse.urljoin(
            self.endpoint, "/api/v2/externalmodel")
        body = self._create_registration_request_body(
            transform_model_name(name), schema, metadata)
        result = requests.post(url, json=body)

        response = None
        if result.status_code == 200:
            response = result.json()
            self.logger.info("Registered a new model: %s", response["model"]["name"])
        else:
            raise errors.ModelRegistrationFailed(
                f"Could not register a model: {result.content}")
        return response

    def _create_feature(self, schema: ColumnDescription) -> Dict:
        """Create a single feature for the model registration contract."""
        return {
            "name":     schema.name,
            "dtype":    schema.htype,
            "profile":  PROFILE_CONVERSIONS.get(schema.dtype),
            "shape": {
                "dim": [
                    {"size": dim, "name": f"{schema.name}_{i}"}
                    for i, dim in enumerate(schema.shape)
                ],
                "unknownRank": False,
            }
        }

    def _create_registration_request_body(
            self,
            name: str,
            schema: SchemaDescription,
            metadata: Dict
    ) -> Dict:
        """Create a request body for external model registration request."""
        body = {
            "name": name,
            "metadata": metadata or {},
            "contract": {
                "modelName": name,
                "predict": {
                    "signatureName": "predict",
                    "inputs": [
                        self._create_feature(feature)
                        for i, feature in enumerate(schema.inputs)
                    ],
                    "outputs": [
                        self._create_feature(feature)
                        for i, feature in enumerate(schema.outputs)
                    ],
                }
            }
        }
        self.logger.debug("Built a request body:\n%s", body)
        return body
