from typing import List, Dict, Union
import logging
import pprint
import boto3
import botocore
from hydro_integrations.aws.helpers import SessionMixin, AWSClientFactory
from hydro_integrations.aws.exceptions import (
    StackCanNotBeProcessed, StackIsBeingProcessed, StackNotFound
)

logger = logging.getLogger(__name__)


RESOURCES_EXIST_NORMAL = ['CREATE_COMPLETE', 'UPDATE_COMPLETE', 'IMPORT_COMPLETE']
STACK_CREATION_FAILED = ['CREATE_FAILED', 'ROLLBACK_COMPLETE',]
IN_PROGRESS_STATES = [
    'CREATE_IN_PROGRESS', 'ROLLBACK_IN_PROGRESS', 'DELETE_IN_PROGRESS', 'UPDATE_IN_PROGRESS',
    'UPDATE_COMPLETE_CLEANUP_IN_PROGRESS', 'UPDATE_ROLLBACK_IN_PROGRESS',
    'UPDATE_ROLLBACK_COMPLETE_CLEANUP_IN_PROGRESS', 'REVIEW_IN_PROGRESS', 'IMPORT_IN_PROGRESS',
    'IMPORT_ROLLBACK_IN_PROGRESS',
]


class CloudFormation(SessionMixin):
    """Base object for interacting with CloudFormation API."""
    def __init__(
            self,
            stack_url: str,
            stack_name: str,
            stack_parameters: List[Dict[str, str]],
            stack_capabilities: List[str],
            session: boto3.Session,
    ):
        self.stack_url = stack_url
        self.stack_name = stack_name
        self.stack_parameters = stack_parameters
        self.stack_capabilities = stack_capabilities
        self._session = session or boto3.Session()
        self._cf_client = AWSClientFactory.get_or_create_client('cloudformation', self._session)

        self.__stack_outputs = None

    def _wait(self, name):
        waiter = self._cf_client.get_waiter(name)
        try:
            waiter.wait(
                StackName=self.stack_name,
            )
        except botocore.exceptions.WaiterError as error:
            logger.error(error)
            events = self._describe_stack_events_short()
            if events is not None:
                events.reverse()
                logger.error("Occurred events during stack life.")
                logging.error(pprint.pformat(events))
            else:
                logger.error("Could not find stack events.")
            raise StackCanNotBeProcessed from error

    def _create_stack(self):
        """Synchronously create a CloudFormation stack."""
        self._cf_client.create_stack(
            StackName=self.stack_name,
            TemplateURL=self.stack_url,
            Parameters=self.stack_parameters,
            Capabilities=self.stack_capabilities,
        )
        self._wait('stack_create_complete')

    def _update_stack(self):
        """Synchronously update a CloudFormation stack."""
        try:
            self._cf_client.update_stack(
                StackName=self.stack_name,
                TemplateURL=self.stack_url,
                Parameters=self.stack_parameters,
                Capabilities=self.stack_capabilities,
            )
            self._wait('stack_update_complete')
        except botocore.exceptions.ClientError as error:
            logger.warning(error)

    def _get_stack_state(self, stack: dict) -> str:
        return stack['StackStatus']

    def _describe_stack(self) -> Union[dict, None]:
        """Try to find stacks with similar name."""
        try:
            return self._cf_client.describe_stacks(
                StackName=self.stack_name,
            )['Stacks'][0]
        except botocore.exceptions.ClientError:
            logger.debug("Could not find a stack with name: %s.", self.stack_name)

    def _describe_stack_resources(self) -> Union[dict, None]:
        """Get stack resources."""
        try:
            return self._cf_client.describe_stack_resources(
                StackName=self.stack_name,
            )
        except botocore.exceptions.ClientError:
            logger.debug("Could not find a stack with name: %s.", self.stack_name)

    def _describe_stack_events(self) -> Union[dict, None]:
        """Try to find stack events of the underlying stack."""
        try:
            return self._cf_client.describe_stack_events(
                StackName=self.stack_name,
            )['StackEvents']
        except botocore.exceptions.ClientError:
            logger.debug("Could not find stack %s", self.stack_name)

    def _describe_stack_events_short(self) -> Union[List[dict], None]:
        """Describe stack events in shortened form."""
        reasons = self._describe_stack_events()
        details = ['LogicalResourceId', 'ResourceStatus', 'ResourceStatusReason', 'ResourceType']
        if reasons:
            return [
                {key: reason.get(key) for key in details} for reason in reasons
            ]

    def _deploy_stack(self, update_stack_if_exists: bool = True):
        """Synchronously deploy the stack."""
        stack = self._describe_stack()
        if stack is None:
            logger.info("Stack doesn't exists. Creating a new stack.")
            self._create_stack()
            return None

        state = self._get_stack_state(stack)
        logger.info("Found %s stack in %s state.", self.stack_name, state)

        if state in RESOURCES_EXIST_NORMAL:
            if update_stack_if_exists:
                logger.info("Updating stack.")
                self._update_stack()
        elif state in STACK_CREATION_FAILED:
            logger.error("Current stack is failed to be created. Please, resolve the issue "
                         "and delete the stack first.")
            events = self._describe_stack_events_short()
            if events is not None:
                events.reverse()
                logger.error(pprint.pformat(events))
            raise StackCanNotBeProcessed()
        elif state in IN_PROGRESS_STATES:
            logger.warning("Stack is currently being processed. Please, wait until stack finishes")
            raise StackIsBeingProcessed()
        else:
            raise Exception("Reached unexpected state.")

    def _delete_stack(self):
        """Synchronously delete an S3 lambda notification and delete the stack."""
        logger.info("Deleting deployed stack")
        self._cf_client.delete_stack(
            StackName=self.stack_name,
        )
        self._wait('stack_delete_complete')

    @property
    def stack_outputs(self) -> List[dict]:
        if self.__stack_outputs is None:
            stack = self._describe_stack()
            if stack is None:
                raise StackNotFound("Could not retrieve outputs of a nonexisting stack.")
            self.__stack_outputs = stack['Outputs']
        return self.__stack_outputs
