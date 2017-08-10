import pytest

import json
import shakedown
import sdk_cmd as cmd
import sdk_install as install
import sdk_marathon as marathon
import sdk_upgrade as upgrade
import sdk_utils as utils
import sdk_tasks as tasks

from tests.test_utils import (
    DEFAULT_BROKER_COUNT,
    DEFAULT_POD_TYPE,
    SERVICE_NAME,
    DEFAULT_TASK_NAME,
    service_cli
)


def setup_module(module):
    install.uninstall(SERVICE_NAME)
    utils.gc_frameworks()


def teardown_module(module):
    install.uninstall(SERVICE_NAME)


@pytest.mark.sanity
@pytest.mark.smoke
@pytest.mark.upgrade
@pytest.mark.skipif('shakedown.dcos_version_less_than("1.9")',
                    reason="Feature only supported in DC/OS 1.9 and up")
def test_upgrade():
    upgrade.test_upgrade(
        "beta-{}".format(SERVICE_NAME),
        SERVICE_NAME,
        DEFAULT_BROKER_COUNT)


