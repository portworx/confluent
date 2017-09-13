This document describes the process of updating the testing and release tooling from the DC/OS SDK.

This assumes that the https://github.com/mesosphere/dcos-commons repo has been cloned, the desired branch (either `master` or `0.30.X`) has been checked out
and the `SDK_ROOT` environment variable set:
```bash
$ git clone git@github.com:mesosphere/dcos-commons.git
$ cd dcos-commons
$ export SDK_ROOT=$(pwd)
```

The `--dry-run` flag can be added to the commands below to check which files would be copied or deleted.

After each step, check the output of `git diff` and `git status` to ensure that the changes are expected. Once this is done, these can be committed.

1. Copy `tools` files:
    ```bash
    $ rsync -avz --delete $SDK_ROOT/tools .
    ```
1. Copy `testing` files:
    ```bash
    $ rsync -avz --delete $SDK_ROOT/testing .
    ```
1. Copy `kafka` tests:
    ```bash
    $ rsync -avz --delete $SDK_ROOT/frameworks/kafka/tests .
    ```
1. Copy `kafka` CLI:
    ```bash
    $ rsync -avz --delete $SDK_ROOT/frameworks/kafka/cli/dcos-kafka/* cli/dcos-confluent-kafka
    ```
