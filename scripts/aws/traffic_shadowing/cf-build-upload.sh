#!/bin/bash
set -ex

[ -z "$REGION" ] && REGION="eu-west-3"
[ -z "$SOURCE_DIR" ] && SOURCE_DIR="../../../templates/aws/traffic_shadowing"
[ -z "$DIST_DIR" ] && DIST_DIR="../../../dist/aws/traffic_shadowing"
[ -z "$S3_DIST_BUCKET" ] && S3_DIST_BUCKET="hydrosphere-integrations"
[ -z "$S3_APP_DIST_PREFIX" ] && S3_APP_DIST_PREFIX="lambda/traffic_shadowing"
[ -z "$S3_CF_DIST_PREFIX" ] && S3_CF_DIST_PREFIX="cloudformation/traffic_shadowing"

mkdir -p ${DIST_DIR%/}

suffix=$(cat /dev/urandom | LC_ALL=C tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)
echo "Copy template to ${DIST_DIR%/}/cf-template-$suffix.yaml"
cp ${SOURCE_DIR%/}/cf-template.yaml ${DIST_DIR%/}/cf-template-$suffix.yaml

echo "Extract S3 uri of the packaged lambda function from sam template"
S3_PACKAGE_VERSION_URI=$(yq r ${DIST_DIR%/}/sam-template.yaml Resources.TrafficShadowing.Properties.CodeUri)
IFS='/' read -r -a array <<< "$S3_PACKAGE_VERSION_URI"
S3_APP_DIST_KEY=${S3_APP_DIST_PREFIX%/}/${array[@]: -1:1}

echo "Create version of a cloudformation template"
IFS=' ' read -r -a md5array <<< $(md5 ${DIST_DIR%/}/cf-template-$suffix.yaml)
version=${md5array[0]}
printf $version > ../../../template_version.txt


publish_cf() {
    echo "Process $1 region"
    echo "Update S3 destination of the function in the cloudformation template"
    bucket=${S3_DIST_BUCKET%/}-$1
    yq w ${DIST_DIR%/}/cf-template-$suffix.yaml -i 'Resources.TrafficShadowingFunction.Properties.Code.S3Bucket' $bucket
    yq w ${DIST_DIR%/}/cf-template-$suffix.yaml -i 'Resources.TrafficShadowingFunction.Properties.Code.S3Key' $S3_APP_DIST_KEY
    cp ${DIST_DIR%/}/cf-template-$suffix.yaml ${DIST_DIR%/}/cf-$version.yaml

    echo "Upload result cloudformation script to s3://$bucket/${S3_CF_DIST_PREFIX%/}/$version"
    aws s3 cp ${DIST_DIR%/}/cf-$version.yaml s3://$bucket/${S3_CF_DIST_PREFIX%/}/$version.yaml
    if [ $REGION != $1 ]
    then 
        echo "Clone packaged lambda from s3://${S3_DIST_BUCKET%/}-$REGION/$S3_APP_DIST_KEY to s3://$bucket/$S3_APP_DIST_KEY"
        aws s3 cp s3://${S3_DIST_BUCKET%/}-$REGION/$S3_APP_DIST_KEY s3://$bucket/$S3_APP_DIST_KEY
    fi
}

# Europe
for region in "eu-central-1" "eu-west-1" "eu-west-2" "eu-west-3" "eu-north-1" 
do  
    publish_cf $region
done

# US
for region in "us-east-1" "us-east-2" "us-west-1" "us-west-2"
do  
    publish_cf $region
done

# Canada
for region in "ca-central-1"
do  
    publish_cf $region
done

# Asia Pacific
for region in "ap-south-1" "ap-northeast-1" "ap-northeast-2" "ap-southeast-1" "ap-southeast-2" 
do  
    publish_cf $region
done

# South America
for region in "sa-east-1" 
do  
    publish_cf $region
done

rm ${DIST_DIR%/}/cf-template-$suffix.yaml
