<html>
<head>
<title>Redis Connection with phpiredis</title>
</head>
<body>
<h1>This page initiates a Redis connection and sets a variable to 10.</h1>
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

  # Establish Redis connection and authenticate
  $redis = phpiredis_connect($redisUrl, $redisPort);
  $response = phpiredis_command_bs($redis, array('AUTH', $redisPassword));

  # Set value of variable to 10
  $set_response = phpiredis_command_bs($redis, array('SET', 'variable', 10));
  $get_response = phpiredis_command_bs($redis, array('GET', 'variable'));

  echo "SET response was ";
  print_r($set_response);

  echo "<br/><br/><br/>";

  echo "Value of variable is currently ";
  print_r($get_response);
?>
</body>
</html>
