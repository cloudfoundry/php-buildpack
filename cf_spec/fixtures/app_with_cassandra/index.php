<?php
require_once 'vendor/autoload.php';
use CfCommunity\CfHelper\CfHelper;
$cfHelper = CfHelper::getInstance();

# Get Cassandra VCAP_SERVICES values
$serviceManager = $cfHelper->getServiceManager();
#Cassandra service has to have cassandra in the name
$cassandraService = $serviceManager->getService('.*cassandra.*');
$node_ips = $cassandraService->getValue('node_ips');
$username = $cassandraService->getValue('username');
$password = $cassandraService->getValue('password');

#Datastax driver will autoconnect to rest of nodes based off one node connection
$node = current($node_ips);

#Connects to the Cassandra service
$cluster   = Cassandra::cluster()
                 ->withCredentials($username, $password)
                 ->withContactPoints($node)
                 ->build();
$session = $cluster->connect();

#Print keyspaces and tables
$keyspaces = $session->schema()->keyspaces();
echo "<table border=\"1\">";
echo "<tr><th>Keyspace</th><th>Table</th></tr>";
foreach ($keyspaces as $keyspace) {
    foreach ($keyspace->tables() as $table) {
        echo sprintf("<tr><td>%s</td><td>%s</td></tr>\n", $keyspace->name(), $table->name());
    }
}
echo "</table>";
