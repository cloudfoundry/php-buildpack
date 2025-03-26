<!DOCTYPE html>
<html>
  <head>
    <title>Powered By Cloud Foundry</title>
  </head>
  <body>
<?php
  // https://getcomposer.org/doc/01-basic-usage.md#autoloading
  // This is how you autoload composer packages
  
  require '../lib/vendor/autoload.php';

  $dotenv = Dotenv\Dotenv::createImmutable(__DIR__);
  $dotenv->load();
  $projectName = $_ENV['PROJECT_NAME'];
  echo "<p style='text-align: center'>Powered By " . $projectName . " Buildpacks</p>"
?>
  </body>
</html>
