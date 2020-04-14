from typing import Union
from tests.stubs.base import MockBase


class ListModelsStub(MockBase):
    method = "/api/v2/model"

    def __init__(self, name: Union[str, None] = None):
        self.name = name

    @property
    def expected_params(self) -> dict:
        return {}

    @property
    def service_response(self) -> dict:
        response = [
            {
                "id": 24,
                "name": "something-else",
            },
        ]
        if self.name is not None:
            response.append({
                "id": 25,
                "name": self.name,
            })
        return response


class ListModelVersionsStub(MockBase):
    method = "/api/v2/model/version/{}/{}"

    def __init__(
            self,
            name: str,
            model_id: int = 1,
            model_version: int = 1,
            model_version_id: int = 1,
    ):
        self.name = name
        self.model_id = model_id
        self.model_version = model_version
        self.model_version_id = model_version_id
        self.method = self.method.format(name, model_version)

    @property
    def expected_params(self) -> dict:
        return {}

    @property
    def service_response(self) -> dict:
        return {
            "model": {
                "id": self.model_id,
                "name": self.name
            },
            "modelContract": {
                "modelName": self.name,
                "predict": {
                    "signatureName": "predict",
                    "inputs": [
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_INT64",
                            "name": "Account Length",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_DOUBLE",
                            "name": "VMail Message",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_DOUBLE",
                            "name": "Day Mins",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_INT64",
                            "name": "Day Calls",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                    ],
                    "outputs": [
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_DOUBLE",
                            "name": "Churn",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        }
                    ]
                }
            },
            "id": self.model_version_id,
            "metadata": {
                "original_model_name": self.name.lower()
            },
            "kind": "External",
            "modelVersion": self.model_version,
            "created": "2020-03-19T11:54:03.586Z"
        }


class RegisterExternalModelStub(MockBase):
    method = "/api/v2/externalmodel"

    def __init__(
            self,
            name: str,
            model_id: int = 1,
            model_version: int = 1,
            model_version_id: int = 1,
            metadata: Union[dict, None] = None
    ):
        self.name = name
        self.model_id = model_id
        self.model_version = model_version
        self.model_version_id = model_version_id
        self.metadata = metadata

    @property
    def expected_params(self) -> dict:
        return {
            "name": self.name,
            "metadata": self.metadata or {},
            "contract": {
                "modelName": self.name,
                "predict": {
                    "signatureName": "predict",
                    "inputs": [
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_INT64",
                            "name": "Account Length",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_DOUBLE",
                            "name": "VMail Message",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_DOUBLE",
                            "name": "Day Mins",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_INT64",
                            "name": "Day Calls",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                    ],
                    "outputs": [
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_DOUBLE",
                            "name": "Churn",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        }
                    ]
                }
            }
        }

    @property
    def service_response(self) -> dict:
        return {
            "model": {
                "id": self.model_id,
                "name": self.name
            },
            "modelContract": {
                "modelName": self.name,
                "predict": {
                    "signatureName": "predict",
                    "inputs": [
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_INT64",
                            "name": "Account Length",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_DOUBLE",
                            "name": "VMail Message",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_DOUBLE",
                            "name": "Day Mins",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_INT64",
                            "name": "Day Calls",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        },
                    ],
                    "outputs": [
                        {
                            "profile": "NUMERICAL",
                            "dtype": "DT_DOUBLE",
                            "name": "Churn",
                            "shape": {
                                "dim": [],
                                "unknownRank": False
                            }
                        }
                    ]
                }
            },
            "id": self.model_version_id,
            "metadata": {
                "original_model_name": self.name.lower()
            },
            "kind": "External",
            "modelVersion": self.model_version,
            "created": "2020-03-19T11:54:03.586Z"
        }


class UploadTrainingDataStub(MockBase):
    method = "/monitoring/profiles/batch/{}/s3"

    def __init__(self, training_file_uri: str, model_version_id: int):
        self.training_file_uri = training_file_uri
        self.model_version_id = model_version_id
        self.method = self.method.format(self.model_version_id)

    @property
    def expected_params(self):
        return {
            "path": self.training_file_uri
        }

    @property
    def service_response(self):
        return {}


class WaitTrainingDataProcessingStub(MockBase):
    method = "/monitoring/profiles/batch/{}/status"

    def __init__(self, kind: str, model_version_id: int):
        self.kind = kind
        self.model_version_id = model_version_id
        self.method = self.method.format(self.model_version_id)

    @property
    def expected_params(self):
        return {}

    @property
    def service_response(self):
        return {
            "kind": self.kind
        }
