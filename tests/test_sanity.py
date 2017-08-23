import pytest

import shakedown

import sdk_hosts
import sdk_install
import sdk_metrics
import sdk_tasks
import sdk_utils

from tests import config


FOLDERED_SERVICE_NAME = sdk_utils.get_foldered_name(config.SERVICE_NAME)

TOPIC_NAME = 'topic1'
EPHEMERAL_TOPIC_NAME = 'topic2'

DEFAULT_REPLICATION_FACTOR = 1
DEFAULT_PARTITION_COUNT = 1


def setup_module(module):
    sdk_install.uninstall(config.SERVICE_NAME, config.SERVICE_NAME)
    sdk_install.uninstall(FOLDERED_SERVICE_NAME, config.SERVICE_NAME)

    sdk_install.install(
        config.SERVICE_NAME,
        config.DEFAULT_BROKER_COUNT,
        service_name=FOLDERED_SERVICE_NAME,
        additional_options={"service": {"name": FOLDERED_SERVICE_NAME}})
    # TODO: exercise upgrade as a part of sanity tests (saves time on not installing yet another time)
    # at the moment this isn't feasible because test_sanity uses foldered paths, and the released
    # version of confluent-kafka (as of this writing) doesn't support them
    #sdk_upgrade.test_upgrade(
    #    config.SERVICE_NAME,
    #    config.SERVICE_NAME,
    #    config.DEFAULT_BROKER_COUNT,
    #    service_name=FOLDERED_SERVICE_NAME,
    #    additional_options={"service": {"name": FOLDERED_SERVICE_NAME}})


def teardown_module(module):
    sdk_install.uninstall(FOLDERED_SERVICE_NAME, config.SERVICE_NAME)


# --------- Endpoints -------------


@pytest.mark.smoke
@pytest.mark.sanity
def test_endpoints_address():
    def fun():
        ret = config.service_cli('endpoints {}'.format(config.DEFAULT_TASK_NAME), service_name=FOLDERED_SERVICE_NAME)
        if len(ret['address']) == config.DEFAULT_BROKER_COUNT:
            return ret
        return False
    endpoints = shakedown.wait_for(fun)
    assert len(endpoints['address']) == config.DEFAULT_BROKER_COUNT
    assert len(endpoints['dns']) == config.DEFAULT_BROKER_COUNT
    for i in range(len(endpoints['dns'])):
        assert sdk_hosts.autoip_host(FOLDERED_SERVICE_NAME, 'kafka-{}-broker'.format(i)) in endpoints['dns'][i]
    assert endpoints['vip'] == sdk_hosts.vip_host(FOLDERED_SERVICE_NAME, 'broker', 9092)


@pytest.mark.smoke
@pytest.mark.sanity
def test_endpoints_zookeeper():
    zookeeper = config.service_cli('endpoints zookeeper', service_name=FOLDERED_SERVICE_NAME, get_json=False)
    assert zookeeper.rstrip() == (
        'master.mesos:2181/dcos-service-{}'.format(sdk_utils.get_zk_path(config.SERVICE_NAME))
    )


# --------- Broker -------------


@pytest.mark.smoke
@pytest.mark.sanity
def test_broker_list():
    brokers = config.service_cli('broker list', service_name=FOLDERED_SERVICE_NAME)
    assert set(brokers) == set([str(i) for i in range(config.DEFAULT_BROKER_COUNT)])


@pytest.mark.smoke
@pytest.mark.sanity
def test_broker_invalid():
    try:
        config.service_cli('broker get {}'.format(config.DEFAULT_BROKER_COUNT + 1), service_name=FOLDERED_SERVICE_NAME)
        assert False, "Should have failed"
    except AssertionError as arg:
        raise arg
    except:
        pass  # expected to fail

# --------- Pods -------------


@pytest.mark.smoke
@pytest.mark.sanity
def test_pod_restart():
    for i in range(config.DEFAULT_BROKER_COUNT):
        pod_name = '{}-{}'.format(config.DEFAULT_POD_TYPE, i)
        task_name = '{}-{}'.format(pod_name, config.DEFAULT_TASK_NAME)

        broker_id = sdk_tasks.get_task_ids(FOLDERED_SERVICE_NAME, task_name)
        restart_info = config.service_cli('pod restart {}'.format(pod_name), service_name=FOLDERED_SERVICE_NAME)
        sdk_tasks.check_tasks_updated(FOLDERED_SERVICE_NAME, task_name, broker_id)
        sdk_tasks.check_running(FOLDERED_SERVICE_NAME, config.DEFAULT_BROKER_COUNT)
        assert len(restart_info) == 2
        assert restart_info['tasks'][0] == task_name


@pytest.mark.smoke
@pytest.mark.sanity
def test_pod_replace():
    pod_name = '{}-0'.format(config.DEFAULT_POD_TYPE)
    task_name = '{}-{}'.format(pod_name, config.DEFAULT_TASK_NAME)

    broker_0_id = sdk_tasks.get_task_ids(FOLDERED_SERVICE_NAME, task_name)
    config.service_cli('pod replace {}'.format(pod_name), service_name=FOLDERED_SERVICE_NAME)
    sdk_tasks.check_tasks_updated(FOLDERED_SERVICE_NAME, task_name, broker_0_id)
    sdk_tasks.check_running(FOLDERED_SERVICE_NAME, config.DEFAULT_BROKER_COUNT)
    # wait till all brokers register

    def fn():
        try:
            if len(config.service_cli('broker list', service_name=FOLDERED_SERVICE_NAME)) == config.DEFAULT_BROKER_COUNT:
                return True
        except:
            pass
        return False
    shakedown.wait_for(fn, noisy=True, timeout_seconds=15*60)


# --------- Topics -------------

@pytest.mark.smoke
@pytest.mark.sanity
def test_topic_create():
    create_info = config.service_cli('topic create {}'.format(EPHEMERAL_TOPIC_NAME), service_name=FOLDERED_SERVICE_NAME)
    print(create_info)
    assert ('Created topic "%s".\n' % EPHEMERAL_TOPIC_NAME in create_info['message'])

    topic_list_info = config.service_cli('topic list', service_name=FOLDERED_SERVICE_NAME)
    assert EPHEMERAL_TOPIC_NAME in topic_list_info

    topic_info = config.service_cli('topic describe {}'.format(EPHEMERAL_TOPIC_NAME), service_name=FOLDERED_SERVICE_NAME)
    assert len(topic_info) >= 1
    assert len(topic_info['partitions']) == DEFAULT_PARTITION_COUNT


@pytest.mark.smoke
@pytest.mark.sanity
def test_topic_delete():
    delete_info = config.service_cli('topic delete {}'.format(EPHEMERAL_TOPIC_NAME), service_name=FOLDERED_SERVICE_NAME)

    assert len(delete_info) == 1
    assert delete_info['message'].startswith('Output: Topic {} is marked for deletion'.format(EPHEMERAL_TOPIC_NAME))

    topic_info = config.service_cli('topic describe {}'.format(EPHEMERAL_TOPIC_NAME), service_name=FOLDERED_SERVICE_NAME)
    assert len(topic_info) == 1
    assert len(topic_info['partitions']) == DEFAULT_PARTITION_COUNT


@pytest.mark.sanity
def test_topic_partition_count():
    config.service_cli('topic create {}'.format(TOPIC_NAME), service_name=FOLDERED_SERVICE_NAME)
    topic_info = config.service_cli('topic describe {}'.format(TOPIC_NAME), service_name=FOLDERED_SERVICE_NAME)
    assert len(topic_info['partitions']) == DEFAULT_PARTITION_COUNT


@pytest.mark.sanity
def test_topic_offsets_increase_with_writes():
    offset_info = config.service_cli('topic offsets --time="-1" {}'.format(TOPIC_NAME), service_name=FOLDERED_SERVICE_NAME)
    assert len(offset_info) == DEFAULT_PARTITION_COUNT

    offsets = {}
    for o in offset_info:
        assert len(o) == DEFAULT_REPLICATION_FACTOR
        offsets.update(o)

    assert len(offsets) == DEFAULT_PARTITION_COUNT

    num_messages = 10
    write_info = config.service_cli('topic producer_test {} {}'.format(TOPIC_NAME, num_messages), service_name=FOLDERED_SERVICE_NAME)
    assert len(write_info) == 1
    assert write_info['message'].startswith('Output: {} records sent'.format(num_messages))

    offset_info = config.service_cli('topic offsets --time="-1" {}'.format(TOPIC_NAME), service_name=FOLDERED_SERVICE_NAME)
    assert len(offset_info) == DEFAULT_PARTITION_COUNT

    post_write_offsets = {}
    for offsets in offset_info:
        assert len(o) == DEFAULT_REPLICATION_FACTOR
        post_write_offsets.update(o)

    assert not offsets == post_write_offsets


@pytest.mark.sanity
def test_decreasing_topic_partitions_fails():
    partition_info = config.service_cli('topic partitions {} {}'.format(TOPIC_NAME, DEFAULT_PARTITION_COUNT - 1), service_name=FOLDERED_SERVICE_NAME)

    assert len(partition_info) == 1
    assert partition_info['message'].startswith('Output: WARNING: If partitions are increased')
    assert ('The number of partitions for a topic can only be increased' in partition_info['message'])


@pytest.mark.sanity
def test_setting_topic_partitions_to_same_value_fails():
    partition_info = config.service_cli('topic partitions {} {}'.format(TOPIC_NAME, DEFAULT_PARTITION_COUNT), service_name=FOLDERED_SERVICE_NAME)

    assert len(partition_info) == 1
    assert partition_info['message'].startswith('Output: WARNING: If partitions are increased')
    assert ('The number of partitions for a topic can only be increased' in partition_info['message'])


@pytest.mark.sanity
def test_increasing_topic_partitions_succeeds():
    partition_info = config.service_cli('topic partitions {} {}'.format(TOPIC_NAME, DEFAULT_PARTITION_COUNT + 1), service_name=FOLDERED_SERVICE_NAME)

    assert len(partition_info) == 1
    assert partition_info['message'].startswith('Output: WARNING: If partitions are increased')
    assert ('The number of partitions for a topic can only be increased' not in partition_info['message'])


@pytest.mark.sanity
def test_no_under_replicated_topics_exist():
    partition_info = config.service_cli('topic under_replicated_partitions', service_name=FOLDERED_SERVICE_NAME)

    assert len(partition_info) == 1
    assert partition_info['message'] == ''


@pytest.mark.sanity
def test_no_unavailable_partitions_exist():
    partition_info = config.service_cli('topic unavailable_partitions', service_name=FOLDERED_SERVICE_NAME)

    assert len(partition_info) == 1
    assert partition_info['message'] == ''


@pytest.mark.sanity
@sdk_utils.dcos_1_9_or_higher
def test_metrics():
    sdk_metrics.wait_for_any_metrics(FOLDERED_SERVICE_NAME, "kafka-0-broker", 10 * 60)
