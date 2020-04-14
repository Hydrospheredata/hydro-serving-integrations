from typing import Union
import boto3
import botocore


class ClientFactory:
    """Helper class for managing clients."""

    @staticmethod
    def get_client(name: str, session: Union[boto3.Session, botocore.session.Session]):
        session_id = str(id(session))
        if not getattr(ClientFactory, session_id, {}):
            setattr(ClientFactory, session_id, {})
        clients = getattr(ClientFactory, session_id)
        return clients.setdefault(name, ClientFactory._get_client(name, session))

    @staticmethod
    def _get_client(name: str, session: Union[boto3.Session, botocore.session.Session]):
        if isinstance(session, boto3.Session):
            return session.client(name)
        else:
            return session.create_client(name)
