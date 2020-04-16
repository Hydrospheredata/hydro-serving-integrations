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
        """Expected parameters to be passed to the invocation method."""

    @property
    @abstractmethod
    def service_response(self) -> dict:
        """Expected service response from invoking the method."""

    @property
    def service_error_code(self) -> str:
        """Expected error code from invoking the method, e.g., ValueError."""
        return ''

    @property
    def service_message(self) -> str:
        """Expected detailed error message from invoking the method."""
        return ''

    @property
    def http_status_code(self) -> int:
        """Expected http status code from invoking the method."""
        return 400

    @property
    def service_error_meta(self) -> Union[dict, None]:
        """Expected error metadata form service response."""
        return None

    @property
    def response_meta(self) -> Union[dict, None]:
        """Expected metadata from service response."""
        return None

    def generate_response(self) -> dict:
        """
        Helper function to quickly generate kwargs for botocore.stub.Stubber.add_response.
        """
        return {
            'method': self.method,
            'service_response': self.service_response,
            'expected_params': self.expected_params,
        }

    def generate_client_error(self) -> dict:
        """
        Helper function to quickly generate kwargs for botocore.stub.Stubber.add_client_error.
        """
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
        """Helper function to quickly generate kwargs for requests_mock package."""
        return {
            'url': urllib.parse.urljoin(HYDROSPHERE_ENDPOINT, self.method),
            'text': json.dumps(self.service_response),
        }

    def generate_client_error(self) -> dict:
        """Helper function to quickly generate kwargs for requests_mock package."""
        return {
            'url': urllib.parse.urljoin(HYDROSPHERE_ENDPOINT, self.method),
            'status_code': self.http_status_code
        }
