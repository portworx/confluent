import json
import sdk_cmd as command
import sdk_spin as spin
import sdk_tasks as tasks

from tests.config import (
    DEFAULT_PARTITION_COUNT,
    SERVICE_NAME,
    DEFAULT_REPLICATION_FACTOR,
    DEFAULT_BROKER_COUNT,
    DEFAULT_PLAN_NAME,
    DEFAULT_PHASE_NAME,
    DEFAULT_POD_TYPE,
    DEFAULT_TASK_NAME
)


DEFAULT_TOPIC_NAME = 'topic1'
EPHEMERAL_TOPIC_NAME = 'topic2'

STATIC_PORT_OPTIONS_DICT = {"brokers": {"port": 9092}}
DYNAMIC_PORT_OPTIONS_DICT = {"brokers": {"port": 0}}
DEPLOY_STRATEGY_SERIAL_CANARY = {"service": {"deploy_strategy": "serial-canary"}}


def service_cli(cmd_str, get_json=True):
    full_cmd = '{} {}'.format(SERVICE_NAME, cmd_str)
    ret_str = command.run_cli(full_cmd)
    if get_json:
        return json.loads(ret_str)
    return ret_str

def broker_count_check(count):
    def fun():
        try:
            if len(service_cli('broker list')) == count:
                return True
        except:
            pass
        return False

    spin.time_wait_return(fun)


# Only use if need to wait for plan resource to start
def service_plan_wait(plan_name):
    def fun():
        try:
            return service_cli('plan show --json {}'.format(plan_name))
        except:
            return False

    return spin.time_wait_return(fun)


def wait_plan_complete():
    def plan_complete_fun():
        try:
            pl = service_cli('plan show --json {}'.format(DEFAULT_PLAN_NAME))
            if pl['status'] == 'COMPLETE':
                return True
        except:
            pass
        return False

    spin.time_wait_return(plan_complete_fun)


def restart_broker_pods(service_name=SERVICE_NAME):
    for i in range(DEFAULT_BROKER_COUNT):
        broker_id = tasks.get_task_ids(service_name,'{}-{}-{}'.format(DEFAULT_POD_TYPE, i, DEFAULT_TASK_NAME))
        restart_info = service_cli('pod restart {}-{}'.format(DEFAULT_POD_TYPE, i))
        tasks.check_tasks_updated(service_name, '{}-{}-{}'.format(DEFAULT_POD_TYPE, i, DEFAULT_TASK_NAME), broker_id)
        assert len(restart_info) == 2
        assert restart_info['tasks'][0] == '{}-{}-{}'.format(DEFAULT_POD_TYPE, i, DEFAULT_TASK_NAME)


def replace_broker_pod(service_name=SERVICE_NAME):
    broker_0_id = tasks.get_task_ids(service_name, '{}-0-{}'.format(DEFAULT_POD_TYPE, DEFAULT_TASK_NAME))
    service_cli('pod replace {}-0'.format(DEFAULT_POD_TYPE))
    tasks.check_tasks_updated(service_name, '{}-0-{}'.format(DEFAULT_POD_TYPE, DEFAULT_TASK_NAME), broker_0_id)
    tasks.check_running(service_name, DEFAULT_BROKER_COUNT)
    # wait till all brokers register
    broker_count_check(DEFAULT_BROKER_COUNT)


def create_topic(service_name=SERVICE_NAME):
    create_info = service_cli('topic create {}'.format(EPHEMERAL_TOPIC_NAME))
    print(create_info)
    assert ('Created topic "%s".\n' % EPHEMERAL_TOPIC_NAME in create_info['message'])

    topic_list_info = service_cli('topic list')
    assert EPHEMERAL_TOPIC_NAME in topic_list_info

    topic_info = service_cli('topic describe {}'.format(EPHEMERAL_TOPIC_NAME))
    assert len(topic_info) >= 1
    assert len(topic_info['partitions']) == DEFAULT_PARTITION_COUNT


def delete_topic(service_name=SERVICE_NAME):
    delete_info = service_cli('topic delete {}'.format(EPHEMERAL_TOPIC_NAME))

    assert len(delete_info) == 1
    assert delete_info['message'].startswith('Output: Topic {} is marked for deletion'.format(EPHEMERAL_TOPIC_NAME))

    topic_info = service_cli('topic describe {}'.format(EPHEMERAL_TOPIC_NAME))
    assert len(topic_info) == 1
    assert len(topic_info['partitions']) == DEFAULT_PARTITION_COUNT