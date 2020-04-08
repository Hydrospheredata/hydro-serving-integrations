#!/usr/bin/env sh

[ -z "$DIST_DIR" ] && DIST_DIR="../../../dist/aws/TrafficShadowing/"
[ -z "$BUILD_DIR" ] && BUILD_DIR="../../../build/aws/TrafficShadowing/"
[ -z "$S3_APP_DIST_BUCKET" ] && S3_APP_DIST_BUCKET="hydrosphere-integrations"
[ -z "$S3_APP_DIST_PREFIX" ] && S3_APP_DIST_PREFIX="lambda/TrafficShadowing"

mkdir -p ${DIST_DIR%/}/sam

current_region=$(aws configure get region)
sam package \
    --s3-bucket $S3_APP_DIST_BUCKET-$current_region \
    --s3-prefix $S3_APP_DIST_PREFIX \
    --template ${BUILD_DIR%/}/template.yaml \
    --output-template-file ${DIST_DIR%/}/sam-template.yaml