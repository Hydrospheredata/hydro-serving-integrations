# TrafficShadowing

**Note**, all scripts should be executed from this directory.

1. `sam-build.sh` — build a lambda function from the SAM template with all dependencies included.
1. `sam-invoke.sh` — invoke a lambda function for a given event.
1. `sam-package.sh` — package built lambda function and upload artifacts to S3.
1. `cf-build-upload.sh` — build a CloudFormation template from SAM artifacts and distribute across specified region buckets.

To deploy a new version of CloudFormation template, execute scripts in the following order.

```sh
./sam-build.sh && ./sam-package.sh && ./cf-build-upload.sh
```