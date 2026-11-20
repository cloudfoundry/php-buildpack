<?php
echo "<h1>PHP Extensions Test</h1>";
echo "<h2>PHP Version: " . phpversion() . "</h2>";

$required_extensions = ['apcu'];

echo "<h3>Required Extensions Status:</h3>";
echo "<ul>";
foreach ($required_extensions as $ext) {
    $loaded = extension_loaded($ext);
    $status = $loaded ? '✓ LOADED' : '✗ NOT LOADED';
    echo "<li><strong>$ext:</strong> $status</li>";
}
echo "</ul>";

echo "<h3>All Loaded Extensions:</h3>";
echo "<ul>";
foreach (get_loaded_extensions() as $ext) {
    echo "<li>$ext</li>";
}
echo "</ul>";
?>
