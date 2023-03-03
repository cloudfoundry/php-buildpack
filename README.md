# Cloud Foundry PHP Buildpack

[![CF Slack](https://www.google.com/s2/favicons?domain=www.slack.com) Join us on Slack](https://cloudfoundry.slack.com/messages/buildpacks/)

A buildpack to deploy PHP applications to Cloud Foundry based systems, such as a [cloud provider](https://www.cloudfoundry.org/learn/certified-providers/) or your own instance.

### Buildpack User Documentation

Official buildpack documentation can be found here: [php buildpack docs](http://docs.cloudfoundry.org/buildpacks/php/index.html).

### Building the Buildpack

#### Option 1: Using the `package.sh` script
1. Run `./scripts/package.sh [ --uncached | --cached ] [ --stack=STACK ]`

This requires that you have `docker` installed on your local machine, as it
will run packaging setup within a `ruby` image.

#### Option 2: Manually use the `buildpack-packager`
1. Make sure you have fetched submodules

   ```bash
   git submodule update --init
   ```

1. Check out a tagged release. It is not recommended to bundle buildpacks based on master or develop as these are moving targets.

   ```bash
   git checkout v4.4.2  # or whatever version you want, see releases page for available versions
   ```

1. Get latest buildpack dependencies, this will require having Ruby 3.0 or running in a Ruby 3.0 container image

   ```shell
   BUNDLE_GEMFILE=cf.Gemfile bundle
   ```

1. Build the buildpack. Please note that the PHP buildpack still uses the older Ruby based buildpack packager. This is different than most of the other buildpacks which use a newer Golang based buildpack packager. You must use the Ruby based buildpack packager with the PHP buildpack.

   ```shell
   BUNDLE_GEMFILE=cf.Gemfile bundle exec buildpack-packager [ --uncached | --cached ] [ --any-stack | --stack=STACK ]
   ```

1. Use in Cloud Foundry

    Upload the buildpack to your Cloud Foundry instance and optionally specify it by name

    ```bash
    cf create-buildpack custom_php_buildpack php_buildpack-cached-custom.zip 1
    cf push my_app -b custom_php_buildpack
    ```

### Contributing
Find our guidelines [here](https://github.com/cloudfoundry/php-buildpack/blob/develop/CONTRIBUTING.md).

### Integration Tests
Buildpacks use the [Cutlass](https://github.com/cloudfoundry/libbuildpack/tree/master/cutlass) framework for running integration tests.

To run integration tests, run the following command:

```
./scripts/integration.sh
```

### Unit Tests

To run unit tests, run the following command:

```bash
./scripts/unit
```

### Requirements
 1. [PyEnv] - This will allow you to easily install Python 2.6.6, which is the same version available through the staging environment of CloudFoundry.
 1. [virtualenv] & [pip] - The buildpack uses virtualenv and pip to setup the [required packages].  These are used by the unit test and not required by the buildpack itself.

### Setup
```bash
git clone https://github.com/cloudfoundry/php-buildpack
cd php-buildpack
python -V  # should report 2.6.6, if not fix PyEnv before creating the virtualenv
virtualenv `pwd`/env
. ./env/bin/activate
pip install -r requirements.txt
```

### Project Structure

The project is broken down into the following directories:

  - `bin` contains executable scripts, including `compile`, `release` and `detect`
  - `defaults` contains the default configuration
  - `docs` contains project documentation
  - `extensions` contains non-core extensions
  - `env` virtualenv environment
  - `lib` contains core extensions, helper code and the buildpack utils
  - `scripts` contains the Python scripts that run on compile, release and detect
  - `tests` contains test scripts and test data
  - `run_tests.sh` a convenience script for running the full suite of tests

### Understanding the Buildpack

The easiest way to understand the buildpack is to trace the flow of the scripts.  The buildpack system calls the `compile`, `release` and `detect` scripts provided by the buildpack.  These are located under the `bin` directory and are generic.  They simply redirect to the corresponding Python script under the `scripts` directory.

Of these, the `detect` and `release` scripts are straightforward, providing the minimal functionality required by a buildpack.  The `compile` script is more complicated but works like this.

  - load configuration
  - setup the `WEBDIR` directory
  - install the buildpack utils and the core extensions (HTTPD, Nginx & PHP)
  - install other extensions
  - install the `rewrite` and `start` scripts
  - setup the runtime environment and process manager
  - generate a startup.sh script

### Extensions

The buildpack relies heavily on extensions.  An extension is simply a set of Python methods that will get called at various times during the staging process.

Included non-core extensions:
- [`composer`](extensions/composer) - [Downloads, installs and runs Composer](http://docs.cloudfoundry.org/buildpacks/php/gsg-php-composer.html)
- [`dynatrace`](extensions/dynatrace) - Downloads and configures Dynatrace OneAgent
  - Looks for a bound service with name `dynatrace` and value `credentials` with sub-keys
    - `apiurl`
    - `environmentid`
    - `apitoken`
- [`newrelic`](extensions/newrelic) - [Downloads, installs and configures the NewRelic agent for PHP](http://docs.cloudfoundry.org/buildpacks/php/gsg-php-newrelic.html)
- [`sessions`](extensions/sessions) - [Configures PHP to store session information in a bound Redis or Memcached service instance](http://docs.cloudfoundry.org/buildpacks/php/gsg-php-sessions.html)

### Adding extensions

In general, you shouldn't need to modify the buildpack itself.  Instead creating your own extension should be the way to go.

To create an extension, simply create a folder.  The name of the folder will be the name of the extension.  Inside that folder, create a file called `extension.py`. That file will contain your code.  Inside that file, put your extension methods and any additional required code.

It's not necessary to fork the buildpack to add extensions for your app. The buildpack will notice and use extensions if you place them in a `.extensions` folder at your application root. See the [extensions directory in the this example](./fixtures/custom_extension/.extensions/phpmyadmin/extension.py) for a sample.

#### Methods

Here is an explanation of the methods offered to an extension developer.  All of them are optional and if a method is not implemented, it is simply skipped.

```python
def configure(ctx):
    pass
```

The `configure` method gives extension authors a chance to adjust the configuration of the buildpack prior to *any* extensions running.  The method is called very early on in the lifecycle of the buildpack, so keep this in mind when using this method.  The purpose of this method is to allow an extension author the opportunity to modify the configuration for PHP, the web server or another extension prior to those components being installed.  

An example of when to use this method would be to adjust the list of PHP extensions that are going to be installed.

The method takes one argument, which is the buildpack context.  You can edit the context to update the state of the buildpack.  Return value is ignore / not necessary.


```python
def preprocess_commands(ctx):
    return ()
```

The `preprocess_commands` method gives extension authors the ability to contribute a list of commands that should be run prior to the services.  These commands are run in the execution environment, not the staging environment and should execute and complete quickly.  The purpose of these commands is to give extension authors the chance to run any last-minute code to adjust to the environment.

As an example, this is used by the core extensions rewrite configuration files with information that is specific to the runtime environment.

The method takes the context as an argument and should return a tuple of tuples (i.e. list of commands to run).

```python
def service_commands(ctx):
    return {}
```

The `service_commands` method gives extension authors the ability to contribute a set of services that need to be run.  These commands are run and should continue to run.  If any service exits, the process manager will halt all of the other services and the application will be restarted by Cloud Foundry.

The method takes the context as an argument and should return a dictionary of services to run.  The key should be the service name and the value should be a tuple which is the command and arguments.

```python
def service_environment(ctx):
    return {}
```

The `service_environment` method gives extension authors the ability to contribute environment variables that will be set and available to the services.

The method takes the buildpack context as its argument and should return a dictionary of the environment variables to be added to the environment where services (see `service_commands`) are executed.  

The key should be the variable name and the value should be the value.  The value can either be a string, in which case the environment variable will be set with the value of the string or it can be a list.

If it's a list, the contents will be combined into a string and separated by the path separation character (i.e. ':' on Unix / Linux or ';' on Windows).  Keys that are set multiple times by the same or different extensions are automatically combined into one environment variable using the same path separation character.  This is helpful when two extensions both want to contribute to the same variable, for example LD_LIBRARY_PATH.

Please note that environment variables are not evaluated as they are set.  This would not work because they are set in the staging environment which is different than the execution environment.  This means you cannot do things like `PATH=$PATH:/new/path` or `NEWPATH=$HOME/some/path`.  To work around this, the buildpack will rewrite the environment variable file before it's processed.  This process will replace any `@<env-var>` markers with the value of the environment variable from the execution environment.  Thus if you do `PATH=@PATH:/new/path` or `NEWPATH=@HOME/some/path`, the service end up with a correctly set `PATH` or `NEWPATH`.

```python
def compile(install):
    return 0
```

The `compile` method is the main method and where extension authors should perform the bulk of their logic.  This method is called  by the buildpack while it's installing extensions.

The method is given one argument which is an Installer builder object.  The object can be used to install packages, configuration files or access the context (for examples of all this, see the core extensions like [HTTPD], [Nginx], [PHP], [Dynatrace] and [NewRelic]).  The method should return 0 when successful or any other number when it fails.  Optionally, the extension can raise an exception.  This will also signal a failure and it can provide more details about why something failed.

#### Method Order

It is sometimes useful to know what order the buildpack will use to call the methods in an extension.  They are called in the following order.

1. `configure`
2. `compile`
3. `service_environment`
4. `service_commands`
5. `preprocess_commands`

#### Example

Here is an example extension.  While technically correct, it doesn't actually do anything.

Here's the directory.

```bash
$ ls -lRh
total 0
drwxr-xr-x  3 daniel  staff   102B Mar  3 10:57 testextn

./testextn:
total 8
-rw-r--r--  1 daniel  staff   321B Mar  3 11:03 extension.py
```

Here's the code.

```python
import logging

_log = logging.getLogger('textextn')

# Extension Methods
def configure(ctx):
    pass

def preprocess_commands(ctx):
    return ()

def service_commands(ctx):
    return {}

def service_environment(ctx):
    return {}

def compile(install):
    return 0
```

#### Tips

 1. To be consistent with the rest of the buildpack, extensions should import and use the standard logging module.  This will allow extension output to be incorporated into the output for the rest of the buildpack.
 1. The buildpack will run every extension that is included with the buildpack and the application.  There is no mechanism to disable specific extensions.  Thus, when you write an extension, you should make some way for the user to enable / disable it's functionality.  See the [NewRelic] extension for an example of this.
 1. If an extension requires configuration, it should be included with the extension.  The `defaults/options.json` file is for the buildpack and its core extensions.  See the [NewRelic] buildpack for an example of this.
 1. Extensions should have their own test module.  This generally takes the form `tests/test_<extension_name>.py`.
 1. Run [bosh-lite].  It'll speed up testing and allow you to inspect the environment manually, if needed.
 1. Run a local web server for your binaries.  It'll seriously speed up download times.
 1. Test, test and test again.  Create unit and integration tests for your code and extensions.  This gives you quick and accurate feedback on your code.  It also makes it easier for you to make changes in the future and be confident that you're not breaking stuff.
 1. Check your code with flake8.  This linting tool can help to detect problems quickly.

[PyEnv]:https://github.com/yyuu/pyenv
[virtualenv]:http://www.virtualenv.org/en/latest/
[pip]:http://www.pip-installer.org/en/latest/
[required packages]:https://github.com/cloudfoundry/php-buildpack/blob/master/requirements.txt
[bosh-lite]:https://github.com/cloudfoundry/bosh-lite
[HTTPD]:https://github.com/cloudfoundry/php-buildpack/tree/master/lib/httpd
[Nginx]:https://github.com/cloudfoundry/php-buildpack/tree/master/lib/nginx
[PHP]:https://github.com/cloudfoundry/php-buildpack/tree/master/lib/php
[Dynatrace]:https://github.com/cloudfoundry/php-buildpack/tree/master/extensions/dynatrace
[NewRelic]:https://github.com/cloudfoundry/php-buildpack/tree/master/extensions/newrelic
[unit tests]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/development.md#testing

### Help and Support

Join the #buildpacks channel in our [Slack community](http://slack.cloudfoundry.org/) 

### Reporting Issues

This project is managed through GitHub.  If you encounter any issues, bug or problems with the buildpack please open an issue.

### Active Development

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
