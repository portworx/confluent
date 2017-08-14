#!/usr/bin/env bash

set -e -x

PUBLISH_LOCATION="${1-aws}"

REPO_ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd $REPO_ROOT_DIR

# Build/upload framework scheduler artifact if one is not directly provided:
if [ -z "${STUB_UNIVERSE_URL}" ]; then
    STUB_UNIVERSE_URL=$(echo "${framework}_STUB_UNIVERSE_URL" | awk '{print toupper($0)}')
    # Build/upload framework scheduler:
    UNIVERSE_URL_PATH=confluent-universe-url
    UNIVERSE_URL_PATH=$UNIVERSE_URL_PATH ./build.sh aws

    if [ ! -f "$UNIVERSE_URL_PATH" ]; then
        echo "Missing universe URL file: $UNIVERSE_URL_PATH"
        exit 1
    fi
    export STUB_UNIVERSE_URL=$(cat $UNIVERSE_URL_PATH)
    rm  $UNIVERSE_URL_PATH
    echo "Built/uploaded stub universe: $STUB_UNIVERSE_URL"
else
    echo "Using provided STUB_UNIVERSE_URL: $STUB_UNIVERSE_URL"
fi

TEMP_DIR='_tmp_test_env'
# save time by using system packages if availble
# dcos and shakedown use libraries that may encounter system-level compatibility issues
python3 -m venv $TEMP_DIR
. $TEMP_DIR/bin/activate
pip3 install -r test_requirements.txt

# Get a CCM cluster if not already configured.
if [ -z "$CLUSTER_URL" ]; then
    # Warning: this will error out if set -o pipefail and set -e
    random_id=$(cat /dev/urandom | tr -dc 'a-z0-9' | fold -w 10 | head -n 1)
    cat <<EOF > config.yaml
---
launch_config_version: 1
deployment_name: dcos-ci-test-infinity-$random_id
template_url: https://s3.amazonaws.com/downloads.mesosphere.io/dcos-enterprise/testing/master/cloudformation/ee.single-master.cloudformation.json
provider: aws
aws_region: us-west-2
template_parameters:
    KeyName: default
    AdminLocation: 0.0.0.0/0
    PublicSlaveInstanceCount: 0
    SlaveInstanceCount: 6
ssh_user: core
EOF
    echo "CLUSTER_URL is empty/unset, launching new cluster."
    dcos-launch create
    dcos-launch wait
    dcos-launch describe
    # jq emits json strings by default: "value".  Use --raw-output to get value without quotes
    CLUSTER_URL=https://`dcos-launch describe | jq -r .masters[0].public_ip`
    echo
else
    echo "Using provided CLUSTER_URL as cluster: $CLUSTER_URL"
fi

# configure this session's CLI
dcos config set core.dcos_url $CLUSTER_URL
dcos config set core.ssl_verify false
tools/./dcos_login.py

dcos package repo add --index=0 test-confluent-kafka $STUB_UNIVERSE_URL

py.test -vv -k "sanity" tests/
