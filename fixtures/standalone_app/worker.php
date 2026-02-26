<?php
// Standalone PHP worker application for testing APP_START_CMD
echo "Standalone PHP Worker Started\n";
echo "PHP Version: " . phpversion() . "\n";

// Keep process running so CF health check passes before cleanup
while (true) {
    sleep(60);
}
