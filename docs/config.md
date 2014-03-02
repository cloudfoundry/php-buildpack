## Configuration

This build pack was built to be extremely flexible and configurable for an application developer.  This document describes the different options that are available to an application developer and when he or she might want to use them.

### Defaults

The build pack stores all of its default configuration settings in the [defaults] directory.  This is a good place to look if you want to see how something is configured out-of-the-box.

## options.json

The `options.json` file is the configuration file for the build pack itself.  This instructs the build pack what to download, where to download it from and how to install it.  Additionally it allows you to configure package names and versions (i.e. PHP, HTTPD or Nginx versions), the web server to use (HTTPD or Nginx) and the PHP extensions that are enabled.

To configure these options for your applicaton, simply create the file `.bp-config/options.json` in your project directory.  The build pack will find this file when it runs and merge it with the default values that it uses.  Any values specified in your file will override the defaults.

Here are a list of the options that an application developer might want to override.

|      Variable     |   Explanation                                        |
------------------- | -----------------------------------------------------|
| WEB_SERVER | Sets the web server to use.  Should be either 'httpd' or 'nginx'.  This value defaults to 'httpd'. |
| HTTPD_VERSION | Sets the version of Apache HTTPD to use. Currently the build pack supports the 2.4.x branch.  This value will default to the latest release that is supported by the build pack. |
| ADMIN_EMAIL | The value used in HTTPD's configuration for [ServerAdmin] |
| NGINX_VERSION | Sets the version of Nginx to use.  Currently the build pack supports the 1.5.x branch.  This value will default to the latest release that is supported by the build pack. |
| PHP_VERSION | Sets the version of PHP to use.  Currently the build pack supports the 5.4.x and 5.5.x branches.  This value will default to the latest release of the 5.4.x branch. |
| PHP_54_LATEST | Set by the build pack, this provides the latest PHP 5.4.x release supported by the build pack.  By setting PHP_VERSION to `{PHP_54_LATEST}`, your configuration will always use the latest PHP 5.4.x release. |
| PHP_55_LATEST | Set by the build pack, this provides the latest PHP 5.5.x release supported by the build pack.  By setting PHP_VERSION to `{PHP_55_LATEST}`, your configuration will always use the latest PHP 5.5.x release. |
| PHP_EXTENSIONS | A list of the extensions to enable.  The default is to enable "bz2", "zlib", "curl" and "mcrypt". |
| ZEND_EXTENSIONS | A list of the Zend extensions to enable.  The defaut is not to enable any. |
| DOWNLOAD_URL | This is the base of the URL that the build pack uses to locate its binary files.  The default points to the location of the build pack's binary files.  If you want to provide your own binaries, you can point this URL at the repository that holds your custom binaries.  This should be an HTTP or HTTPS URL. |

### HTTPD, Nginx and PHP configuration

The build pack will automatically configure HTTPD, Nginx and PHP for your application.  In most situations this should just work, however if you need to adjust the configuration it can be done.  

The first step is to create a directory for the configuration files under the `.bp-config`.  The new directory's name should be one or more of the following: `httpd`, `nginx` or `php.  Once created, simply add the configuration files to that directory.

Ex:  (to change HTTPD logging configuration)

```
$ ls -l .bp-config/httpd/extra/
total 8
-rw-r--r--  1 daniel  staff  396 Jan  3 08:31 httpd-logging.conf
```

In this example, we've created the `httpd` directory and added the `extra/httpd-logging.conf` file which matches the [extra/httpd-logging.conf] file is found in the build pack [defaults].  With this configuration file in place, the build pack will detect it and install it when the application is pushed to CF.  

By installing it, the build pack will override the default file of the same name.  This means that the settings in the default file will no longer be applied, unless the application specific file also contains them as well.  In fact, it's a good idea to take the default file from the build pack, use it as a starting point and edit as necessary.  This will make it easier to edit the file without breaking the overall configuration.

A couple further notes.  First, you are not limited to including configuration files that exist in the build pack default configuration.  You can include files that only exist in the application, however the build pack will not know about these.  Thus you'll need to adjust the configuration to take the new files into consideration.

Second, you need to take care when adjusting the configurations.  It is possible for you to break the build pack's configuration and thus cause your application to fail.  If you've included custom configuration, be sure to double check it if your application stops working.

## Extensions

The behavior of the build pack can be controlled with extensions.  Out-of-the-box the build pack includes some of it's own extensions like for HTTP, Nginx, PHP and NewRelic.  In addition to these, it's possible for an application developer to include his own custom extensions.  These should be placed into the `.extensions` directory of your project folder.  When pushed, the build pack will look in this location for application specific extensions and run them.

The [Development Documentation] explains how to write extensions.


[defaults]:https://github.com/dmikusa-pivotal/cf-php-build-pack/tree/master/defaults
[ServerAdmin]:http://httpd.apache.org/docs/2.4/mod/core.html#serveradmin
[extra/httpd-logging.conf]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/defaults/config/httpd/2.4.x/extra/httpd-logging.conf
[Development Documentation]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/development.md

