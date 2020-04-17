# pylint: disable=redefined-outer-name
import logging
import pytest
import urllib.parse
from botocore.stub import Stubber
from sagemaker.model_monitor.data_capture_config import DataCaptureConfig
from hydro_integrations.aws.sagemaker import TrafficShadowing
from tests.traffic_shadowing.stubs import (
    CreateStackStub, DescribeStacksStub, DeleteStackStub,
    GetEmptyNotificationStub, GetOneNotificationStub, PutNotificationStub,
    PutEmptyNotificationStub, GetBucketLocationStub
)
from tests.traffic_shadowing.config import (
    HYDROSPHERE_ENDPOINT, TRAIN_PREFIX_FULL, CAPTURE_BUCKET, CAPTURE_PREFIX_FULL
)
from tests.traffic_shadowing.config import session, s3_client, cloudformation_client


@pytest.fixture
def shadowing():
    with Stubber(s3_client) as s3_stubber:
        s3_stubber.add_response(
            **GetBucketLocationStub(CAPTURE_BUCKET).generate_response()
        )
        data_capture_config = DataCaptureConfig(
            enable_capture=True,
            destination_s3_uri=CAPTURE_PREFIX_FULL,
        )
        return TrafficShadowing(
            HYDROSPHERE_ENDPOINT,
            TRAIN_PREFIX_FULL,
            data_capture_config,
            session,
        )


def test_deploy_stack(caplog, shadowing: TrafficShadowing):
    """Test basic stack creation in a clean environment."""
    caplog.set_level(logging.INFO)
    with Stubber(cloudformation_client) as cloudformation_stubber, \
            Stubber(s3_client) as s3_stubber:

        # cloudformation stubs
        create_stack_stub = CreateStackStub(
            shadowing.stack_name,
            shadowing.get_stack_parameters(),
            shadowing.get_stack_capabilities(),
            shadowing.stack_url,
        )
        describe_stacks_stub = DescribeStacksStub \
            .from_stub(create_stack_stub)

        # s3 stubs
        get_empty_notification_stub = \
            GetEmptyNotificationStub(
                shadowing.s3_data_capture_bucket
            )

        put_notification_stub = PutNotificationStub(
            shadowing.s3_data_capture_bucket,
            shadowing.s3_data_capture_prefix,
            describe_stacks_stub.lambda_arn,
        )

        # Stub first DescribeStacks API call to find existing
        # stacks. Should raise ClientError, as there shouldn't
        # be anything deployed at the moment.
        cloudformation_stubber.add_client_error(
            **describe_stacks_stub.generate_client_error()
        )

        # Stub CreateStack API call.
        cloudformation_stubber.add_response(
            **create_stack_stub.generate_response()
        )

        # Stub DescribeStacks API call as a waiter instance to
        # check for successful deployment.
        cloudformation_stubber.add_response(
            **describe_stacks_stub.generate_response(),
        )

        # Stub GetBucketNotificationConfiguration API call on
        # the provided data capture bucket.
        s3_stubber.add_response(
            **get_empty_notification_stub.generate_response(),
        )

        # Stub DescribeStacks API call to retreive lambda Arn
        # from stack outputs.
        cloudformation_stubber.add_response(
            **describe_stacks_stub.generate_response(),
        )

        # Stub PutBucketNotificationConfiguration API call to
        # update existing notification configuration.
        s3_stubber.add_response(
            **put_notification_stub.generate_response(),
        )

        shadowing.deploy_stack()

        cloudformation_stubber.assert_no_pending_responses()
        s3_stubber.assert_no_pending_responses()


def test_delete_stack(caplog, shadowing: TrafficShadowing):
    """Test basic stack deletion."""
    caplog.set_level(logging.INFO)
    with Stubber(cloudformation_client) as cloudformation_stubber, \
            Stubber(s3_client) as s3_stubber:

        # cloudformation stubs
        describe_stacks_stub = DescribeStacksStub(
            shadowing.stack_name,
            shadowing.get_stack_parameters(),
            shadowing.get_stack_capabilities(),
            shadowing.stack_url,
        )
        delete_stack_stub = DeleteStackStub(
            shadowing.stack_name,
        )

        # s3 stubs
        get_notification_stub = \
            GetOneNotificationStub(
                shadowing.s3_data_capture_bucket,
                shadowing.s3_data_capture_prefix,
                describe_stacks_stub.lambda_arn,
            )
        put_empty_notification_stub = PutEmptyNotificationStub \
            .from_stub(get_notification_stub)

        # Stub first DescribeStacks API call to get outputs
        # of an existing stack.
        cloudformation_stubber.add_response(
            **describe_stacks_stub.generate_response()
        )

        # Stub GetBucketNotificationConfiguration API call on
        # the provided data capture bucket.
        s3_stubber.add_response(
            **get_notification_stub.generate_response(),
        )

        # Stub PutBucketNotificationConfiguration API call to
        # update existing notification configuration with
        # removed lambda configuration.
        s3_stubber.add_response(
            **put_empty_notification_stub.generate_response(),
        )

        # Stub DeleteStack API call.
        cloudformation_stubber.add_response(
            **delete_stack_stub.generate_response()
        )

        # Stub DescribeStacks API call as a waiter instance to
        # check for successful deletion.
        cloudformation_stubber.add_client_error(
            **describe_stacks_stub.generate_client_error()
        )

        shadowing.delete_stack()

        cloudformation_stubber.assert_no_pending_responses()
        s3_stubber.assert_no_pending_responses()
