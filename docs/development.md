## Development

This page aims to provide some help should you want to modify or extend the buildpack.

### Setup

To get setup developing the buildpack, you'll need some tools.  Here's the setup that should work.

 1. [PyEnv] - This will allow you to easily install Python 2.6.6, which is the same version available through the staging environment of CloudFoundry.
 1. [virtualenv] & [pip] - The buildpack uses virtualenv and pip to setup the [required packages].  These are used by the unit test and not required by the buildpack itself.

With those tools installed, you should be able to run these commands to get up and running.

```bash
git clone https://github.com/cloudfoundry/php-buildpack
cd php-buildpack
python -V  # should report 2.6.6, if not fix PyEnv before creating the virtualenv
virtualenv `pwd`/env
. ./env/bin/activate
pip install -r requirements.txt
```

That's it.  You should now be able to run the [unit tests].  Go ahead and do that now (try the `run_tests.sh` script), and if they all pass and you're all set.

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

In general, you shouldn't need to modify the buildpack itself.  Instead creating an extension should be the way to go.

### Extensions

The buildpack relies heavily on extensions.  An extension is simply a set of Python methods that will get called at various times during the staging process.  

#### Creation

To create an extension, simply create a folder.  The name of the folder will be the extension.  Inside that folder, create a file called `extension.py`. That file will contain your code.  Inside that file, put your extension methods and any additional required code.

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

The method is given one argument which is an Installer builder object.  The object can be used to install packages, configuration files or access the context (for examples of all this, see the core extensions like [HTTPD], [Nginx], [PHP] and [NewRelic]).  The method should return 0 when successful or any other number when it fails.  Optionally, the extension can raise an exception.  This will also signal a failure and it can provide more details about why something failed.

##### Method Order

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

  - To be consistent with the rest of the buildpack, extensions should import and use the standard logging module.  This will allow extension output to be incorporated into the output for the rest of the buildpack.
  - The buildpack will run every extension that is included with the buildpack and the application.  There is no mechanism to disable specific extensions.  Thus, when you write an extension, you should make some way for the user to enable / disable it's functionality.  See the [NewRelic] extension for an example of this.
  - If an extension requires configuration, it should be included with the extension.  The `defaults/options.json` file is for the buildpack and its core extensions.  See the [NewRelic] buildpack for an example of this.
  - Extensions should have their own test module.  This generally takes the form `tests/test_<extension_name>.py`.

### Testing

#### Running unit tests

The buildpack makes use of [Nose] for testing.  You can run the full suite of tests with this command.

```
./run_tests.sh
```

That will run all of the tests.  You can run individual tests with this command.

```
nosetests tests/test_<name>.py
```

To debug tests or see the output, you can run with the `-s` option.  This will prevent nose from capturing the output of stdout.  Alternatively, you can use the `--pdb` argument to drop to a debugger when a test fails.

Data for all tests is stored under `tests/data`.

### Tips

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
[NewRelic]:https://github.com/cloudfoundry/php-buildpack/tree/master/extensions/newrelic
[unit tests]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/development.md#testing
