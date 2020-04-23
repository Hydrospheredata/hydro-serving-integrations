# hydro-serving-integrations

This repository contains implementations of integrations with AWS Sagemaker.

## Installation 

```sh
$ pip install hydro-integrations
```

## Usage

```python
from hydro_integrations.aws.sagemaker import TrafficShadowing
from sagemaker.model import Model
from sagemaker.model_monitor.data_capture_config import DataCaptureConfig

# Create Sagemaker Model 
model = Model(...)

# Define data capture config
data_capture_config = DataCaptureConfig(
    enable_capture=True,
    sampling_percentage=100,
    destination_s3_uri="s3://bucket/data/captured"
)

# Deploy Sagemaker model with the specified 
# data capture config
predictor = model.deploy(
    initial_instance_count=1,
    instance_type='ml.m4.xlarge',
    endpoint_name='model-shadowing-example',
    data_capture_config=data_capture_config
)

# Deploy TrafficShadowing CloudFormation stack. 
shadowing = TrafficShadowing(
    hydrosphere_endpoint="https://<hydrosphere>", 
    s3_data_training_uri="s3://bucket/data/training",
    data_capture_config=data_capture_config,
)
shadowing.deploy_stack()
```

## How it works

Once you've enabled data capturing on your AWS Sagemaker Endpoint, you can deploy TrafficShadowing CloudFormation stack, which contains AWS Lambda function responsible for shadowing traffic from configured S3 bucket to Hydrosphere for analysis.

**Note**, by default `destination_s3_uri` parameter, specified in the `DataCaptureConfig`, represents a prefix where your requests will be stored. In the example above, we've deployed a model with the endpoint name `model-shadowing-example`. This means that all requests collected from that model endpoint will be placed under `s3://bucket/data/captured/model-shadowing-example` path. Lambda function, deployed as part of the `TrafficShadowing` stack, expects that training data is organized in the same way, i.e., data used for training the `model-shadowing-example` model is placed under `s3://bucket/data/training/model-shadowing-example` path. Lambda function then finds the biggest `.csv` file under that directory and uploads it to the Hydrosphere platform for building profiles for your model.
