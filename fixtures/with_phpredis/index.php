<html>
<head>
<title>Redis Connection with phpredis</title>
</head>
<body>
<h1>This page initiates a Redis connection and displays Redis info via the phpredis client.</h1>
<?php
  $redisUrl = "localhost";
  $redisPort = 6379;
  $redisPassword = "password";

  print "<p>RedisUrl: $redisUrl</p>";
  print "<p>RedisPort: $redisPort</p>";
  print "<p>RedisPassword: redacted</p>";

  # Establish Redis connection and authenticate
  $redis = new Redis();
  $redis->connect($redisUrl, $redisPort);
  $redis->auth($redisPassword);
  $info = $redis->info();
  print_r($info);
?>
</body>
</html>
