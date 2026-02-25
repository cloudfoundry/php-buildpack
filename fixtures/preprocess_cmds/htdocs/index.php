<?php
// Test fixture for ADDITIONAL_PREPROCESS_CMDS
// The preprocess commands run via .profile.d with $HOME=/home/vcap (v4.x compatible)

echo "ADDITIONAL_PREPROCESS_CMDS Test\n";
echo "================================\n\n";

// Test 1: Check that preprocess file was created at $HOME/preprocess_ran.txt
// This verifies that $HOME was correctly set to /home/vcap during preprocess
$preprocess_file = '/home/vcap/preprocess_ran.txt';

if (file_exists($preprocess_file)) {
    $content = file_get_contents($preprocess_file);
    echo "Preprocess file found!\n";
    echo "Location: $preprocess_file\n";
    echo "Content:\n";
    echo $content;
    
    // Test 2: Check for expected markers (verifies commands executed)
    if (strpos($content, 'PREPROCESS_MARKER_1') !== false) {
        echo "\nMARKER_1_FOUND: YES\n";
    } else {
        echo "\nMARKER_1_FOUND: NO\n";
    }
    
    if (strpos($content, 'PREPROCESS_MARKER_2') !== false) {
        echo "MARKER_2_FOUND: YES\n";
    } else {
        echo "MARKER_2_FOUND: NO\n";
    }
    
    // Test 3: Verify execution order (MARKER_1 should appear before MARKER_2)
    $pos1 = strpos($content, 'PREPROCESS_MARKER_1');
    $pos2 = strpos($content, 'PREPROCESS_MARKER_2');
    if ($pos1 !== false && $pos2 !== false && $pos1 < $pos2) {
        echo "EXECUTION_ORDER: CORRECT\n";
    } else {
        echo "EXECUTION_ORDER: INCORRECT\n";
    }
} else {
    echo "ERROR: Preprocess file NOT found at: $preprocess_file\n";
    echo "PREPROCESS_COMMANDS_RAN: NO\n";
}

// Test 4: Verify $HOME was restored after preprocess commands
// At runtime (PHP-FPM), $HOME should be back to /home/vcap/app or /home/vcap
$runtime_home = getenv('HOME');
echo "\nHOME_RESTORED: ";
if ($runtime_home === '/home/vcap' || $runtime_home === '/home/vcap/app') {
    echo "YES ($runtime_home)\n";
} else {
    echo "NO (unexpected: $runtime_home)\n";
}

// Test 5: Verify $HOME variable was properly rewritten in preprocess commands
// The commands use $HOME which should resolve to /home/vcap during preprocess
$home_marker_file = '/home/vcap/home_var_test.txt';
if (file_exists($home_marker_file)) {
    $home_content = trim(file_get_contents($home_marker_file));
    echo "HOME_VAR_REWRITTEN: ";
    if ($home_content === '/home/vcap') {
        echo "YES (was $home_content during preprocess)\n";
    } else {
        echo "NO (was $home_content, expected /home/vcap)\n";
    }
} else {
    echo "HOME_VAR_REWRITTEN: SKIPPED (no home_var_test.txt)\n";
}
?>
