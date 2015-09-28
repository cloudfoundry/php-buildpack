## Configuration

This buildpack was built to be extremely flexible and configurable for the application developer.  This document describes the different options that are available to an application developer and when he or she might want to use them.

### Defaults

The buildpack stores all of its default configuration settings in the [defaults] directory.  This is a good place to look if you want to see how something is configured out-of-the-box.

## options.json

The `options.json` file is the configuration file for the buildpack itself.  This instructs the buildpack what to download, where to download it from and how to install it.  Additionally it allows you to configure package names and versions (i.e. PHP, HTTPD or Nginx versions), the web server to use (HTTPD, Nginx or None) and the PHP extensions that are enabled.

To configure these options for your application, simply create the file `.bp-config/options.json` in your project directory.  The buildpack will find this file when it runs and merge it with the default values that it uses.  Any values specified in your file will override the defaults.

Here are a list of the options that an application developer might want to override.

|      Variable     |   Explanation                                        |
------------------- | -----------------------------------------------------|
| WEB\_SERVER | Sets the web server to use.  Should be one of 'httpd', 'nginx' or 'none'.  This value defaults to 'httpd'. |
| HTTPD\_VERSION | Sets the version of Apache HTTPD to use. Currently the buildpack supports the latest stable version.  This value will default to the latest release that is supported by the buildpack. |
| ADMIN\_EMAIL | The value used in HTTPD's configuration for [ServerAdmin] |
| NGINX\_VERSION | Sets the version of Nginx to use.  Currently the buildpack supports the latest stable version.  This value will default to the latest release that is supported by the buildpack. |
| PHP\_55\_LATEST | Set by the buildpack, this provides the latest PHP 5.5.x release supported by the buildpack.  By setting PHP_VERSION to `{PHP_55_LATEST}`, your configuration will always use the latest PHP 5.5.x release. |
| PHP\_56\_LATEST | Set by the buildpack, this provides the latest PHP 5.6.x release supported by the buildpack.  By setting PHP_VERSION to `{PHP_56_LATEST}`, your configuration will always use the latest PHP 5.6.x release. |
| PHP\_70\_LATEST | Set by the buildpack, this provides the latest PHP 7.0.x release supported by the buildpack.  By setting PHP_VERSION to `{PHP_70_LATEST}`, your configuration will always use the latest PHP 7.0.x release. |
| PHP\_VERSION | Sets the version of PHP to use. |
| PHP\_EXTENSIONS | A list of the [extensions](#php-extensions) to enable. The [default](https://github.com/cloudfoundry/php-buildpack/blob/master/defaults/options.json#L35) is to enable "bz2", "zlib", "curl" and "mcrypt". |
| PHP\_MODULES | A list of the [modules](#php-modules) to enable.  The default is nothing.  The buildpack will automatically enable either the `fpm` or `cli` modules.  If you want to force this, you can set this list to contain `fpm`, `cli`, `cgi` and / or `pear`.  |
| ZEND\_EXTENSIONS | A list of the Zend extensions to enable.  The defaut is not to enable any. |
| APP\_START\_CMD | This option is used to instruct the buildpack what command to run if WEB_SERVER is set to `none` (i.e. it is a stand alone app).  By default, the buildpack will search for and run `app.php`, `main.php`, `run.php` or `start.php` (in that order).  This option can be the name of the script to run or the name plus arguments. |
| WEBDIR | Set a custom location for your web or public files.  This is the root directory from which the web server will host your files and the root directory from which PHP-FPM will look for your PHP files.  Defaults to `htdocs`.  Other common settings are `public`, `static` or `html`.  Path is relative to `/home/vcap/app`. |
| LIBDIR | Set a custom library directory.  This path is automatically added to the `include_path` by the buildpack.  Defaults to `lib`.  Path is relative to `/home/vcap/app`. |
| HTTP\_PROXY | Instruct the buildpack to use an HTTP proxy to download resources accessed via http. |
| HTTPS\_PROXY | Instruct the buildpack to use an HTTP proxy to download resources accessed via https. |
| ADDITIONAL\_PREPROCESS\_CMDS | A list of additional commands that should be run prior to the application.  This allows developers a way to run things like migration scripts prior to the application being run. |

For details about supported versions, please read the [release notes](https://github.com/cloudfoundry/php-buildpack/releases) for your buildpack version.



### HTTPD, Nginx and PHP configuration

The buildpack will automatically configure HTTPD, Nginx and PHP for your application.  In most situations this should just work, however if you need to adjust the configuration it can be done.  

The first step is to create a directory for the configuration files under the `.bp-config`.  The new directory's name should be one or more of the following: `httpd`, `nginx` or `php`.  Once created, simply add the configuration files to that directory.

Ex:  (to change HTTPD logging configuration)

```
$ ls -l .bp-config/httpd/extra/
total 8
-rw-r--r--  1 daniel  staff  396 Jan  3 08:31 httpd-logging.conf
```

In this example, we've created the `httpd` directory and added the `extra/httpd-logging.conf` file which matches the [extra/httpd-logging.conf] file is found in the buildpack [defaults].  With this configuration file in place, the buildpack will detect it and install it when the application is pushed to CF.  

By installing it, the buildpack will override the default file of the same name.  This means that the settings in the default file will no longer be applied, unless the application specific file also contains them as well.  In fact, it's a good idea to take the default file from the buildpack, use it as a starting point and edit as necessary.  This will make it easier to edit the file without breaking the overall configuration.

A couple further notes.  First, you are not limited to including configuration files that exist in the buildpack default configuration.  You can include files that only exist in the application, however the buildpack will not know about these.  Thus you'll need to adjust the configuration to take the new files into consideration.

Second, you need to take care when adjusting the configurations.  It is possible for you to break the buildpack's configuration and thus cause your application to fail.  If you've included custom configuration, be sure to double check it if your application stops working.

### PHP Extensions

As mentioned in the chart above, PHP extensions can easily be enabled by setting the `PHP_EXTENSIONS` or `ZEND_EXTENSIONS` option in `.bp-config/options.json`.  This option allows you to make sure that any of the bundled PHP extensions are installed and configured for your environment. The list of bundled php extensions is available in the [manifest.yml](https://github.com/cloudfoundry/php-buildpack/blob/master/manifest.yml#L65).

Alternatively, PHP extensions can also be enabled through [standard portable composer syntax](docs/composer.md).

#### Composer

The PHP Buildpack also has support for using composer files within your PHP application. By default, it will utilize composer files (json, lock) that reside inside the app root directory or the directory specified as `WEBDIR` in your `options.json`. In the event that you have your composer files inside your app directory but not in the default directories, you can specify this custom location via an environment variable for your app called `COMPOSER_PATH` (relative to the app root directory). Please note that your composer lock and json files must be in the same directory.

See [full composer support details](docs/composer.md).

### PHP Modules

In addition to extensions, there are a few PHP modules that can be installed.  These are parts of the traditional PHP install that have been split out into their own download to decrease the size of the binaries used by the buildpack by default.  If you need one of these you can manually install the module by adding it to the `PHP_MODULES` list.

The list of available modules includes `cli`, `fpm`, `cgi` and `pear`.  The first one, `cli`, will install the `php` and `phar` binaries, the second, `fpm`, will install the PHP-FPM binary, the third, `cgi`, will install the `php-cgi` binary and the fourth, `pear`, will install PHP's Pear script and associated libraries.  

In most cases, manually selecting one of these four special modules is not necessary.  For example, the buildpack will install the `cli` module when you push a stand alone application and it will install the `fpm` module when you run a web application.  Currently the buildpack will not install the `cgi` module or `pear`.  If you need one of these, you'll have to instruct the buildpack to install it.

## Extensions

The behavior of the buildpack can be controlled with extensions.  Out-of-the-box the buildpack includes some of it's own extensions like for [HTTPD], [Nginx], [PHP] and [NewRelic].  These are core extensions and will be automatically included by the buildpack and used as necessary.  In addition to these, it's possible for an application developer to include his or her own custom extensions.  These should be placed into the `.extensions` directory of your project folder.  When pushed, the buildpack will look in this location for application specific extensions and run them.

The [Development Documentation] explains how to write extensions.


[defaults]:https://github.com/cloudfoundry/php-buildpack/tree/master/defaults
[ServerAdmin]:http://httpd.apache.org/docs/2.4/mod/core.html#serveradmin
[extra/httpd-logging.conf]:https://github.com/cloudfoundry/php-buildpack/blob/master/defaults/config/httpd/extra/httpd-logging.conf
[Development Documentation]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/development.md
[HTTPD]:https://github.com/cloudfoundry/php-buildpack/tree/master/lib/httpd
[Nginx]:https://github.com/cloudfoundry/php-buildpack/tree/master/lib/nginx
[PHP]:https://github.com/cloudfoundry/php-buildpack/tree/master/lib/php
[NewRelic]:https://github.com/cloudfoundry/php-buildpack/tree/master/extensions/newrelic
