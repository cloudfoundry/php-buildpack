## Composer

Yes! We support [Composer]!

Usage of the buildpack with Composer is consistent to usage without it, so most of the standard documentation still applies.  Where it does not, this document will fill in the Composer specific gaps.

 1. Usage of Composer requires a `composer.json` file.  This should be placed in the root of your application.

 1. You are not required to push a `composer.lock` file with your application, although I would strongly encourage you to do so.  It will ensure that a consistent set of dependencies are installed when you push to Cloud Foundry.

 1. You can require dependencies to packages and extensions.  Extensions should be prefixed with the standard `ext-`.  If you reference an extension that is available to the buildpack, it will automatically be installed.  See the main [README] for a list of supported extensions.

 1. If you set the version of PHP to use in your `composer.json` (require -> php) or `composer.lock` (platform -> php) file, the buildpack will take the version and install it.  This will override the version information you set in the `options.json` file.

The following format is supported for PHP version numbers.  This is a small subset of the format supported by Composer.

|   Example   |  Expected Version                 |
------------- | ----------------------------------|
|   5.5.*     |  latest 5.5.x release |
|   >=5.5     |  latest 5.5.x release |
|   5.5.x     |  specific 5.5.x release that is listed |

### Configuration

The buildpack tries to run with a good set of default values for Composer.  If you'd like to adjust things further, you can do so by adding a `.bp-config/options.json` file to your application and setting any of the following values in it.

|      Variable     |   Explanation                                        |
------------------- | -----------------------------------------------------|
| COMPOSER_VERSION  | The version of Composer to use.  It defaults to the latest. |
| COMPOSER_INSTALL_OPTIONS | A list of options that should be passed to `composer install`.  This defaults to `--no-interaction --no-dev --no-progress`.  The `--no-progress` option must be used due to the way the buildpack calls Composer. |
| COMPOSER_VENDOR_DIR | Allows you to override the default value used by the buildpack.  This is passed through to Composer and instructs it where to create the `vendor` directory.  Defaults to `{BUILD_DIR}/{LIBDIR}/vendor`. |
| COMPOSER_BIN_DIR | Allows you to override the default value used by the buildpack.  This is passed through to Composer and instructs it where to place executables from packages.  Defaults to `{BUILD_DIR}/php/bin`. |
| COMPOSER_CACHE_DIR | Allows you to override the default value used by the buildpack.  This is passed through to Composer and instructs it where to place its cache files.  Generally you should not change this value.  The default is `{CACHE_DIR}/composer` which is a sub directory of the cache folder passed into the buildpack (meaning that Composer cache files will be restored on subsequent application pushes. |

### GitHub API Request Limits

Composer uses GitHub's API to retrieve zip files for installation into the application folder. If you do not vendor dependencies before pushing an app, Composer will fetch dependencies at staging time using the GitHub API.

GitHub's API is request-limited. Once you have reached your hourly allowance of API requests (typically, 60), GitHub's API will begin to return 403 errors and staging will fail.

To avoid this situation, there are two alternatives.

1. Vendor dependencies before pushing your application.
2. Supply a GitHub OAuth API token.

#### Vendoring Dependencies

To vendor dependencies, you will need to run `composer install` before you push your application. You may also need to configure `COMPOSER_VENDOR_DIR` to "vendor".

#### Supply a GitHub Token

Composer can use [GitHub API OAuth tokens](https://help.github.com/articles/creating-an-access-token-for-command-line-use/) to greatly increase your hourly request limit (typically to 5000).

During staging, the buildpack looks for this token in the environment variable `COMPOSER_GITHUB_OAUTH_TOKEN`. If you supply a valid token, Composer will use it during staging. This mechanism will not work if the token is invalid.

To supply the token, you can either use `cf set-env <your-app-name> COMPOSER_GITHUB_OAUTH_TOKEN "<oauth-token-value>"`, or you can add it to the `env:` block of your application manifest.

### Staging Environment

Composer runs in the buildpack staging environment. Variables that have been set with `cf set-env` or with [a `manifest.yml env:` block](http://docs.cloudfoundry.org/devguide/deploy-apps/manifest.html#env-block) will be visible to Composer (including `COMPOSER_GITHUB_OAUTH_TOKEN`).

For example:

    $ cf push a_symfony_app --no-start
    $ cf set-env a_symfony_app SYMFONY_ENV "prod"
    $ cf start a_symfony_app

In this example, `a_symfony_app` will be supplied with an environment variable, `SYMFONY_ENV`, that will be visible to Composer and any scripts started by Composer.

#### Non-configurable Environment Variables

There are two special variables that cannot be configured: `LD_LIBRARY_PATH` and `PHPRC`. This is because these variables have different values at staging time and run time, but any variable set by a user is injected into both environments.

[Composer]:https://getcomposer.org
[README]:https://github.com/cloudfoundry/php-buildpack#features
