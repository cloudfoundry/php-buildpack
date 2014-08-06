## Composer

Yes!! We support [Composer]!

Usage of the build pack with Composer is consistent to usage without it, so most of the standard documentation still applies.  Where it does not, this document will fill in the Composer specific gaps.

 1. Usage of Composer requires a `composer.json` file.  This should be placed in the root of your application.

 1. You are not required to push a `composer.lock` file with your application, although I would strongly encourage you to do so.  It will ensure that a consistent set of dependencies are installed when you push to CloudFoundry.

 1. You can require dependencies to packages and extensions.  Extensions should be prefixed with the standard `ext-`.  If you reference an extension that is available to the build pack, it will automatically be installed.  See the main [README] for a list of supported extensions.

### Configuration

The build pack tries to run with a good set of default values for Composer.  If you'd like to adjust things further, you can do so by adding a `.bp-config/options.json` file to your application and setting any of the following values in it.

|      Variable     |   Explanation                                        |
------------------- | -----------------------------------------------------|
| COMPOSER_VERSION  | The version of Composer to use.  It defaults to the latest. |
| COMPOSER_INSTALL_OPTIONS | A list of options that should be passed to `composer install`.  This defaults to `--no-interaction --no-dev --no-progress`.  The `--no-progress` option must be used due to the way the build pack calls Composer. |


[Composer]:https://getcomposer.org
[README]:https://github.com/dmikusa-pivotal/cf-php-build-pack#features
