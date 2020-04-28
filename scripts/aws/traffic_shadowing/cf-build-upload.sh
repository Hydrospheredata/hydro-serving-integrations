#!/bin/bash
set -ex

[ -z "$REGION" ] && REGION="eu-west-3"
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

# Create version of a cloudformation/code template
IFS=' ' read -r -a md5cf <<< $(md5 -q ${DIST_DIR%/}/cf-template-$suffix.yaml)
version=${md5cf[0]}-${array[@]: -1:1}
printf $version > ../../../hydro_integrations/aws/sagemaker/traffic_shadowing_template_version

# Update S3 destination of the function in the cloudformation template
bucket=${S3_DIST_BUCKET%/}-$1
yq w ${DIST_DIR%/}/cf-template-$suffix.yaml -i 'Resources.CopyZips.Properties.SourceBucket' $bucket
yq w ${DIST_DIR%/}/cf-template-$suffix.yaml -i 'Resources.CopyZips.Properties.Objects[0]' $S3_APP_DIST_KEY
yq w ${DIST_DIR%/}/cf-template-$suffix.yaml -i 'Resources.TrafficShadowingFunction.Properties.Code.S3Key' $S3_APP_DIST_KEY
aws cloudformation validate-template --template-body file://${DIST_DIR%/}/cf-template-$suffix.yaml > /dev/null
cp ${DIST_DIR%/}/cf-template-$suffix.yaml ${DIST_DIR%/}/cf-$version.yaml

# Upload result cloudformation script to distribution bucket
aws s3 cp ${DIST_DIR%/}/cf-$version.yaml s3://$bucket/${S3_CF_DIST_PREFIX%/}/$version.yaml

rm ${DIST_DIR%/}/cf-template-$suffix.yaml
