#!/usr/bin/env sh
set -e

[ -z "$SOURCE_DIR" ] && SOURCE_DIR="../../../templates/aws/TrafficShadowing"
[ -z "$DIST_DIR" ] && DIST_DIR="../../../dist/aws/TrafficShadowing"
[ -z "$S3_DIST_BUCKET" ] && S3_DIST_BUCKET="hydrosphere-integrations"
[ -z "$S3_APP_DIST_PREFIX" ] && S3_APP_DIST_PREFIX="lambda/TrafficShadowing"
[ -z "$S3_CF_DIST_PREFIX" ] && S3_CF_DIST_PREFIX="cloudformation/TrafficShadowing"

mkdir -p ${DIST_DIR%/}

suffix=$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
echo "Copy template to ${DIST_DIR%/}/cf-template-$suffix.yaml"
cp ${SOURCE_DIR%/}/cf-template.yaml ${DIST_DIR%/}/cf-template-$suffix.yaml

echo "Extract S3 uri of the packaged lambda function from sam template"
S3_PACKAGE_VERSION_URI=$(yq r ${DIST_DIR%/}/sam-template.yaml Resources.TrafficShadowing.Properties.CodeUri)
IFS='/' read -r -a array <<< "$S3_PACKAGE_VERSION_URI"
S3_APP_DIST_KEY=${S3_APP_DIST_PREFIX%/}/${array[@]: -1:1}

echo "Create version of a cloudformation template"
version=$(md5 -q ${DIST_DIR%/}/cf-template-$suffix.yaml)
printf $version > ../../../template_version.txt

current_region=$(aws configure get region)
for target_region in "eu-west-3" "eu-central-1"
do 
    echo "Process $target_region region"
    echo "Update S3 destination of the function in the cloudformation template"
    yq w ${DIST_DIR%/}/cf-template-$suffix.yaml -i 'Resources.TrafficShadowingFunction.Properties.Code.S3Bucket' $S3_DIST_BUCKET-$target_region
    yq w ${DIST_DIR%/}/cf-template-$suffix.yaml -i 'Resources.TrafficShadowingFunction.Properties.Code.S3Key' $S3_APP_DIST_KEY
    cp ${DIST_DIR%/}/cf-template-$suffix.yaml ${DIST_DIR%/}/cf-$version.yaml

    echo "Upload result cloudformation script to s3://${S3_DIST_BUCKET%/}-$target_region/${S3_CF_DIST_PREFIX%/}/$version"
    aws s3 cp ${DIST_DIR%/}/cf-$version.yaml s3://${S3_DIST_BUCKET%/}-$target_region/${S3_CF_DIST_PREFIX%/}/$version.yaml
    if [ $current_region != $target_region ]
    then 
        echo "Clone packaged lambda to s3://${S3_DIST_BUCKET%/}-$current_region/$S3_APP_DIST_KEY"
        aws s3 cp s3://${S3_DIST_BUCKET%/}-$current_region/$S3_APP_DIST_KEY s3://${S3_DIST_BUCKET%/}-$target_region/$S3_APP_DIST_KEY
    fi
done

rm ${DIST_DIR%/}/cf-template-$suffix.yaml
