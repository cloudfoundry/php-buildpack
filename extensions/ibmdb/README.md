    ✓ This is a functional buildpack, and ready-to-use! Use:
    cf push "Your App" -b https://github.com/fishfin/php-buildpack


## Cloud Foundry PHP Buildpack with pre-integrated extensions for IBM Relational Databases
This buildpack is a fork of [https://github.com/cloudfoundry/php-buildpack](https://github.com/cloudfoundry/php-buildpack), v4.3.24, last updated on 18-Dec-2016. It automatically copies the correct version of `ibm_db2.so` file to the PHP Extensions directory, and IBM CLI Drivers to BP_DIR/ibm\_clidrivers.

The buildpack currently supports the following PHP versions: `5.5.37`, `5.5.38`, `5.6.28`, `5.6.29`, `7.0.13` and `7.0.14`.

In `manifest.yml`, the default version is set as `5.5.38`. To change the PHP version to use, in your application root directory, edit `composer.json` file and add `require` directive for PHP:
```
{
    "require": {
        "php": "7.0.14"
    }
}
```
Here, PHP 7.0.14 is selected. Now push your app. php.ini is automatically edited by the script and extension=ibm_db2.so is added, so you do not need to do anything additional to enable the extension.
