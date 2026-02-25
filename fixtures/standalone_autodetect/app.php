<?php
// Auto-detected standalone app (app.php has highest priority)
echo "Auto-detected app.php\n";
echo "PHP Version: " . phpversion() . "\n";

// Create marker to verify correct file was detected
file_put_contents(getenv('HOME') . '/autodetect_result.txt', "app.php\n");

echo "Auto-detection test: SUCCESS\n";
exit(0);
