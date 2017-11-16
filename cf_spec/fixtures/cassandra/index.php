<?php
$cluster  = Cassandra::cluster()
  ->withContactPoints($_ENV["CASSANDRA_HOST"])
  ->withPort(9042)
  ->build();

$keyspace  = 'system';
$session   = $cluster->connect($keyspace);        // create session, optionally scoped to a keyspace
$statement = new Cassandra\SimpleStatement(       // also supports prepared and batch statements
      'SELECT keyspace_name, columnfamily_name FROM schema_columnfamilies'
    );
$future    = $session->executeAsync($statement);  // fully asynchronous and easy parallel execution
$result    = $future->get();                      // wait for the result, with an optional timeout

foreach ($result as $row) {                       // results and rows implement Iterator, Countable and ArrayAccess
      printf("The keyspace %s has a table called %s\n", $row['keyspace_name'], $row['columnfamily_name']);
}
?>
