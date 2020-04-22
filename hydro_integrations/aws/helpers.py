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
            return session.get_scoped_config().get('region', '')


class AWSClientFactory:
    """Helper class for managing AWS clients."""

    @staticmethod
    def get_or_create_client(name: str, session: Union[boto3.Session, botocore.session.Session]):
        session_id = str(id(session))
        if not getattr(AWSClientFactory, session_id, {}):
            setattr(AWSClientFactory, session_id, {})
        clients = getattr(AWSClientFactory, session_id)
        return clients.setdefault(name, AWSClientFactory._get_or_create_client(name, session))

    @staticmethod
    def _get_or_create_client(name: str, session: Union[boto3.Session, botocore.session.Session]):
        if isinstance(session, boto3.Session):
            return session.client(name)
        else:
            return session.create_client(name)
