---
post_title: Managing
menu_order: 40
post_excerpt: ""
enterprise: 'no'
---

# Updating Configuration
You can make changes to the service after it has been launched. Configuration management is handled by the scheduler process, which in turn handles deploying Confluent Kafka itself.

Edit the runtime environment of the scheduler to make configuration changes. After making a change, the scheduler will be restarted and automatically deploy any detected changes to the service.

Some changes, such as decreasing the number of brokers or changing volume requirements, are not supported after initial deployment. See [Limitations](#limitations).

To see a full list of available options, run `dcos package describe --config beta-confluent-kafka` in the CLI, or browse the Confluent Kafka install dialog in the DC/OS web interface.

## Adding a Node
The service deploys `BROKER_COUNT` tasks by default. This can be customized at initial deployment or after the cluster is running. Shrinking the cluster is not supported.

## Resizing a Node
The CPU and Memory requirements of each broker can be increased or decreased as follows:
- CPU (1.0 = 1 core): `BROKER_CPUS`
- Memory (in MB): `BROKER_MEM`

**Note:** Volume requirements (type and/or size) cannot be changed after initial deployment.

## Updating Placement Constraints

Placement constraints can be updated after initial deployment using the following procedure. See [Service Settings](#service-settings) for more information on placement constraints.

Let's say we have the following deployment of our brokers:

- Placement constraint of: `hostname:LIKE:10.0.10.3|10.0.10.8|10.0.10.26|10.0.10.28|10.0.10.84`
- Tasks:
```
10.0.10.3: kafka-0
10.0.10.8: kafka-1
10.0.10.26: kafka-2
10.0.10.28: empty
10.0.10.84: empty
```

`10.0.10.8` is being decommissioned and we should move away from it. Steps:

1. Remove the decommissioned IP and add a new IP to the placement rule whitelist by editing `PLACEMENT_CONSTRAINT`:

	```
	hostname:LIKE:10.0.10.3|10.0.10.26|10.0.10.28|10.0.10.84|10.0.10.123
	```

# Restarting brokers

This operation will restart a broker while keeping it at its current location and with its current persistent volume data. This may be thought of as similar to restarting a system process, but it also deletes any data that is not on a persistent volume.

1. Run `dcos beta-confluent-kafka pods restart kafka-0 --name=confluent-kafka`

# Graceful Shutdown
## Extend the Kill Grace Period

Increase the `brokers.kill_grace_period` value via the DC/OS CLI, i.e.,  to `60`
seconds. This example assumes that the Kafka service instance is named `kafka`.

During the configuration update, each of the Kafka broker tasks are restarted. During
the shutdown portion of the task restart, the previous configuration value for
`brokers.kill_grace_period` is in effect. Following the shutdown, each broker
task is launched with the new effective configuration value. Take care to monitor
the amount of time Kafka brokers take to cleanly shutdown. Find the relevant log
entries in the [Configure](configure.md) section.

Create an options file `kafka-options.json` with the following content:

        {
            "brokers": {
               "kill_grace_period": 60
            }
        }

Issue the following command:

        dcos confluent-kafka --name=/kafka update --options=kafka-options.json

## Restart a Broker with Grace

A graceful (or clean) shutdown takes longer than an ungraceful shutdown, but the next startup will be much quicker. This is because the complex reconciliation activities that would have been required are not necessary after graceful shutdown.

## Replace a Broker with Grace

The grace period must also be respected when a broker is shut down before replacement. While it is not ideal that a broker must respect the grace period even if it is going to lose persistent state, this behavior will be improved in future versions of the SDK. Broker replacement generally requires complex and time-consuming reconciliation activities at startup if there was not a graceful shutdown, so the respect of the grace kill period still provides value in most situations. We recommend setting the kill grace period only sufficiently long enough to allow graceful shutdown. Monitor the Kafka broker clean shutdown times in the broker logs to keep this value tuned to the scale of data flowing through the Kafka service.
