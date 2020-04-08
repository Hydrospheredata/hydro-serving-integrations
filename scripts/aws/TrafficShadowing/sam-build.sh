#!/usr/bin/env sh
set -e 

[ -z "$SOURCE_DIR" ] && SOURCE_DIR="../../../templates/aws/TrafficShadowing"
[ -z "$CODE_DIR" ] && CODE_DIR="../../../aws/TrafficShadowing"
[ -z "$DIST_DIR" ] && DIST_DIR="../../../dist/aws/TrafficShadowing"
[ -z "$BUILD_DIR" ] && BUILD_DIR="../../../build/aws/TrafficShadowing"
[ -z "$EVENT_JSON" ] && EVENT_JSON="../../../events/aws/TrafficShadowing/event.json"

sam build --debug \
    --use-container \
    --template ${SOURCE_DIR%/}/sam-template.yaml \
    --build-dir ${BUILD_DIR%/} \
    --base-dir ${CODE_DIR%/}
