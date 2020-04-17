#!/usr/bin/env sh

[ -z "$REGION" ] && REGION="eu-west-3"
[ -z "$DIST_DIR" ] && DIST_DIR="../../../dist/aws/traffic_shadowing/"
[ -z "$BUILD_DIR" ] && BUILD_DIR="../../../build/aws/traffic_shadowing/"
[ -z "$S3_APP_DIST_BUCKET" ] && S3_APP_DIST_BUCKET="hydrosphere-integrations"
[ -z "$S3_APP_DIST_PREFIX" ] && S3_APP_DIST_PREFIX="lambda/traffic_shadowing"

mkdir -p ${DIST_DIR%/}/sam

sam package \
    --s3-bucket $S3_APP_DIST_BUCKET-$REGION \
    --s3-prefix $S3_APP_DIST_PREFIX \
    --template ${BUILD_DIR%/}/template.yaml \
    --output-template-file ${DIST_DIR%/}/sam-template.yaml