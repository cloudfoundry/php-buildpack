<html>
 <head>
  <title>PHP Test</title>
 </head>
 <body>
<?php
echo '<p>Hello World!</p>';

$names = $_SERVER['QUERY_STRING'];
foreach (explode(",", $names) as $name) {
  if (extension_loaded($name)) {
    echo 'SUCCESS: ' . $name . ' loads.';
  }
  else {
    echo 'ERROR: ' . $name . ' failed to load.';
  }
}
?>
 </body>
</html>
