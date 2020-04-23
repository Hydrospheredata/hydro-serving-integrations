#!/bin/bash
set -ex

[ -z "$BUILD_DIR" ] && BUILD_DIR="../../../build/aws/traffic_shadowing"
[ -z "$EVENT_JSON" ] && EVENT_JSON="../../../events/aws/traffic_shadowing/event.json"
[ -z "$S3_DATA_CAPTURE_BUCKET" ] && S3_DATA_CAPTURE_BUCKET="capture-bucket"
[ -z "$S3_DATA_CAPTURE_PREFIX" ] && S3_DATA_CAPTURE_PREFIX="capture/prefix"
[ -z "$S3_DATA_TRAINING_BUCKET" ] && S3_DATA_TRAINING_BUCKET="training-bucket"
[ -z "$S3_DATA_TRAINING_PREFIX" ] && S3_DATA_TRAINING_PREFIX="training/prefix"
[ -z "$HYDROSPHERE_ENDPOINT" ] && HYDROSPHERE_ENDPOINT="http://example.com"

sam local invoke \
    --template ${BUILD_DIR%/}/template.yaml \
    --event $EVENT_JSON \
    --parameter-overrides \
        ParameterKey=S3DataCaptureBucketName,ParameterValue=$S3_DATA_CAPTURE_BUCKET \
        ParameterKey=S3DataCapturePrefix,ParameterValue=$S3_DATA_CAPTURE_PREFIX \
        ParameterKey=S3DataTrainingBucketName,ParameterValue=$S3_DATA_TRAINING_BUCKET \
        ParameterKey=S3DataTrainingPrefix,ParameterValue=$S3_DATA_TRAINING_PREFIX \
        ParameterKey=HydrosphereEndpoint,ParameterValue=$HYDROSPHERE_ENDPOINT