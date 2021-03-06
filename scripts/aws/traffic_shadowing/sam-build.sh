#!/bin/bash
set -ex

[ -z "$SOURCE_DIR" ] && SOURCE_DIR="../../../templates/aws/traffic_shadowing"
[ -z "$CODE_DIR" ] && CODE_DIR="../../../aws/traffic_shadowing"
[ -z "$DIST_DIR" ] && DIST_DIR="../../../dist/aws/traffic_shadowing"
[ -z "$BUILD_DIR" ] && BUILD_DIR="../../../build/aws/traffic_shadowing"

sam build --debug \
    --use-container \
    --template ${SOURCE_DIR%/}/sam-template.yaml \
    --build-dir ${BUILD_DIR%/} \
    --base-dir ${CODE_DIR%/}
