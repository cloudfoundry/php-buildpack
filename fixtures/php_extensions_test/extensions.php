<?php
header('Content-Type: text/plain');

echo "Loaded Extensions:\n";
echo "=================\n\n";

$extensions = get_loaded_extensions();
sort($extensions);

foreach ($extensions as $ext) {
    echo "- " . $ext . "\n";
}

echo "\nExtension Directory:\n";
echo "===================\n";
echo ini_get('extension_dir') . "\n";

echo "\nChecking specific extensions:\n";
echo "============================\n";
echo "bz2: " . (extension_loaded('bz2') ? 'YES' : 'NO') . "\n";
echo "curl: " . (extension_loaded('curl') ? 'YES' : 'NO') . "\n";
echo "zlib: " . (extension_loaded('zlib') ? 'YES' : 'NO') . "\n";
