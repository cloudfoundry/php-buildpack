## Default Configuration

This build pack was build to be extremely flexible and configurable for an application developer.  This document describes the different options that are available to an application developer and when he or she might want to use them.

The build pack stores all of its default configuration settings in the [defaults] directory.  This is a good place to look if you want to see how something is configured out-of-the-box.

## options.json

The `options.json` file is the configuration file for the build pack itself.  This instructs the build pack what to download, where to download it from and how to install it.  Additionally it allows you to configure package names and versions (i.e. PHP, HTTPD or Nginx versions), the web server (HTTPD or Nginx) and the PHP extensions that are enabled.

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

## HTTPD, Nginx and PHP configuration

Explain how to override / configure this.

## Extensions

Explain how to use extensions and override default configuration.


[defaults]:https://github.com/dmikusa-pivotal/cf-php-build-pack/tree/master/defaults
[ServerAdmin]:http://httpd.apache.org/docs/2.4/mod/core.html#serveradmin

