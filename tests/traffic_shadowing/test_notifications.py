# pylint: disable=protected-access,redefined-outer-name
import logging
import pytest
from botocore.stub import Stubber
from sagemaker.model_monitor.data_capture_config import DataCaptureConfig
from hydro_integrations.aws.sagemaker import TrafficShadowing
from tests.traffic_shadowing.stubs import (
    DescribeStacksStub, PutNotificationStub, PutEmptyNotificationStub, GetBucketLocationStub
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
