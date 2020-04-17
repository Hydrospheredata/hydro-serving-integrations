#!/usr/bin/env sh

[ -z "$S3_DIST_BUCKET" ] && S3_DIST_BUCKET="hydrosphere-integrations"


create_bucket () {
    export BUCKET=$S3_DIST_BUCKET-$1
    envsubst '${BUCKET}' < public-bucket-policy.json.tmpl > public-bucket-policy.json
    aws s3 mb s3://$BUCKET --region $1
    aws s3api put-bucket-policy \
        --bucket $BUCKET \
        --policy file://public-bucket-policy.json \
        --confirm-remove-self-bucket-access
    aws s3api put-bucket-request-payment \
        --bucket $BUCKET \
        --request-payment-configuration '{"Payer": "Requester"}'
}


# Europe
for region in "eu-central-1" "eu-west-1" "eu-west-2" "eu-west-3" "eu-north-1" 
do  
    create_bucket $region
done

# US
for region in "us-east-1" "us-east-2" "us-west-1" "us-west-2"
do  
    create_bucket $region
done

# Canada
for region in "ca-central-1"
do  
    create_bucket $region
done

# Asia Pacific
for region in "ap-south-1" "ap-northeast-1" "ap-northeast-2" "ap-southeast-1" "ap-southeast-2" 
do  
    create_bucket $region
done

# South America
for region in "sa-east-1" 
do  
    create_bucket $region
done
