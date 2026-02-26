<?php
// Auto-detected standalone app (app.php has highest priority)
echo "Auto-detected app.php\n";
echo "PHP Version: " . phpversion() . "\n";
echo "Auto-detection test: SUCCESS\n";

// Keep process running so CF health check passes before cleanup
while (true) {
    sleep(60);
}
