<html>
<head>
<title>Redis Connection with phpredis</title>
</head>
<body>
<h1>This page initiates a Redis connection and displays Redis info via the phpredis client.</h1>
<?php
  require_once 'vendor/autoload.php';
  use CfCommunity\CfHelper\CfHelper;
  $cfHelper = CfHelper::getInstance();

  # Try to fetch Redis VCAP_SERVICES values
  $serviceManager = $cfHelper->getServiceManager();
  $redisService = $serviceManager->getService('.*redis.*');

  $defaultUrl = "localhost";
  $defaulPort = 6379;
  $defaulPassword = "password";

  # Prevent PHP Errors if no service is bound
  if (is_null($redisService)){
    $redisUrl = $defaultUrl;
    $redisPort = $defaulPort;
    $redisPassword = $defaulPassword;
  }
  else {
    $redisUrl = $redisService->getValue('hostname');
    $redisPort = $redisService->getValue('port');
    $redisPassword = $redisService->getValue('password');
  }

  print "<p>RedisUrl: $redisUrl</p>";
  print "<p>RedisPort: $redisPort</p>";
  print "<p>RedisUrl: redacted</p>";

  # Establish Redis connection and authenticate
  $redis = new Redis();
  $redis->connect($redisUrl, $redisPort);
  $redis->auth($redisPassword);
  $info = $redis->info();
  print_r($info);
?>
</body>
</html>
