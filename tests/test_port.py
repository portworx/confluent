import pytest

import sdk_install
import sdk_marathon
import sdk_tasks

from tests import config


def setup_module(module):
    sdk_install.uninstall(config.SERVICE_NAME, config.SERVICE_NAME)


def teardown_module(module):
    sdk_install.uninstall(config.SERVICE_NAME, config.SERVICE_NAME)


@pytest.mark.sanity
def static_to_static_port():
    sdk_install.install(config.SERVICE_NAME,
                    config.DEFAULT_BROKER_COUNT,
                    service_name=config.SERVICE_NAME,
                    additional_options={"brokers": {"port": 9092} })

    sdk_tasks.check_running(config.SERVICE_NAME, config.DEFAULT_BROKER_COUNT)

    broker_ids = sdk_tasks.get_task_ids(config.SERVICE_NAME, config.DEFAULT_POD_TYPE)

    for broker_id in range(config.DEFAULT_BROKER_COUNT):
        result = config.service_cli('broker get {}'.format(broker_id))
        assert result['port'] == 9092

    result = config.service_cli('endpoints broker')
    assert len(result['address']) == config.DEFAULT_BROKER_COUNT
    for port in result['address']:
        assert int(port.split(':')[-1]) == 9092
    assert len(result['dns']) == config.DEFAULT_BROKER_COUNT
    for port in result['dns']:
        assert int(port.split(':')[-1]) == 9092

    marathon_config = sdk_marathon.get_config(config.SERVICE_NAME)
    marathon_config['env']['BROKER_PORT'] = '9095'
    sdk_marathon.update_app(config.SERVICE_NAME, marathon_config)

    sdk_tasks.check_tasks_updated(config.SERVICE_NAME, config.DEFAULT_POD_TYPE, broker_ids)
    # all tasks are running
    sdk_tasks.check_running(config.SERVICE_NAME, config.DEFAULT_BROKER_COUNT)

    for broker_id in range(config.DEFAULT_BROKER_COUNT):
        result = config.service_cli('broker get {}'.format(broker_id))
        assert result['port'] == 9095

    result = config.service_cli('endpoints broker')
    assert len(result['address']) == config.DEFAULT_BROKER_COUNT
    for port in result['address']:
        assert int(port.split(':')[-1]) == 9095
    assert len(result['dns']) == config.DEFAULT_BROKER_COUNT
    for port in result['dns']:
        assert int(port.split(':')[-1]) == 9095


@pytest.mark.sanity
def static_to_dynamic_port():
    sdk_tasks.check_running(config.SERVICE_NAME, config.DEFAULT_BROKER_COUNT)

    broker_ids = sdk_tasks.get_task_ids(config.SERVICE_NAME, config.DEFAULT_POD_TYPE)

    marathon_config = sdk_marathon.get_config(config.SERVICE_NAME)
    marathon_config['env']['BROKER_PORT'] = '0'
    sdk_marathon.update_app(config.SERVICE_NAME, marathon_config)

    sdk_tasks.check_tasks_updated(config.SERVICE_NAME, config.DEFAULT_POD_TYPE, broker_ids)
    # all tasks are running
    sdk_tasks.check_running(config.SERVICE_NAME, config.DEFAULT_BROKER_COUNT)

    for broker_id in range(config.DEFAULT_BROKER_COUNT):
        result = config.service_cli('broker get {}'.format(broker_id))
        assert result['port'] != 9092

    result = config.service_cli('endpoints broker')
    assert len(result['address']) == config.DEFAULT_BROKER_COUNT
    for port in result['address']:
        assert int(port.split(':')[-1]) != 9092
    assert len(result['dns']) == config.DEFAULT_BROKER_COUNT
    for port in result['dns']:
        assert int(port.split(':')[-1]) != 9092


@pytest.mark.sanity
def dynamic_to_dynamic_port():
    sdk_tasks.check_running(config.SERVICE_NAME, config.DEFAULT_BROKER_COUNT)

    broker_ids = sdk_tasks.get_task_ids(config.SERVICE_NAME, config.DEFAULT_POD_TYPE)

    sdk_marathon.bump_cpu_count_config(config.SERVICE_NAME, 'BROKER_CPUS')

    sdk_tasks.check_tasks_updated(config.SERVICE_NAME, config.DEFAULT_POD_TYPE, broker_ids)
    # all tasks are running
    sdk_tasks.check_running(config.SERVICE_NAME, config.DEFAULT_BROKER_COUNT)



@pytest.mark.sanity
def dynamic_to_static_port():
    sdk_tasks.check_running(config.SERVICE_NAME, config.DEFAULT_BROKER_COUNT)
    broker_ids = sdk_tasks.get_task_ids(config.SERVICE_NAME, config.DEFAULT_POD_TYPE)

    marathon_config = sdk_marathon.get_config(config.SERVICE_NAME)
    marathon_config['env']['BROKER_PORT'] = '9092'
    sdk_marathon.update_app(config.SERVICE_NAME, marathon_config)

    sdk_tasks.check_tasks_updated(config.SERVICE_NAME, config.DEFAULT_POD_TYPE, broker_ids)
    # all tasks are running
    sdk_tasks.check_running(config.SERVICE_NAME, config.DEFAULT_BROKER_COUNT)

    for broker_id in range(config.DEFAULT_BROKER_COUNT):
        result = config.service_cli('broker get {}'.format(broker_id))
        assert result['port'] == 9092

