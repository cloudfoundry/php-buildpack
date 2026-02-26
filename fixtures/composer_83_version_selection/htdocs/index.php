<?php
// Regression test for https://github.com/cloudfoundry/php-buildpack/issues/1220
// Outputs the running PHP major.minor version so the integration test can assert
// that PHP 8.3 was selected, not the default 8.1.
echo 'PHP Version: ' . PHP_MAJOR_VERSION . '.' . PHP_MINOR_VERSION;
