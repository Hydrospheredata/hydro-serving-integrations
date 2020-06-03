"""
This module defines various exceptions.
"""

# pylint: disable=missing-class-docstring

class ModelNotFound(Exception):
    pass


class DataNotFound(Exception):
    pass


class ApiNotAvailable(Exception):
    pass


class ModelRegistrationFailed(Exception):
    pass


class DataUploadFailed(Exception):
    pass
