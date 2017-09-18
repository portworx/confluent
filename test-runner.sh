#!/usr/bin/env bash

# Build a framework, package, upload it, and then run its integration tests.
# (Or all frameworks depending on arguments.) Expected to be called by test.sh

# Exit immediately on errors
set -e -x

# Remove the DC/OS cluster
cleanup() {
    dcos-launch delete
}

# Export the required environment variables:
export DCOS_ENTERPRISE
export PYTHONUNBUFFERED=1
export SECURITY


REPO_ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

if [ "$FRAMEWORK" = "all" ]; then
    if [ ! -n "$STUB_UNIVERSE_URL" ]; then
        echo "Cannot set \$STUB_UNIVERSE_URL when building all frameworks"
        exit 1
    fi
    if [ ! -n $FRAMEWORK_DIR ]; then
        echo "Cannot set \$FRAMEWORK_DIR when building all framworks"
        exit 1
    fi
    # randomize the FRAMEWORK_LIST
    FRAMEWORK_LIST=$(ls $REPO_ROOT_DIR/frameworks | while read -r fw; do printf "%05d %s\n" "$RANDOM" "$fw"; done | sort -n | cut -c7- )
else
    FRAMEWORK_LIST=$FRAMEWORK
fi

echo "Beginning integration tests at "`date`

pytest_args=()

if [ -n "$PYTEST_K" ]; then
    pytest_args+=(-k "$PYTEST_K")
fi

if [ -n "$PYTEST_M" ]; then
    pytest_args+=(-m "$PYTEST_M")
fi

if [ -n "$PYTEST_ARGS" ]; then
    # TeamCity strips double quotes from commands, meaning that we need to use
    # single quotes. Remove leading and trailing single quotes:
    PYTEST_ARGS=${${PYTEST_ARGS%\'}#\'}
    pytest_args+=("$PYTEST_ARGS")
fi

if [ -f /ssh/key ]; then
    eval "$(ssh-agent -s)"
    ssh-add /ssh/key
fi

for framework in $FRAMEWORK_LIST; do
    echo "STARTING: $framework"
    FRAMEWORK_DIR=$REPO_ROOT_DIR/frameworks/${framework}

    if [ ! -d ${FRAMEWORK_DIR} -a "${FRAMEWORK}" != "all" ]; then
        echo "FRAMEWORK_DIR=${FRAMEWORK_DIR} does not exist."
        echo "Assuming single framework in ${REPO_ROOT}."
        FRAMEWORK_DIR=${REPO_ROOT_DIR}
    fi

    if [ -z "$STUB_UNIVERSE_URL" ]; then
        echo "Starting build for $framework at "`date`
        export UNIVERSE_URL_PATH=${FRAMEWORK_DIR}/${framework}-universe-url
        ${FRAMEWORK_DIR}/build.sh aws
        if [ ! -f "$UNIVERSE_URL_PATH" ]; then
            echo "Missing universe URL file: $UNIVERSE_URL_PATH"
            exit 1
        fi
        export STUB_UNIVERSE_URL=$(cat $UNIVERSE_URL_PATH)
        echo "Finished build for $framework at "`date`
    else
        echo "Using provided STUB_UNIVERSE_URL: $STUB_UNIVERSE_URL"
    fi

    if [ -z "$CLUSTER_URL" ]; then

        echo "No DC/OS cluster specified. Attempting to create one now"
        dcos-launch create -c /build/config.yaml

        # enable the trap to ensure cleanup
        trap cleanup ERR

        dcos-launch wait

        # configure the dcos-cli/shakedown backend
        export CLUSTER_URL=https://`dcos-launch describe | jq -r .masters[0].public_ip`
        CLUSTER_WAS_CREATED=True
    fi

    echo "Configuring dcoscli for cluster: $CLUSTER_URL"
    echo "\tDCOS_ENTERPRISE=$DCOS_ENTERPRISE"
    /build/tools/dcos_login.py

    if [ `cat cluster_info.json | jq .key_helper` == 'true' ]; then
        cat cluster_info.json | jq -r .ssh_private_key > /root/.ssh/id_rsa
        chmod 600 /root/.ssh/id_rsa
    fi

    echo "Starting test for $framework at "`date`
    py.test -vv -s "${pytest_args[@]}" ${FRAMEWORK_DIR}/tests
    exit_code=$?
    echo "Finished test for $framework at "`date`

    set +e
    if [ -n ${CLUSTER_WAS_CREATED:-} ]; then
        dcos-launch delete
        unset CLUSTER_URL
    fi
done

echo "Finished integration tests at "`date`

exit $exit_code
