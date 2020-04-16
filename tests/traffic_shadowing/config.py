import os
import botocore
from hydro_integrations.aws.helpers import AWSClientFactory

session = botocore.session.get_session()
s3_client = AWSClientFactory.get_or_create_client('s3', session)
cloudformation_client = AWSClientFactory.get_or_create_client('cloudformation', session)


HYDROSPHERE_ENDPOINT = os.environ["HYDROSPHERE_ENDPOINT"]
TRAIN_BUCKET = os.environ["S3_DATA_TRAINING_BUCKET"]
TRAIN_PREFIX = os.environ["S3_DATA_TRAINING_PREFIX"]
TRAIN_PREFIX_FULL = f"s3://{TRAIN_BUCKET}/{TRAIN_PREFIX}"
CAPTURE_BUCKET = os.environ["S3_DATA_CAPTURE_BUCKET"]
CAPTURE_PREFIX = os.environ["S3_DATA_CAPTURE_PREFIX"]
CAPTURE_PREFIX_FULL = f"s3://{CAPTURE_BUCKET}/{CAPTURE_PREFIX}"
