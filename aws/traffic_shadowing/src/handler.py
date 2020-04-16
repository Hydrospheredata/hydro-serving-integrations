"""
Lambda function shadowing traffic from SageMaker models to the Hydrosphere platform.
"""
import logging
import json
import os
from typing import Dict, Any, Union
import boto3
import botocore
from src.model_pool import ModelPool
from src.data import Record, Request, Contract
from src import log  # pylint: disable=unused-import
from src import utils
from src.utils import S3Utils

logger = logging.getLogger(__name__)

S3_DATA_CAPTURE_BUCKET = os.environ['S3_DATA_CAPTURE_BUCKET']
S3_DATA_CAPTURE_PREFIX = os.environ['S3_DATA_CAPTURE_PREFIX']
S3_DATA_TRAINING_BUCKET = os.environ['S3_DATA_TRAINING_BUCKET']
S3_DATA_TRAINING_PREFIX = os.environ['S3_DATA_TRAINING_PREFIX']
HYDROSPHERE_ENDPOINT = os.environ['HYDROSPHERE_ENDPOINT']

logger.debug('%s=%s', 'S3_DATA_CAPTURE_BUCKET', S3_DATA_CAPTURE_BUCKET)
logger.debug('%s=%s', 'S3_DATA_CAPTURE_PREFIX', S3_DATA_CAPTURE_PREFIX)
logger.debug('%s=%s', 'S3_DATA_TRAINING_BUCKET', S3_DATA_TRAINING_BUCKET)
logger.debug('%s=%s', 'S3_DATA_TRAINING_PREFIX', S3_DATA_TRAINING_PREFIX)
logger.debug('%s=%s', 'HYDROSPHERE_ENDPOINT', HYDROSPHERE_ENDPOINT)


def lambda_handler(
        event: Dict,
        context: Any,   # pylint: disable=unused-argument
        session: Union[boto3.Session, botocore.session.Session, None] = None
) -> Dict:
    """
    AWS Lambda function handler.
    """
    session = session or boto3.Session()
    s3_utils = S3Utils(session)
    model_pool = ModelPool(HYDROSPHERE_ENDPOINT)

    total_requests = 0
    for i, event_record in enumerate(event.get('Records')):
        logger.debug("%d/%d | Scanning through record %s", i, len(event.get('Records')), event)
        capture_record = Record.from_event_record(event_record, session)
        model_name = utils.parse_model_name(
            S3_DATA_CAPTURE_PREFIX, capture_record.key
        )
        training_file_uri = s3_utils.get_largest_csv(
            S3_DATA_TRAINING_BUCKET, S3_DATA_TRAINING_PREFIX, model_name
        )
        train_record = Record(*utils.parse_s3_uri(training_file_uri), session)
        contract = Contract(capture_record, train_record, session)

        model = model_pool.get_or_create_model(
            model_name, contract.schema, training_file_uri
        )
        j = 0
        for j, data in enumerate(capture_record.read()):
            logger.debug("Reading %d request", j)
            request = Request.from_dict(json.loads(data), contract.schema)
            model.analyse(request)
        total_requests += j

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Processed %d requests' % total_requests,
            'detail': total_requests
        })
    }
