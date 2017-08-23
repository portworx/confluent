import pytest

import shakedown # needed for version check below
import sdk_install
import sdk_upgrade

from tests import config


def setup_module(module):
    sdk_install.uninstall(config.SERVICE_NAME)


def teardown_module(module):
    sdk_install.uninstall(config.SERVICE_NAME)


@pytest.mark.sanity
@pytest.mark.smoke
@pytest.mark.upgrade
@pytest.mark.skipif('shakedown.dcos_version_less_than("1.9")',
                    reason="Feature only supported in DC/OS 1.9 and up")
def test_upgrade():
    # TODO: replace with an upgrade.test_upgrade call in the initialization of test_sanity.
    # at the moment this isn't feasible because test_sanity uses foldered paths, and the released
    # version of confluent-kafka (as of this writing) doesn't support them
    sdk_upgrade.test_upgrade(
        "beta-{}".format(config.SERVICE_NAME),
        config.SERVICE_NAME,
        config.DEFAULT_BROKER_COUNT)


