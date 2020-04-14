import os
import pytest
import botocore
from src.utils import ClientFactory

session = botocore.session.get_session()
s3_client = ClientFactory.get_client('s3', session)

S3_DATA_CAPTURE_BUCKET = os.environ['S3_DATA_CAPTURE_BUCKET']
S3_DATA_CAPTURE_PREFIX = os.environ['S3_DATA_CAPTURE_PREFIX']
S3_DATA_TRAINING_BUCKET = os.environ['S3_DATA_TRAINING_BUCKET']
S3_DATA_TRAINING_PREFIX = os.environ['S3_DATA_TRAINING_PREFIX']
HYDROSPHERE_ENDPOINT = os.environ['HYDROSPHERE_ENDPOINT']

MODEL_NAME = "DEMO-xgb-churn-pred-model-monitor-2020-03-11-12-25-04"
TRAINING_KEY = f"{S3_DATA_TRAINING_PREFIX}/{MODEL_NAME}/training-dataset-with-header.csv"
CAPTURE_KEY = f"{S3_DATA_CAPTURE_PREFIX}/{MODEL_NAME}/AllTraffic/2020/03/11/12/32-18-648-cee08c3a-02ce-4790-b8ba-3173cfc12813.jsonl"
CAPTURE_SIZE = 2776


@pytest.fixture
def s3_event():
    return {
        "Records": [
            {
                "eventVersion": "2.1",
                "eventSource": "aws:s3",
                "awsRegion": "us-east-2",
                "eventTime": "2020-03-11T12:46:24.913Z",
                "eventName": "ObjectCreated:Put",
                "userIdentity": {
                    "principalId": "AWS:AROA5XGMCUEIEM5XIA5M4:SageMaker"
                },
                "requestParameters": {
                    "sourceIPAddress": "10.1.57.30"
                },
                "responseElements": {
                    "x-amz-request-id": "665202EF5C2DCB57",
                    "x-amz-id-2": "dO6fzj/TZHJq9JvLGGGgmZt3BW9+2l26YVWcDcZpPKVvXcYKSNLbxEZXqVs5hynKxmOOHt/bbpfvYc1EpXgps3cdDfCiTOYtMO9cTdxnJMg="
                },
                "s3": {
                    "s3SchemaVersion": "1.0",
                    "configurationId": "96813b24-32d9-47fb-8766-17f96113168f",
                    "bucket": {
                        "name": S3_DATA_CAPTURE_BUCKET,
                        "ownerIdentity": {
                            "principalId": "AYOFZ9JA3UDEA"
                        },
                        "arn": f"arn:aws:s3:::{S3_DATA_CAPTURE_BUCKET}"
                    },
                    "object": {
                        "key": CAPTURE_KEY,
                        "size": CAPTURE_SIZE,
                        "eTag": "ce232e54888d676f0446cc43da864f57",
                        "sequencer": "005E68DDA0CEAB1436"
                    }
                }
            }
        ]
    }


# def test_lambda_handler(caplog, s3_event: dict):
#     caplog.set_level(logging.DEBUG)
#     transformed_model_name = utils.transform_model_name(MODEL_NAME)

#     with Stubber(s3_client) as s3_stubber:
#         with requests_mock.mock() as mock:
#             # Stub ListObjectsV2 API call to list training data
#             # bucket to find the biggest csv file
#             list_objects_v2_stub = ListObjectsV2Stub(
#                 S3_DATA_TRAINING_BUCKET, f"{S3_DATA_TRAINING_PREFIX}/{MODEL_NAME}"
#             )
#             s3_stubber.add_response(**list_objects_v2_stub.generate_response())

#             # Stub GetObject API call to read first line of
#             # production request data to infer schema
#             get_object_stub_test = GetObjectStub(
#                 S3_DATA_CAPTURE_BUCKET,
#                 CAPTURE_KEY,
#                 'aws/traffic_shadowing/tests/test_file.jsonl'
#             )
#             s3_stubber.add_response(**get_object_stub_test.generate_response())

#             # Stub GetObject API call to read first line of
#             # training data to adjust inferred schema
#             get_object_stub_train = GetObjectStub(
#                 S3_DATA_TRAINING_BUCKET,
#                 TRAINING_KEY,
#                 'aws/traffic_shadowing/tests/train_file.csv'
#             )
#             s3_stubber.add_response(**get_object_stub_train.generate_response())

#             # Stub Hydrosphere API to list existing models
#             list_models_stub = ListModelsStub(
#                 transformed_model_name
#             )
#             mock.get(**list_models_stub.generate_response())

#             # Stub Hydrosphere API to fetch existing model version
#             list_model_versions_stub = ListModelVersionsStub(
#                 MODEL_NAME,
#                 transformed_model_name,
#                 1,
#             )
#             mock.get(**list_model_versions_stub.generate_response())

#             # Stub GetObject API call to read all file containing
#             # captured requests for analysis.
#             get_object_stub_test = GetObjectStub(
#                 S3_DATA_CAPTURE_BUCKET, 
#                 CAPTURE_KEY, 
#                 'aws/traffic_shadowing/tests/test_file.jsonl'
#             )
#             s3_stubber.add_response(**get_object_stub_test.generate_response())

#             result = lambda_handler(s3_event, "", session)
#             assert result
