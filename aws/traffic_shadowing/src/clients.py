import os
import urllib.parse
from typing import Union
import grpc
import boto3
import botocore
from hydro_serving_grpc.monitoring.api_pb2_grpc import MonitoringServiceStub


class AWSClientFactory:
    """Helper class for managing AWS clients."""

    @staticmethod
    def get_client(name: str, session: Union[boto3.Session, botocore.session.Session]):
        session_id = str(id(session))
        if not getattr(AWSClientFactory, session_id, {}):
            setattr(AWSClientFactory, session_id, {})
        clients = getattr(AWSClientFactory, session_id)
        return clients.setdefault(name, AWSClientFactory._get_client(name, session))

    @staticmethod
    def _get_client(name: str, session: Union[boto3.Session, botocore.session.Session]):
        if isinstance(session, boto3.Session):
            return session.client(name)
        else:
            return session.create_client(name)


class RPCStubFactory:
    """Helper class for managing gRPC stubs."""

    @staticmethod
    def get_stub(service_stub, channel: Union[grpc.Channel, None] = None):
        channel = channel or RPCStubFactory._get_channel(os.environ["HYDROSPHERE_ENDPOINT"])
        return service_stub(channel)

    @staticmethod
    def _get_channel(uri: str)-> grpc.Channel:
        """Make a gRPC channel from endpoint URI."""
        parse = urllib.parse.urlparse(uri)
        use_ssl_connection = parse.scheme == 'https'
        if use_ssl_connection:
            credentials = grpc.ssl_channel_credentials()
            channel = grpc.secure_channel(parse.netloc, credentials=credentials)
        else:
            channel = grpc.insecure_channel(parse.netloc)
        return channel
