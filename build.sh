#!/usr/bin/env bash
set -e

FRAMEWORK_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BUILD_DIR=$FRAMEWORK_DIR/build/distributions

BOOTSTRAP_DIR=disable \
EXECUTOR_DIR=disable \
TEMPLATE_DOCUMENTATION_PATH="https://www.confluent.io/whitepaper/deploying-confluent-platform-with-mesosphere" \
TEMPLATE_ISSUES_PATH="https://groups.google.com/forum/#!forum/confluent-platform" \
    $FRAMEWORK_DIR/tools/build_framework.sh \
        confluent-kafka \
        $FRAMEWORK_DIR \
        --artifact "$BUILD_DIR/confluent-kafka-scheduler.zip" \
        $@
