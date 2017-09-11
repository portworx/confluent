import json
import sdk_cmd


SERVICE_NAME = 'confluent-kafka'
PACKAGE_NAME = 'confluent-kafka'
DEFAULT_BROKER_COUNT = 3
DEFAULT_POD_TYPE = 'kafka'
DEFAULT_TASK_NAME = 'broker'


def service_cli(cmd_str, service_name=SERVICE_NAME, get_json=True):
    ret_str = sdk_cmd.run_cli('{} --name={} {}'.format(SERVICE_NAME, service_name, cmd_str))
    if get_json:
        return json.loads(ret_str)
    return ret_str
