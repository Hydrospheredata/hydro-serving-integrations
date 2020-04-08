#!/usr/bin/env sh
set -e 

[ -z "$BUILD_DIR" ] && BUILD_DIR="../../../build/aws/TrafficShadowing"
[ -z "$EVENT_JSON" ] && EVENT_JSON="../../../events/aws/TrafficShadowing/event.json"

sam local invoke \
    --template ${BUILD_DIR%/}/template.yaml \
    --event $EVENT_JSON \
    --parameter-overrides \
        ParameterKey=S3DataCaptureBucketName,ParameterValue=sagemaker-us-east-2-943173312784 \
        ParameterKey=S3DataCapturePrefix,ParameterValue=sagemaker/DEMO-ModelMonitor/datacapture \
        ParameterKey=S3DataTrainingBucketName,ParameterValue=sagemaker-integration \
        ParameterKey=S3DataTrainingPrefix,ParameterValue=sagemaker/DEMO-ModelMonitor/baselining \
        ParameterKey=HydrosphereEndpoint,ParameterValue=https://hydro-serving.dev.hydrosphere.io