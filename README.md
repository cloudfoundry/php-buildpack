## Cloud Foundry PHP Buildpack

A buildpack to deploy PHP applications to Cloud Foundry based systems, such as a [cloud provider](https://www.cloudfoundry.org/learn/certified-providers/) or your own instance.

## 30 Second Tutorial

Getting started with this buildpack is easy.  With the [`cf` command line utility](https://github.com/cloudfoundry/cli) installed, open a shell, change directories to the root of your PHP files and push your application using the argument `-b https://github.com/cloudfoundry/php-buildpack.git`.

Example:

```bash
mkdir my-php-app
cd my-php-app
cat << EOF > index.php
<?php
  phpinfo();
?>
EOF
cf push -m 128M -b https://github.com/cloudfoundry/php-buildpack.git my-php-app
```

Please note that you should change *my-php-app* to some unique name on your target Cloud Foundry instance, otherwise you'll get a hostname conflict error and the push will fail.

The example above will create and push a test application, *my-php-app*, to Cloud Foundry.  The `-b` argument instructs CF to use this buildpack.  The remainder of the options and arguments are not specific to the buildpack, for questions on those consult the output of `cf help push`.

Here's a breakdown of what happens when you run the example above.

  - On your PC:
    - It will create a new directory and one PHP file, which just invokes `phpinfo()`
    - Run `cf` to push your application.  This will create a new application with a memory limit of 128M (more than enough here) and upload our test file.
  - Within Cloud Foundry:
    - The buildpack is executed.
    - Application files are copied to the `htdocs` folder.
    - Apache HTTPD & PHP are downloaded, configured with the buildpack defaults and run.
    - Your application is accessible at the URL `http://my-php-app.example.com` (Replacing `example.com` with the domain of your public CF provider or private instance).

## More Information

While the *30 Second Tutorial* shows how quick and easy it is to get started using the buildpack, it skips over quite a bit of what you can do to adjust, configure and extend the buildpack.  The following sections and links provide a more in-depth look at the buildpack.

  - [Supported Software](#supported-software)
  - [Features](#features)
  - [Example Applications](#examples)
  - [Usage]
  - [Configuration Options]
  - [Composer support]
  - [Binaries]
  - [Troubleshooting]
  - [Getting Help](#getting-help)
  - [Development]
  - [License](#license)
  - [Building](#building)
  - [Contributing](./CONTRIBUTING.md)

## Supported Software
The [release notes page](https://github.com/cloudfoundry/php-buildpack/releases) has a list of currently supported modules and packages.

* **PHP Runtimes**
  * php-cli
  * php-cgi
  * php-fpm
* **Third-Party Modules**
  * New Relic, in connected environments only.



## Features

Here are some special features of the buildpack.

  - Supports running commands or migration scripts prior to application startup.
  - Supports an extension mechanism that allows the buildpack to provide additional functionality.
  - Allows for application developers to provide custom extensions.
  - Easy troubleshooting with the `BP_DEBUG` environment variable.
  - Download location is configurable, allowing users to host binaries on the same network (i.e. run without an Internet connection)
  - Smart session storage, defaults to file w/sticky sessions but can also use redis for storage.

## Examples

Here are some example applications that can be used with this buildpack.

  - [php-info]  This app has a basic index page and shows the output of `phpinfo()`.
  - [PHPMyAdmin]  A deployment of PHPMyAdmin that uses bound MySQL services.
  - [PHPPgAdmin] A deployment of PHPPgAdmin that uses bound PostgreSQL services.
  - [Wordpress]  A deployment of WordPress that uses bound MySQL service.
  - [Drupal] A deployment of Drupal that uses bound MySQL service.
  - [CodeIgniter]  CodeIgniter tutorial application running on CF.
  - [Stand Alone]  An example which runs a standalone PHP script.
  - [pgbouncer]  An example which runs the PgBouncer process in the container to pool database connections.
  - [phalcon]  An example which runs a Phalcon based application.
  - [composer] An example which uses Composer.

## Getting Help

If you have questions, comments or need further help with the buildpack you can post to the [cf-dev](https://lists.cloudfoundry.org/archives/) mailing list. It's a good place for posting question on all of the open source Cloud Foundry components, like this buildpack.

If you are using one of the [many CF providers](https://www.cloudfoundry.org/learn/certified-providers/), please use their support channels.
## License

The Cloud Foundry PHP Buildpack is released under version 2.0 of the [Apache License].

## Building

1. Make sure you have fetched submodules

  ```bash
  git submodule update --init
  ```

1. Get latest buildpack dependencies

  ```shell
  BUNDLE_GEMFILE=cf.Gemfile bundle
  ```

1. Build the buildpack

  ```shell
  BUNDLE_GEMFILE=cf.Gemfile bundle exec buildpack-packager [ --uncached | --cached ]
  ```

1. Use in Cloud Foundry

    Upload the buildpack to your Cloud Foundry instance and optionally specify it by name

    ```bash
    cf create-buildpack custom_php_buildpack php_buildpack-cached-custom.zip 1
    cf push my_app -b custom_php_buildpack
    ```

## Supported binary dependencies

The buildpack only supports the stable patches for each dependency listed in the [manifest.yml](manifest.yml) and [releases page](https://github.com/cloudfoundry/php-buildpack/releases).


If you try to use a binary that is not currently supported, staging your app will fail and you will see the following error message:

```
       Could not get translated url, exited with: DEPENDENCY_MISSING_IN_MANIFEST: ...
 !
 !     exit
 !
Staging failed: Buildpack compilation step failed
```

## Testing
Buildpacks use the [Machete](https://github.com/cloudfoundry/machete) framework for running integration tests.

To test a buildpack, run the following command from the buildpack's directory:

```
BUNDLE_GEMFILE=cf.Gemfile bundle exec buildpack-build
```

More options can be found on Machete's [Github page.](https://github.com/cloudfoundry/machete)


## Contributing

Find our guidelines [here](./CONTRIBUTING.md).

## Help and Support

Join the #buildpacks channel in our [Slack community] (http://slack.cloudfoundry.org/) 

### Reporting Issues

This project is managed through GitHub.  If you encounter any issues, bug or problems with the buildpack please open an issue.

The project backlog is on [Pivotal Tracker](https://www.pivotaltracker.com/projects/1042066)

[Configuration Options]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/config.md
[Development]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/development.md
[Troubleshooting]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/troubleshooting.md
[Usage]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/usage.md
[Binaries]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/binaries.md
[php-info]:https://github.com/dmikusa-pivotal/cf-ex-php-info
[PHPMyAdmin]:https://github.com/dmikusa-pivotal/cf-ex-phpmyadmin
[PHPPgAdmin]:https://github.com/dmikusa-pivotal/cf-ex-phppgadmin
[Wordpress]:https://github.com/dmikusa-pivotal/cf-ex-worpress
[Drupal]:https://github.com/dmikusa-pivotal/cf-ex-drupal
[CodeIgniter]:https://github.com/dmikusa-pivotal/cf-ex-code-igniter
[Stand Alone]:https://github.com/dmikusa-pivotal/cf-ex-stand-alone
[pgbouncer]:https://github.com/dmikusa-pivotal/cf-ex-pgbouncer
[Apache License]:http://www.apache.org/licenses/LICENSE-2.0
[vcap-dev]:https://groups.google.com/a/cloudfoundry.org/forum/#!forum/vcap-dev
[support forums]:http://support.run.pivotal.io/home
[Composer support]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/composer.md
["offline" mode]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/binaries.md#bundling-binaries-with-the-build-pack
[phalcon]:https://github.com/dmikusa-pivotal/cf-ex-phalcon
[Phalcon]:http://phalconphp.com/en/
[composer]:https://github.com/dmikusa-pivotal/cf-ex-composer
