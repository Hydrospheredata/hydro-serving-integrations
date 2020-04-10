from typing import Union
import botocore.session
import boto3


class SessionMixin:
    """Helper class for working with boto3 and botocore sessions."""
    def get_region(self):
        return SessionMixin._get_region(self._session)
        
    @staticmethod
    def _get_region(session: Union[boto3.Session, botocore.session.Session]):
        if isinstance(session, boto3.Session):
            return session.region_name
        else:
            return session.get_scoped_config().get('region')


class ClientFactory:
    """Helper class for managing singleton clients."""
    @staticmethod
    def get_client(name: str, session: Union[boto3.Session, botocore.session.Session]):
        if getattr(ClientFactory, name, None):
            return getattr(ClientFactory, name)
        else:
            session = ClientFactory._get_client(name, session)
            setattr(ClientFactory, name, session)
            return session

    @staticmethod
    def _get_client(name: str, session: Union[boto3.Session, botocore.session.Session]):
        if isinstance(session, boto3.Session):
            return session.client(name)
        else:
            return session.create_client(name)
