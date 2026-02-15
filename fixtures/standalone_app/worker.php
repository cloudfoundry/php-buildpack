<?php
// Standalone PHP worker application for testing APP_START_CMD
// This simulates a background worker or queue processor

echo "Standalone PHP Worker Started\n";
echo "PHP Version: " . phpversion() . "\n";
echo "Working Directory: " . getcwd() . "\n";
echo "Script: " . __FILE__ . "\n";

// Create a marker file to verify the worker ran
$markerFile = getenv('HOME') . '/worker_ran.txt';
file_put_contents($markerFile, "WORKER_EXECUTED\n");
echo "Created marker file: $markerFile\n";

// Simulate worker loop (in real app this would process queue items)
$counter = 0;
$maxIterations = 5;

while ($counter < $maxIterations) {
    $counter++;
    echo "Worker iteration: $counter/$maxIterations\n";
    
    // Write status to file for test verification
    $statusFile = getenv('HOME') . '/worker_status.txt';
    file_put_contents($statusFile, "ITERATION_$counter\n", FILE_APPEND);
    
    sleep(1);
}

echo "Worker completed successfully\n";
exit(0);
