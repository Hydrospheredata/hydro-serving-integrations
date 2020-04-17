from typing import List, Dict, Iterable, Union
import hashlib
import logging
import urllib.parse
import boto3
import botocore
from sagemaker.model_monitor.data_capture_config import DataCaptureConfig
from hydro_integrations.aws.sagemaker import utils
from hydro_integrations.aws.sagemaker.exceptions import (
    FunctionNotFound, DataCaptureConfigException
)
from hydro_integrations.aws.cloudformation import CloudFormation
from hydro_integrations.aws.helpers import SessionMixin, AWSClientFactory

logger = logging.getLogger(__name__)


def flatten(items: Iterable) -> Iterable:
    """Yield items from any nested iterable."""
    for item in items:
        if isinstance(item, Iterable) and not isinstance(item, (str, bytes, dict)):
            for sub_item in flatten(item):
                yield sub_item
        else:
            yield item


def append_hash(target: str, to_hash: List[str]) -> str:
    """Generate the stack name based on the input arguments."""
    parameters_hash = hashlib.sha256()
    for item in to_hash:
        parameters_hash.update(item.encode())
    hexdigest = parameters_hash.hexdigest()
    return f"{target}-{hexdigest}"


def get_template_version() -> str:
    """Read template version from packaged file."""
    with open("template_version", "r") as file:
        return file.read().strip()


def get_region_bucket(region: str) -> str:
    """Return predefined regional buckets for CF resources."""
    return "hydrosphere-integrations-{}".format(region)


class TrafficShadowing(CloudFormation, SessionMixin):
    """ Serverless application to shadow traffic to Hydrosphere. """
    STACK_NAME = "traffic-shadowing-hydrosphere"
    TEMPLATE_URI = "https://{}.s3.{}.amazonaws.com/cloudformation/traffic_shadowing/{}.yaml"

    def __init__(
            self,
            hydrosphere_endpoint: str,
            s3_data_training_uri: str,
            data_capture_config: DataCaptureConfig,
            session: Union[boto3.Session, botocore.session.Session, None] = None,
    ):
        self._session = session or boto3.Session()
        self._s3_client = AWSClientFactory.get_or_create_client('s3', self._session)

        self.data_capture_enabled = data_capture_config.enable_capture
        if any(set(["REQUEST", "RESPONSE"]) - set(data_capture_config.capture_options)):
            raise DataCaptureConfigException(
                "Data capturing should be configured to capture requests and responses.")

        self.template_url = self.TEMPLATE_URI.format(
            get_region_bucket(self.get_region()),
            self.get_region(),
            get_template_version()
        )

        utils.validate_non_empty_uri(hydrosphere_endpoint, True, True, False)
        self.hydrosphere_endpoint = hydrosphere_endpoint

        utils.validate_non_empty_uri(data_capture_config.destination_s3_uri, True, True, True)
        capture_parse = urllib.parse.urlparse(data_capture_config.destination_s3_uri)
        self.s3_data_capture_bucket = capture_parse.netloc
        self.s3_data_capture_prefix = capture_parse.path.strip('/')

        utils.validate_non_empty_uri(s3_data_training_uri, True, True, True)
        training_parse = urllib.parse.urlparse(s3_data_training_uri)
        self.s3_data_training_bucket = training_parse.netloc
        self.s3_data_training_prefix = training_parse.path.strip('/')
        self._validate_deployment_configuration()

        self.stack_name = append_hash(
            target=self.STACK_NAME,
            to_hash=[
                self.template_url,
                hydrosphere_endpoint,
                s3_data_training_uri,
                str(data_capture_config._to_request_dict()),
            ],
        )

        super().__init__(
            self.template_url,
            self.stack_name,
            self.get_stack_parameters(),
            self.get_stack_capabilities(),
            self._session,
        )

    def _validate_deployment_configuration(self):
        response = self._s3_client.get_bucket_location(
            Bucket=self.s3_data_capture_bucket
        )
        assert self.get_region() == response['LocationConstraint'], \
            f'Session region {self.get_region()} does not match with the data capture ' \
            f'bucket {self.s3_data_capture_bucket}'

    def get_stack_parameters(self) -> List[Dict[str, str]]:
        """Return Parameters for CloudFormation template."""
        return [
            {
                "ParameterKey": "S3DataCaptureBucketName",
                "ParameterValue": self.s3_data_capture_bucket,
            },
            {
                "ParameterKey": "S3DataCapturePrefix",
                "ParameterValue": self.s3_data_capture_prefix,
            },
            {
                "ParameterKey": "S3DataTrainingBucketName",
                "ParameterValue": self.s3_data_training_bucket,
            },
            {
                "ParameterKey": "S3DataTrainingPrefix",
                "ParameterValue": self.s3_data_training_prefix,
            },
            {
                "ParameterKey": "HydrosphereEndpoint",
                "ParameterValue": self.hydrosphere_endpoint,
            },
        ]

    def get_stack_capabilities(self) -> List[str]:
        """Get capabilities list for deploying underlying CloudFormation stack."""
        return ["CAPABILITY_NAMED_IAM"]

    def _get_lambda_arn(self) -> dict:
        """Retrieve Arn of the deployed TrafficShadowingFunction Lambda."""
        return next(filter(
            lambda x: x['OutputKey'] == 'TrafficShadowingFunctionArn', self.stack_outputs
        ))['OutputValue']

    def _get_bucket_notification_configuration(self):
        """Retrieve current notification configuration of the bucket."""
        result = self._s3_client.get_bucket_notification_configuration(
            Bucket=self.s3_data_capture_bucket
        )
        return result

    def _add_bucket_notification(self, replace: bool = False):
        """
        Append a new lambda notification to the existing notification
        configuration of the data capture bucket.
        """
        if replace:
            logger.info("Replacing bucket notification.")
            configuration = {}
            lambda_configurations = []
        else:
            logger.info("Adding bucket notification.")
            configuration = self._get_bucket_notification_configuration()
            lambda_configurations = configuration.get('LambdaFunctionConfigurations', [])

        lambda_arn = self._get_lambda_arn()
        targets = filter(lambda x: x['LambdaFunctionArn'] == lambda_arn, lambda_configurations)
        rules = map(lambda x: x['Filter']['Key']['FilterRules'], targets)
        flattened_rules = flatten(rules)
        prefixes = filter(lambda x: x['Name'].lower() == 'prefix', flattened_rules)
        if any([item['Value'] == self.s3_data_capture_prefix for item in prefixes]):
            return logger.info("Found similar bucket notification configuration.")

        lambda_configurations.append({
            'LambdaFunctionArn': self._get_lambda_arn(),
            'Events': [
                's3:ObjectCreated:*'
            ],
            'Filter': {
                'Key': {
                    'FilterRules': [
                        {
                            'Name': 'prefix',
                            'Value': self.s3_data_capture_prefix,
                        },
                        {
                            'Name': 'suffix',
                            'Value': '.jsonl'
                        }
                    ]
                }
            }
        })

        configuration['LambdaFunctionConfigurations'] = lambda_configurations
        self._s3_client.put_bucket_notification_configuration(
            Bucket=self.s3_data_capture_bucket,
            NotificationConfiguration=configuration
        )

    def _delete_bucket_notification(self, purge: bool = False):
        """
        Delete lambda notification from the existing notification
        configuration of the data capture bucket.
        """
        lambda_arn = None

        try:
            lambda_arn = self._get_lambda_arn()
        except FunctionNotFound:
            logger.warning("Could not find deployed function arn.")
            if not purge:
                logger.warning("Skipping bucket notification deletion.")
                return None
            else:
                logger.info("Purging bucket notification configuration.")

        if purge:
            configuration = {}
            lambda_configurations = []
        else:
            configuration = self._get_bucket_notification_configuration()
            lambda_configurations = [
                item for item in configuration.get('LambdaFunctionConfigurations', [])
                if item['LambdaFunctionArn'] != lambda_arn
            ]

        configuration['LambdaFunctionConfigurations'] = lambda_configurations
        self._s3_client.put_bucket_notification_configuration(
            Bucket=self.s3_data_capture_bucket,
            NotificationConfiguration=configuration,
        )

    def deploy_stack(self, replace_notification_configuration: bool = False):
        """Synchronously deploy the stack and updates notification configurations."""
        if self.data_capture_enabled:
            self._deploy_stack()
            self._add_bucket_notification(replace_notification_configuration)
        else:
            logger.warning("Data capturing wasn't enabled. Skipping stack deployment.")

    def delete_stack(self, purge_notification_configuration: bool = False):
        """Synchronously delete notification configurations and the stack."""
        self._delete_bucket_notification(purge_notification_configuration)
        self._delete_stack()
