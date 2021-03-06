package com.mesosphere.sdk.confluent.kafka.scheduler;

import org.apache.commons.lang3.StringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import com.mesosphere.sdk.api.EndpointUtils;
import com.mesosphere.sdk.api.types.EndpointProducer;
import com.mesosphere.sdk.confluent.kafka.scheduler.api.BrokerResource;
import com.mesosphere.sdk.confluent.kafka.scheduler.api.KafkaZKClient;
import com.mesosphere.sdk.confluent.kafka.scheduler.api.TopicResource;
import com.mesosphere.sdk.confluent.kafka.scheduler.cmd.CmdExecutor;
import com.mesosphere.sdk.curator.CuratorUtils;
import com.mesosphere.sdk.scheduler.DefaultScheduler;
import com.mesosphere.sdk.scheduler.SchedulerFlags;
import com.mesosphere.sdk.scheduler.SchedulerUtils;
import com.mesosphere.sdk.specification.DefaultService;
import com.mesosphere.sdk.specification.DefaultServiceSpec;
import com.mesosphere.sdk.specification.yaml.RawServiceSpec;

import java.io.File;
import java.util.ArrayList;
import java.util.Collection;

/**
 * Apache Kafka Service.
 */
public class Main {
    private static final Logger LOGGER = LoggerFactory.getLogger(Main.class);
    private static final String KAFKA_ZK_URI_ENV = "KAFKA_ZOOKEEPER_URI";
    private static final String CONFLUENT_METRICS_BOOTSTRAP_ENV = "KAFKA_CONFLUENT_METRICS_REPORTER_BOOTSTRAP_SERVERS";
    private static final String CONFLUENT_METRICS_ZOOKEEPER_ENV = "KAFKA_CONFLUENT_METRICS_REPORTER_ZOOKEEPER_CONNECT";

    private static DefaultScheduler.Builder createSchedulerBuilder(File pathToYamlSpecification) throws Exception {
        RawServiceSpec rawServiceSpec = RawServiceSpec.newBuilder(pathToYamlSpecification).build();
        SchedulerFlags schedulerFlags = SchedulerFlags.fromEnv();

        // Allow users to manually specify a ZK location for kafka itself. Otherwise default to our service ZK location:
        String kafkaZookeeperUri = System.getenv(KAFKA_ZK_URI_ENV);
        if (StringUtils.isEmpty(kafkaZookeeperUri)) {
            // "master.mesos:2181" + "/dcos-service-path__to__my__kafka":
            kafkaZookeeperUri =
                    SchedulerUtils.getZkHost(rawServiceSpec, schedulerFlags)
                    + CuratorUtils.getServiceRootPath(rawServiceSpec.getName());
        }
        LOGGER.info("Running Kafka with zookeeper path: {}", kafkaZookeeperUri);

        DefaultScheduler.Builder schedulerBuilder = DefaultScheduler.newBuilder(
                DefaultServiceSpec.newGenerator(rawServiceSpec, schedulerFlags)
                        .setAllPodsEnv(KAFKA_ZK_URI_ENV, kafkaZookeeperUri)
                        .setAllPodsEnv(CONFLUENT_METRICS_ZOOKEEPER_ENV, kafkaZookeeperUri)
                        .setAllPodsEnv(CONFLUENT_METRICS_BOOTSTRAP_ENV,
                                EndpointUtils.toVipEndpoint(rawServiceSpec.getName(),
                                        new EndpointUtils.VipInfo("broker", 9092)))
                        .build(), schedulerFlags)
                .setPlansFrom(rawServiceSpec);

        return schedulerBuilder
                .setEndpointProducer("zookeeper", EndpointProducer.constant(kafkaZookeeperUri))
                .setCustomResources(getResources(kafkaZookeeperUri));
    }

    private static Collection<Object> getResources(String kafkaZookeeperUri) {
        KafkaZKClient kafkaZKClient = new KafkaZKClient(kafkaZookeeperUri);
        final Collection<Object> apiResources = new ArrayList<>();
        apiResources.add(new BrokerResource(kafkaZKClient));
        apiResources.add(new TopicResource(
                new CmdExecutor(kafkaZKClient, kafkaZookeeperUri, System.getenv("KAFKA_VERSION_PATH")),
                kafkaZKClient));
        return apiResources;
    }

    public static void main(String[] args) throws Exception {
        if (args.length > 0) {
            new DefaultService(createSchedulerBuilder(new File(args[0]))).run();
        } else {
            LOGGER.error("Missing file argument");
            System.exit(1);
        }
    }
}
