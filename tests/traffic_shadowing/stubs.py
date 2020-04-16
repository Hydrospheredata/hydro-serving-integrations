# pylint: disable=missing-class-docstring,line-too-long

import datetime
from uuid import uuid4
from typing import List
from dateutil.tz import tzutc
from tests.stubs import StubBase


# CloudFormation Stubs
# --------------------

class CreateStackStub(StubBase):
    method = 'create_stack'

    def __init__(
            self,
            stack_name: str,
            stack_parameters: List[dict],
            stack_capabilities: List[str],
            template_url: str
    ):
        self.stack_name = stack_name
        self.stack_parameters = stack_parameters
        self.stack_capabilities = stack_capabilities
        self.template_url = template_url

    @property
    def expected_params(self):
        return {
            "StackName": self.stack_name,
            "TemplateURL": self.template_url,
            "Parameters": self.stack_parameters,
            "Capabilities": self.stack_capabilities,
        }

    @property
    def service_response(self):
        return {
            "StackId": uuid4().hex
        }


class DescribeStacksStub(StubBase):
    method = 'describe_stacks'

    def __init__(
            self,
            stack_name: str,
            stack_parameters: List[dict],
            stack_capabilities: List[str],
            template_url: str,
    ):
        self.stack_name = stack_name
        self.stack_parameters = stack_parameters
        self.stack_capabilities = stack_capabilities
        self.template_url = template_url

        self.__lambda_arn = None

    @property
    def lambda_arn(self):
        if self.__lambda_arn is None:
            self.__lambda_arn = 'arn:aws:lambda:xx-xxxx-x:xxxxxxxxxxxx:function:traffic-shadowing-hydrosp-TrafficShadowingFunction-xxxxxxxxxxxx'
        return self.__lambda_arn

    @classmethod
    def from_stub(cls, stub: CreateStackStub):
        return cls(
            stub.stack_name,
            stub.stack_parameters,
            stub.stack_capabilities,
            stub.template_url,
        )

    @property
    def expected_params(self):
        return {"StackName": self.stack_name}

    @property
    def service_response(self):
        return {
            'Stacks': [
                {
                    'StackName': self.stack_name,
                    'Parameters': self.stack_parameters,
                    'CreationTime': datetime.datetime(2020, 4, 9, 17, 54, 52, 411000, tzinfo=tzutc()),
                    'RollbackConfiguration': {},
                    'StackStatus': 'CREATE_COMPLETE',
                    'DisableRollback': False,
                    'NotificationARNs': [],
                    'Capabilities': ['CAPABILITY_NAMED_IAM'],
                    'Outputs': [
                        {
                            'OutputKey': 'TrafficShadowingFunctionArn',
                            'OutputValue': self.lambda_arn,
                        }
                    ],
                    'Tags': [],
                    'EnableTerminationProtection': False,
                    'DriftInformation': {
                        'StackDriftStatus': 'NOT_CHECKED'
                    }
                }
            ],
        }

    @property
    def service_error_code(self):
        return 'ValidationError'

    @property
    def service_message(self):
        return f'Stack with id {self.stack_name} does not exist'


class DeleteStackStub(StubBase):
    method = 'delete_stack'

    def __init__(self, stack_name: str):
        self.stack_name = stack_name

    @property
    def expected_params(self):
        return {
            "StackName": self.stack_name,
        }

    @property
    def service_response(self):
        return {}


# S3 Stubs
# --------

class GetBucketLocationStub(StubBase):
    method = 'get_bucket_location'

    def __init__(self, bucket: str):
        self.bucket = bucket

    @property
    def expected_params(self):
        return {
            "Bucket": self.bucket,
        }

    @property
    def service_response(self):
        return {
            'ResponseMetadata': {
                'RequestId': 'xxxxxxxxxxxxxxxx',
                'HostId': 'xxxxxxxxxxx+xxxxxxxxxxxxx+xxxxxxxxxxx/xxxxxxxxxxx+xxxxxxxxxxxxxxxxxxxxxxxxx=',
                'HTTPStatusCode': 200,
                'HTTPHeaders': {
                    'x-amz-id-2': 'xxxxxxxxxxx+xxxxxxxxxxxxx+xxxxxxxxxxx/xxxxxxxxxxx+xxxxxxxxxxxxxxxxxxxxxxxxx=',
                    'x-amz-request-id': 'xxxxxxxxxxxxxxxx',
                    'date': 'Thu, 16 Apr 2020 10:55:06 GMT',
                    'content-type': 'application/xml',
                    'transfer-encoding': 'chunked',
                    'server': 'AmazonS3'
                },
                'RetryAttempts': 0
            },
            'LocationConstraint': 'eu-west-3'
        }

class GetEmptyNotificationStub(StubBase):
    method = 'get_bucket_notification_configuration'

    def __init__(self, bucket: str):
        self.bucket = bucket

    @property
    def expected_params(self):
        return {"Bucket": self.bucket}

    @property
    def service_response(self):
        return {}


class GetOneNotificationStub(StubBase):
    method = 'get_bucket_notification_configuration'

    def __init__(self, bucket: str, prefix: str, lambda_arn: str):
        self.bucket = bucket
        self.prefix = prefix
        self.lambda_arn = lambda_arn

    @property
    def expected_params(self):
        return {"Bucket": self.bucket}

    @property
    def service_response(self):
        return {
            'LambdaFunctionConfigurations': [
                {
                    'Id': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                    'LambdaFunctionArn': self.lambda_arn,
                    'Events': [
                        's3:ObjectCreated:*'
                    ],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {
                                    'Name': 'Prefix',
                                    'Value': self.prefix
                                },
                                {
                                    'Name': 'Suffix',
                                    'Value': '.jsonl'
                                }
                            ]
                        }
                    }
                }
            ]
        }


class GetMultipleNotificationStub(StubBase):
    method = 'get_bucket_notification_configuration'

    def __init__(self, bucket: str, prefix: str, lambda_arn: str):
        self.bucket = bucket
        self.prefix = prefix
        self.lambda_arn = lambda_arn

    @property
    def expected_params(self):
        return {"Bucket": self.bucket}

    @property
    def service_response(self):
        return {
            'LambdaFunctionConfigurations': [
                {
                    'Id': 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
                    'LambdaFunctionArn': self.lambda_arn,
                    'Events': [
                        's3:ObjectCreated:*'
                    ],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {
                                    'Name': 'Prefix',
                                    'Value': self.prefix
                                },
                                {
                                    'Name': 'Suffix',
                                    'Value': '.jsonl'
                                }
                            ]
                        }
                    }
                },
                {
                    'Id': 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy',
                    'LambdaFunctionArn': self.lambda_arn,
                    'Events': [
                        's3:ObjectCreated:*'
                    ],
                    'Filter': {
                        'Key': {
                            'FilterRules': [
                                {
                                    'Name': 'Prefix',
                                    'Value': self.prefix
                                },
                                {
                                    'Name': 'Suffix',
                                    'Value': '.jsonl'
                                }
                            ]
                        }
                    }
                }
            ]
        }


class PutNotificationStub(StubBase):
    method = 'put_bucket_notification_configuration'

    def __init__(self, bucket: str, prefix: str, lambda_arn: str):
        self.bucket = bucket
        self.prefix = prefix
        self.lambda_arn = lambda_arn

    @classmethod
    def from_stub(cls, stub: GetOneNotificationStub):
        return cls(
            stub.bucket,
            stub.prefix,
            stub.lambda_arn,
        )

    @property
    def expected_params(self):
        return {
            'Bucket': self.bucket,
            'NotificationConfiguration': {
                'LambdaFunctionConfigurations': [
                    {
                        'LambdaFunctionArn': self.lambda_arn,
                        'Events': [
                            's3:ObjectCreated:*',
                        ],
                        'Filter': {
                            'Key': {
                                'FilterRules': [
                                    {
                                        'Name': 'prefix',
                                        'Value': self.prefix,
                                    },
                                    {
                                        'Name': 'suffix',
                                        'Value': '.jsonl'
                                    },
                                ]
                            }
                        }
                    },
                ]
            }
        }

    @property
    def service_response(self):
        return {}


class PutEmptyNotificationStub(StubBase):
    method = 'put_bucket_notification_configuration'

    def __init__(self, bucket: str):
        self.bucket = bucket

    @classmethod
    def from_stub(cls, stub: GetOneNotificationStub):
        return cls(
            stub.bucket,
        )

    @property
    def expected_params(self):
        return {
            'Bucket': self.bucket,
            'NotificationConfiguration': {
                'LambdaFunctionConfigurations': []
            }
        }

    @property
    def service_response(self):
        return {}
