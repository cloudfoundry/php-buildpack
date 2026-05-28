<?php
require '../lib/vendor/autoload.php';

// psr/log is a require-dev dependency.
// If COMPOSER_INSTALL_OPTIONS: ["--dev"] is honoured, this class exists.
if (interface_exists('Psr\Log\LoggerInterface')) {
    echo "dev dependencies installed";
} else {
    http_response_code(500);
    echo "dev dependencies missing";
}
