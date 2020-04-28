#!/bin/bash
set -ex

[ -z "$SOURCE_DIR" ] && SOURCE_DIR="../../../templates/aws/traffic_shadowing"
[ -z "$DIST_DIR" ] && DIST_DIR="../../../dist/aws/traffic_shadowing"
[ -z "$S3_DIST_BUCKET" ] && S3_DIST_BUCKET="hydrosphere-integrations"
[ -z "$S3_APP_DIST_PREFIX" ] && S3_APP_DIST_PREFIX="lambda/traffic_shadowing"
[ -z "$S3_CF_DIST_PREFIX" ] && S3_CF_DIST_PREFIX="cloudformation/traffic_shadowing"

mkdir -p ${DIST_DIR%/}

# Copy template to distribution directory
suffix=$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
cp ${SOURCE_DIR%/}/cf-template.yaml ${DIST_DIR%/}/cf-template-$suffix.yaml

# Extract S3 uri of the packaged lambda function from sam template
S3_PACKAGE_VERSION_URI=$(yq r ${DIST_DIR%/}/sam-template.yaml Resources.TrafficShadowing.Properties.CodeUri)
IFS='/' read -r -a array <<< "$S3_PACKAGE_VERSION_URI"
S3_APP_DIST_KEY=${S3_APP_DIST_PREFIX%/}/${array[@]: -1:1}

# Update S3 destination of the function in the cloudformation template
SOURCE_BUCKET=${S3_DIST_BUCKET%/}
yq w ${DIST_DIR%/}/cf-template-$suffix.yaml -i 'Resources.CopyZips.Properties.SourceBucket' $SOURCE_BUCKET
yq w ${DIST_DIR%/}/cf-template-$suffix.yaml -i 'Resources.CopyZips.Properties.Objects[0]' $S3_APP_DIST_KEY
yq w ${DIST_DIR%/}/cf-template-$suffix.yaml -i 'Resources.TrafficShadowingFunction.Properties.Code.S3Key' $S3_APP_DIST_KEY
aws cloudformation validate-template --template-body file://${DIST_DIR%/}/cf-template-$suffix.yaml > /dev/null
cp ${DIST_DIR%/}/cf-template-$suffix.yaml ../../../hydro_integrations/aws/sagemaker/traffic_shadowing/template.yaml

rm ${DIST_DIR%/}/cf-template-$suffix.yaml
