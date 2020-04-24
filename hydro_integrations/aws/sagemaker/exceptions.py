# pylint: disable=missing-class-docstring
from hydro_integrations.aws.exceptions import NotFound


class FunctionNotFound(NotFound):
    pass


class DataCaptureConfigException(Exception):
    pass
