    ✓ This is a functional buildpack, and ready-to-use! Use:
    cf push "Your App" -b https://github.com/fishfin/php-buildpack
    ----
    And you might just find it useful, that even PDO is supported now!


## Cloud Foundry PHP Buildpack with pre-integrated extensions for IBM Relational Databases
This buildpack is a fork of [https://github.com/cloudfoundry/php-buildpack](https://github.com/cloudfoundry/php-buildpack), v4.3.33, last updated on 31-May-2017. It automatically copies the correct versions of `ibm_db2.so` and `pdo_ibm.so` to the PHP Extensions directory, and IBM CLI Drivers to BP_DIR/ibm\_clidrivers.

The buildpack currently supports the following PHP versions: `5.6.29`, `5.6.30`, `7.0.17`, `7.0.18`, `7.1.3` and `7.1.4`.

In `manifest.yml`, the default version is set as `5.6.30`. To change the PHP version to use, in your application root directory, edit `composer.json` file and add `require` directive for PHP:
```
{
    "require": {
        "php": "7.0.18"
    }
}
```
Here, PHP 7.0.18 is selected. Now push your app. php.ini is automatically edited by the script and `extension=ibm_db2.so` and `extension=pdo_ibm.so` are added, so you do not need to do anything additional to enable the extensions.
