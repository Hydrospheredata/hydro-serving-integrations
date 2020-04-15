import os
import urllib.parse
import json
from typing import Union
from abc import ABC, abstractmethod

HYDROSPHERE_ENDPOINT = os.environ['HYDROSPHERE_ENDPOINT']


class StubBase(ABC):
    """Base class used for mocking of AWS API calls."""
    method = None

    @property
    @abstractmethod
    def expected_params(self) -> dict:
        pass

    @property
    @abstractmethod
    def service_response(self) -> dict:
        pass

    @property
    def service_error_code(self) -> str:
        return ''

    @property
    def service_message(self) -> str:
        return ''

    @property
    def http_status_code(self) -> int:
        return 400

    @property
    def service_error_meta(self) -> Union[dict, None]:
        return None

    @property
    def response_meta(self) -> Union[dict, None]:
        return None

    def generate_response(self) -> dict:
        return {
            'method': self.method,
            'service_response': self.service_response,
            'expected_params': self.expected_params,
        }

    def generate_client_error(self) -> dict:
        return {
            'method': self.method,
            'service_error_code': self.service_error_code,
            'service_message': self.service_message,
            'http_status_code': self.http_status_code,
            'service_error_meta': self.service_error_meta,
            'expected_params': self.expected_params,
            'response_meta': self.response_meta,
        }


class MockBase(StubBase, ABC):
    """Base class used for mocking HTTP requests."""
    # pylint: disable=abstract-method

    def generate_response(self) -> dict:
        return {
            'url': urllib.parse.urljoin(HYDROSPHERE_ENDPOINT, self.method),
            'text': json.dumps(self.service_response),
        }

    def generate_client_error(self) -> dict:
        return {
            'url': urllib.parse.urljoin(HYDROSPHERE_ENDPOINT, self.method),
            'status_code': self.http_status_code
        }
