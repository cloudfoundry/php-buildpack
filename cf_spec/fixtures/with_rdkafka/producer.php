<html>
<head>
<title>Kafka Producer</title>
</head>
<body>
<h1>This PHP file is a Kafka Producer</h1>
<?php
    $conf = new RdKafka\Conf();
    $conf->setErrorCb(function ($kafka, $err, $reason) {
        printf("Kafka error: %s (reason: %s)\n", rd_kafka_err2str($err), $reason);
    });

    $producer = new RdKafka\Producer($conf);
    $producer->addBrokers("127.0.0.1");

    $topicConf = new RdKafka\TopicConf();
    $topicConf->set("message.timeout.ms", 1000);
    $testTopic = $producer->newTopic("test", $topicConf);

    $testTopic->produce(RD_KAFKA_PARTITION_UA, 0, "Hi");
?>
</body>
</html>
