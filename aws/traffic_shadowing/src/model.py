"""This module provides interface for interacting with Hydrosphere."""
import logging
import os
import urllib.parse

import grpc
import hydro_serving_grpc as hs
from hydro_serving_grpc.monitoring.api_pb2_grpc import MonitoringServiceStub
from hydro_serving_grpc.monitoring.metadata_pb2 import ExecutionMetadata
from hydro_serving_grpc.monitoring.api_pb2 import ExecutionInformation
from src.data import Request

logger = logging.getLogger('main')


def make_grpc_channel(
        uri,
) -> grpc.Channel:
    """ Makes gRPC channel from endpoint URI. """

    parse = urllib.parse.urlparse(uri)
    use_ssl_connection = parse.scheme == 'https'
    if use_ssl_connection:
        credentials = grpc.ssl_channel_credentials()
        channel = grpc.secure_channel(parse.netloc, credentials=credentials)
    else:
        channel = grpc.insecure_channel(parse.netloc)
    return channel


class Model:
    """
    Represents a model registered in Hydrosphere and available operations on it.
    """
    def __init__(self, name: str, version: int, model_version_id: int) -> 'Model':
        self.name = name
        self.version = version
        self.model_version_id = model_version_id
        self.signature_name = "predict"

        self.endpoint = os.environ["HYDROSPHERE_ENDPOINT"]
        self.channel = make_grpc_channel(self.endpoint)
        self.stub = MonitoringServiceStub(self.channel)

    def _create_execution_metadata_proto(self, request: Request) -> ExecutionMetadata:
        """
        Create an ExecutionMetadata message. ExecutionMetadata is used to define,
        which model, registered within Hydrosphere platform, was used to process
        a given request.
        """
        return ExecutionMetadata(
            model_name=self.name,
            model_version=self.version,
            modelVersion_id=self.model_version_id,
            signature_name=self.signature_name,
            request_id=request.metadata.event_id,
        )

    def _create_predict_request_proto(self, request: Request) -> hs.PredictRequest:
        """
        Create a PredictRequest message. PredictRequest is used to define the data
        passed to the model for inference.
        """
        return hs.PredictRequest(
            model_spec=hs.ModelSpec(
                name=self.name,
                signature_name=self.signature_name,
            ),
            inputs=request.build_input_tensors(),
        )

    def _create_predict_response_proto(self, request: Request) -> hs.PredictResponse:
        """
        Create a PredictResponse message. PredictResponse is used to define the
        outputs of the model inference.
        """
        return hs.PredictResponse(
            outputs=request.build_output_tensors(),
        )

    def _create_execution_information_proto(
            self,
            request: hs.PredictRequest,
            response: hs.PredictResponse,
            metadata: ExecutionMetadata
    ) -> ExecutionInformation:
        """
        Create an ExecutionInformation message. ExecutionInformation contains all
        request data and all auxiliary information about request execution, required
        to calculate metrics.
        """
        return ExecutionInformation(
            request=request,
            response=response,
            metadata=metadata,
        )

    def compose_execution_information_proto(self, request: Request) -> ExecutionInformation:
        """Compose an ExecutionInformation message from a Request."""
        return self._create_execution_information_proto(
            self._create_predict_request_proto(request),
            self._create_predict_response_proto(request),
            self._create_execution_metadata_proto(request),
        )

    def analyse(self, request: Request) -> None:
        """Use RPC method Analyse of the MonitoringService to calculate metrics."""
        logger.debug("Analysing request: %s", request)
        self.stub.Analyze(self.compose_execution_information_proto(request))
