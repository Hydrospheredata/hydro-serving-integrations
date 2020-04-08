"""
Lambda function shadowing traffic from SageMaker models
to the Hydrosphere platform.
"""
import logging
import json
import os
import urllib.parse
from typing import Dict, Any
from src.model_pool import ModelPool
from src.data import Record, Request, Contract
from src import utils
from src import log

logger = logging.getLogger('main')

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


def lambda_handler(event: Dict, context: Any) -> Dict:
    """
    AWS Lambda function handler.
    """
    model_pool = ModelPool(HYDROSPHERE_ENDPOINT)

    total_requests = 0
    for i, event_record in enumerate(event.get('Records')):
        logger.debug("%d/%d | Scanning through record %s", i, len(event.get('Records')), event)
        record = Record(event_record)
        contract = Contract(record)

        model_name = utils.parse_model_name(S3_DATA_CAPTURE_PREFIX, record.key)
        training_file = utils.parse_training_path(
            S3_DATA_TRAINING_BUCKET, S3_DATA_TRAINING_PREFIX, model_name)
        contract.update_headers(*utils.parse_s3_uri(training_file))

        model = model_pool.get_or_create_model(
            model_name, contract.schema, training_file)
        for j, data in enumerate(record.read_file()):
            logger.debug("Reading %d request", j)
            request = Request.from_dict(data, contract.schema)
            model.analyse(request)
        total_requests += j

    return {
        'statusCode': 200,
        'body': json.dumps('Processed %d requests' %total_requests)
    }
