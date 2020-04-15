import logging
import pytest
import botocore
from botocore.stub import Stubber
from sagemaker.model_monitor.data_capture_config import DataCaptureConfig
from hydro_integrations.aws.sagemaker import TrafficShadowing
from hydro_integrations.aws.helpers import AWSClientFactory
from tests.traffic_shadowing.stubs import (
    CreateStackStub, DescribeStacksStub, DeleteStackStub,
    GetOneNotificationStub, PutNotificationStub, PutEmptyNotificationStub,
)

session = botocore.session.get_session()
s3_client = AWSClientFactory.get_client('s3', session)
cloudformation_client = AWSClientFactory.get_client('cloudformation', session)


@pytest.fixture
def shadowing():
    data_capture_config = DataCaptureConfig(True)
    return TrafficShadowing(
        "http://example.com",
        "s3://bucket/path",
        data_capture_config,
        session,
    )


def test_replace_notification(caplog, shadowing: TrafficShadowing):
    """Test an entire replacement of a bucket notification configuration."""
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

        # s3 stubs
        put_notification_stub = PutNotificationStub(
            shadowing.s3_data_capture_bucket,
            shadowing.s3_data_capture_prefix,
            describe_stacks_stub.lambda_arn
        )

        # Stub DescribeStacks API call to retreive lambda Arn
        # from stack outputs.
        cloudformation_stubber.add_response(
            **describe_stacks_stub.generate_response(),
        )

        # Stub PutBucketNotificationConfiguration API call to
        # replace existing notification configuration.
        s3_stubber.add_response(
            **put_notification_stub.generate_response(),
        )

        shadowing._add_bucket_notification(replace=True)

        cloudformation_stubber.assert_no_pending_responses()
        s3_stubber.assert_no_pending_responses()


def test_purge_notification(caplog, shadowing: TrafficShadowing):
    """Test purging of a bucket notification configuration."""
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

        # s3 stubs
        put_empty_notification_stub = PutEmptyNotificationStub(
            shadowing.s3_data_capture_bucket,
        )

        # Stub DescribeStacks API call to retreive lambda Arn
        # from stack outputs.
        cloudformation_stubber.add_response(
            **describe_stacks_stub.generate_response(),
        )

        # Stub PutBucketNotificationConfiguration API call to
        # replace existing notification configuration.
        s3_stubber.add_response(
            **put_empty_notification_stub.generate_response(),
        )

        shadowing._delete_bucket_notification(purge=True)
        cloudformation_stubber.assert_no_pending_responses()
        s3_stubber.assert_no_pending_responses()
