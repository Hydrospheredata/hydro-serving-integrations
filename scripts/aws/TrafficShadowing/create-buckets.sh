#!/usr/bin/env sh
[ -z "$S3_DIST_BUCKET" ] && S3_DIST_BUCKET="hydrosphere-integrations"

for region in "eu-west-3" "eu-central-1"
do
    aws s3 mb s3://$S3_DIST_BUCKET-$region --region $region
done