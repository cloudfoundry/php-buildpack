## Cloud Foundry PHP Buildpack
[![CF Slack](https://s3.amazonaws.com/buildpacks-assets/buildpacks-slack.svg)](http://slack.cloudfoundry.org)

A buildpack to deploy PHP applications to Cloud Foundry based systems, such as a [cloud provider](https://www.cloudfoundry.org/learn/certified-providers/) or your own instance.

## Using the Buildpack

For information on deploying PHP applications visit [CloudFoundry.org](http://docs.cloudfoundry.org/buildpacks/php/index.html).

# Building the Buildpack

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

## Active Development

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
[Proxy Support]:http://docs.cloudfoundry.org/buildpacks/proxy-usage.html

