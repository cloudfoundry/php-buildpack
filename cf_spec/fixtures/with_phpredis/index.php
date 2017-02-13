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

  # Get Redis VCAP_SERVICES values
  $serviceManager = $cfHelper->getServiceManager();
  $redisService = $serviceManager->getService('.*redis.*');
  $redisUrl = $redisService->getValue('hostname');
  $redisPort = $redisService->getValue('port');
  $redisPassword = $redisService->getValue('password');

  # Establish Redis connection and authenticate
  $redis = new Redis();
  $redis->connect($redisUrl, $redisPort);
  $redis->auth($redisPassword);
  $info = $redis->info();
  print_r($info);
?>
</body>
</html>
