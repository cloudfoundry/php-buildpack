<?php
// Display include_path to verify @{HOME} placeholder replacement
echo "include_path: " . ini_get('include_path') . "\n";
echo "\n";
phpinfo();
?>
