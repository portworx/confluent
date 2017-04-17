package com.mesosphere.sdk.confluent.kafka.scheduler;

import com.mesosphere.sdk.api.types.EndpointProducer;
import com.mesosphere.sdk.confluent.kafka.scheduler.api.BrokerResource;
import com.mesosphere.sdk.confluent.kafka.scheduler.api.KafkaZKClient;
import com.mesosphere.sdk.confluent.kafka.scheduler.api.TopicResource;
import com.mesosphere.sdk.confluent.kafka.scheduler.cmd.CmdExecutor;
import com.mesosphere.sdk.confluent.kafka.scheduler.upgrade.CuratorStateStoreFilter;
import com.mesosphere.sdk.confluent.kafka.scheduler.upgrade.KafkaConfigUpgrade;
import com.mesosphere.sdk.dcos.DcosConstants;
import com.mesosphere.sdk.offer.evaluate.placement.RegexMatcher;
import com.mesosphere.sdk.scheduler.DefaultScheduler;
import com.mesosphere.sdk.specification.DefaultService;
import com.mesosphere.sdk.specification.yaml.RawServiceSpec;
import com.mesosphere.sdk.specification.yaml.YAMLServiceSpecFactory;

import java.io.File;
import java.util.ArrayList;
import java.util.Collection;

/**
 * Kafka Service.
 */
public class KafkaService extends DefaultService {
    public KafkaService(File pathToYamlSpecification) throws Exception {
        RawServiceSpec rawServiceSpec = YAMLServiceSpecFactory.generateRawSpecFromYAML(pathToYamlSpecification);
        DefaultScheduler.Builder schedulerBuilder =
                DefaultScheduler.newBuilder(YAMLServiceSpecFactory.generateServiceSpec(rawServiceSpec));
        schedulerBuilder.setPlansFrom(rawServiceSpec);

        /* Upgrade */
        new KafkaConfigUpgrade(schedulerBuilder.getServiceSpec());
        CuratorStateStoreFilter stateStore = new CuratorStateStoreFilter(schedulerBuilder.getServiceSpec().getName(),
                DcosConstants.MESOS_MASTER_ZK_CONNECTION_STRING);
        stateStore.setIgnoreFilter(RegexMatcher.create("broker-[0-9]*"));
        schedulerBuilder.setStateStore(stateStore);
        /* Upgrade */

        schedulerBuilder.setEndpointProducer("zookeeper", EndpointProducer.constant(
                schedulerBuilder.getServiceSpec().getZookeeperConnection() +
                        DcosConstants.SERVICE_ROOT_PATH_PREFIX + schedulerBuilder.getServiceSpec().getName()));

        schedulerBuilder.setResources(
                getResources(
                        schedulerBuilder.getServiceSpec().getZookeeperConnection(),
                        schedulerBuilder.getServiceSpec().getName()));
        initService(schedulerBuilder);
    }

    private Collection<Object> getResources(String zookeeperConnection, String serviceName) {
        KafkaZKClient kafkaZKClient = new KafkaZKClient(
                zookeeperConnection,
                DcosConstants.SERVICE_ROOT_PATH_PREFIX + serviceName);

        final Collection<Object> apiResources = new ArrayList<>();
        apiResources.add(new BrokerResource(kafkaZKClient));
        apiResources.add(new TopicResource(
                new CmdExecutor(kafkaZKClient, System.getenv("KAFKA_VERSION_PATH")),
                kafkaZKClient));

        return apiResources;
    }
}