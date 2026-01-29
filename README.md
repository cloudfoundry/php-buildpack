# Cloud Foundry PHP Buildpack

[![CF Slack](https://www.google.com/s2/favicons?domain=www.slack.com) Join us on Slack](https://cloudfoundry.slack.com/messages/buildpacks/)

A buildpack to deploy PHP applications to Cloud Foundry based systems, such as a [cloud provider](https://www.cloudfoundry.org/learn/certified-providers/) or your own instance.

### Buildpack User Documentation

Official buildpack documentation can be found here: [php buildpack docs](http://docs.cloudfoundry.org/buildpacks/php/index.html).

**Developer Documentation:**
- [docs/](docs/) - Architecture and implementation guides
  - [User Guide](docs/USER_GUIDE.md) - Complete user guide for all buildpack features
  - [Features Reference](docs/FEATURES.md) - Developer reference with test coverage verification
  - [VCAP_SERVICES Usage](docs/VCAP_SERVICES_USAGE.md) - Service binding patterns
  - [Buildpack Comparison](docs/BUILDPACK_COMPARISON.md) - Alignment with CF standards
  - [Migration Guide](docs/REWRITE_MIGRATION.md) - v4.x to v5.x migration

### Building the Buildpack

To build this buildpack, run the following commands from the buildpack's directory:

1. Source the .envrc file in the buildpack directory.

   ```bash
   source .envrc
   ```
   To simplify the process in the future, install [direnv](https://direnv.net/) which will automatically source `.envrc` when you change directories.

1. Install buildpack-packager

    ```bash
    go install github.com/cloudfoundry/libbuildpack/packager/buildpack-packager@latest
    ```

1. Build the buildpack

    ```bash
    buildpack-packager build [ --cached ]
    ```

   Alternatively, use the package script:

    ```bash
    ./scripts/package.sh [ --cached ]
    ```

1. Use in Cloud Foundry

   Upload the buildpack to your Cloud Foundry and optionally specify it by name

    ```bash
    cf create-buildpack [BUILDPACK_NAME] [BUILDPACK_ZIP_FILE_PATH] 1
    cf push my_app [-b BUILDPACK_NAME]
    ```

### Contributing
Find our guidelines [here](https://github.com/cloudfoundry/php-buildpack/blob/develop/CONTRIBUTING.md).

### Testing

Buildpacks use the [Switchblade](https://github.com/cloudfoundry/switchblade) framework for running integration tests against Cloud Foundry. Before running the integration tests, you need to login to your Cloud Foundry using the [cf cli](https://github.com/cloudfoundry/cli):

```bash
cf login -a https://api.your-cf.com -u name@example.com -p pa55woRD
```

Note that your user requires permissions to run `cf create-buildpack` and `cf update-buildpack`. To run the integration tests, run the following commands from the buildpack's directory:

1. Source the .envrc file in the buildpack directory.

   ```bash
   source .envrc
   ```
   To simplify the process in the future, install [direnv](https://direnv.net/) which will automatically source .envrc when you change directories.

1. Run unit tests

    ```bash
    ./scripts/unit.sh
    ```

1. Run integration tests

    ```bash
    ./scripts/integration.sh
    ```

More information can be found on Github [switchblade](https://github.com/cloudfoundry/switchblade).

### Project Structure

The project is broken down into the following directories:

  - `bin/` - Executable shell scripts for buildpack lifecycle: `detect`, `supply`, `finalize`, `release`, `start`
  - `src/php/` - Go source code for the buildpack
    - `detect/` - Detection logic
    - `supply/` - Dependency installation (PHP, HTTPD, Nginx)
    - `finalize/` - Final configuration and setup
    - `release/` - Release information
    - `extensions/` - Extension system (composer, newrelic, appdynamics, sessions)
    - `config/` - Configuration management
    - `options/` - Options parsing
    - `hooks/` - Lifecycle hooks (dynatrace integration)
    - `integration/` - Integration tests
    - `unit/` - Unit tests
  - `defaults/` - Default configuration files
  - `fixtures/` - Test fixtures and sample applications
  - `scripts/` - Build and test scripts

### Understanding the Buildpack

This buildpack uses Cloud Foundry's [libbuildpack](https://github.com/cloudfoundry/libbuildpack) framework and is written in Go. The buildpack lifecycle consists of:

#### Build-Time Phases

1. **Detect** (`bin/detect` → `src/php/detect/`) - Determines if the buildpack should be used by checking for PHP files or `composer.json`

2. **Supply** (`bin/supply` → `src/php/supply/`) - Installs dependencies:
   - Downloads and installs PHP
   - Downloads and installs web server (HTTPD or Nginx)
   - Runs extensions in "configure" and "compile" phases
   - Installs PHP extensions
   - Runs Composer to install application dependencies

3. **Finalize** (`bin/finalize` → `src/php/finalize/`) - Final configuration:
   - Configures web server (HTTPD or Nginx)
   - Sets up PHP and PHP-FPM configuration
   - Copies start binary to `.bp/bin/`
   - Processes configuration files to replace build-time placeholders with runtime values
   - Generates preprocess scripts that will run at startup
   - Prepares runtime environment

4. **Release** (`bin/release` → `src/php/release/`) - Provides process types and metadata

#### Runtime Phases

5. **Start** (`bin/start` → `src/php/start/cli/`) - Process management:
   - Runs preprocess commands
   - Handles dynamic runtime variables (PORT, TMPDIR) via sed replacement
   - Launches all configured services (PHP-FPM, web server, etc.) from `.procs` file
   - Monitors all processes
   - If any process exits, terminates all others and restarts the application

### Configuration Placeholders

The buildpack uses a two-tier placeholder system for configuration files:

#### Build-Time Placeholders (`@{VAR}`)

These placeholders are replaced during the **finalize phase** (staging/build time) with known values:

- `@{HOME}` - Replaced with dependency or app directory path
- `@{DEPS_DIR}` - Replaced with `/home/vcap/deps`
- `@{WEBDIR}` - Replaced with web document root (default: `htdocs`)
- `@{LIBDIR}` - Replaced with library directory (default: `lib`)
- `@{PHP_FPM_LISTEN}` - Replaced with PHP-FPM socket/TCP address
- `@{TMPDIR}` - Converted to `${TMPDIR}` for runtime expansion
- `@{PHP_EXTENSIONS}` - Replaced with extension directives
- `@{ZEND_EXTENSIONS}` - Replaced with Zend extension directives
- `@{PHP_FPM_CONF_INCLUDE}` - Replaced with fpm.d include directive

**Example** (php.ini):
```ini
; Before finalize:
extension_dir = "@{HOME}/php/lib/php/extensions"
include_path = "@{HOME}/@{LIBDIR}"

; After finalize:
extension_dir = "/home/vcap/deps/0/php/lib/php/extensions"
include_path = "/home/vcap/deps/0/lib"
```

#### Runtime Variables (`${VAR}`)

These are standard environment variables expanded at **runtime**:

- `${PORT}` - HTTP port assigned by Cloud Foundry (dynamic)
- `${TMPDIR}` - Temporary directory (can be customized)
- `${HOME}` - Application directory
- `${HTTPD_SERVER_ADMIN}` - Apache admin email

**Supported by:**
- **Apache HTTPD** - Native variable interpolation for any `${VAR}`
- **Bash scripts** - Standard shell expansion for any `${VAR}`
- **Nginx/PHP configs** - Only `${PORT}` and `${TMPDIR}` via sed replacement

**Example** (httpd.conf):
```apache
Listen ${PORT}                    # Expanded by Apache at runtime
ServerRoot "${HOME}/httpd"        # Expanded by Apache at runtime
DocumentRoot "${HOME}/htdocs"     # Expanded by Apache at runtime
```

**Note:** Custom placeholders are **not supported**. To use custom configuration values, either:
- Use environment variables with `${VAR}` syntax (works with Apache/bash)
- Set values directly in your code instead of using placeholders

### Extensions

The buildpack includes several built-in extensions written in Go:

- **[composer](src/php/extensions/composer/)** - [Downloads, installs and runs Composer](http://docs.cloudfoundry.org/buildpacks/php/gsg-php-composer.html). Automatically detects PHP version requirements from `composer.json` and validates against locked dependencies.
- **[newrelic](src/php/extensions/newrelic/)** - [Downloads, installs and configures the NewRelic agent for PHP](http://docs.cloudfoundry.org/buildpacks/php/gsg-php-newrelic.html)
- **[dynatrace](src/php/hooks/dynatrace.go)** - Downloads and configures Dynatrace OneAgent using the official [libbuildpack-dynatrace](https://github.com/Dynatrace/libbuildpack-dynatrace) library. Looks for a bound service with name `dynatrace` and credentials containing `apiurl`, `environmentid`, and `apitoken`.
- **[appdynamics](src/php/extensions/appdynamics/)** - Downloads and configures AppDynamics agent
- **[sessions](src/php/extensions/sessions/)** - [Configures PHP to store session information in a bound Redis or Memcached service instance](http://docs.cloudfoundry.org/buildpacks/php/gsg-php-sessions.html)

### Extension Architecture

Extensions implement the `Extension` interface defined in [`src/php/extensions/extension.go`](src/php/extensions/extension.go):

```go
type Extension interface {
    Name() string
    ShouldCompile(ctx *Context) (bool, error)
    Configure(ctx *Context) error
    Compile(installer Installer) error
    PreprocessCommands(ctx *Context) ([]string, error)
    ServiceCommands(ctx *Context) (map[string]string, error)
    ServiceEnvironment(ctx *Context) (map[string]string, error)
}
```

**Extension Lifecycle:**

1. **Configure** - Called early to modify buildpack configuration (e.g., set PHP version, add extensions)
2. **Compile** - Main extension logic, downloads and installs components
3. **ServiceEnvironment** - Contributes environment variables
4. **ServiceCommands** - Contributes long-running services
5. **PreprocessCommands** - Contributes commands to run before services start

For examples, see the built-in extensions in `src/php/extensions/`.

### User Extensions

The buildpack supports user-defined extensions through the `.extensions/` directory. This allows you to add custom startup commands, environment variables, and services without modifying the buildpack itself.

#### Creating a User Extension

Create a directory `.extensions/<name>/` in your application with an `extension.json` file:

```
myapp/
├── .extensions/
│   └── myext/
│       └── extension.json
├── index.php
└── .bp-config/
    └── options.json
```

#### extension.json Format

```json
{
    "name": "my-custom-extension",
    "preprocess_commands": [
        "echo 'Running setup'",
        ["./bin/setup.sh", "arg1", "arg2"]
    ],
    "service_commands": {
        "worker": "php worker.php --daemon"
    },
    "service_environment": {
        "MY_VAR": "my_value",
        "ANOTHER_VAR": "another_value"
    }
}
```

**Fields:**

- `name` - Extension identifier (defaults to directory name)
- `preprocess_commands` - Commands to run at container startup before PHP-FPM starts. Each command can be a string or array of arguments.
- `service_commands` - Map of long-running background services (name → command)
- `service_environment` - Environment variables to set for services

### Additional Configuration Options

#### ADDITIONAL_PREPROCESS_CMDS

Run custom commands at container startup before PHP-FPM starts. Useful for migrations, cache warming, or other initialization tasks.

**Configuration (`.bp-config/options.json`):**

```json
{
    "ADDITIONAL_PREPROCESS_CMDS": [
        "php artisan migrate --force",
        "php artisan config:cache",
        ["./bin/setup.sh", "arg1", "arg2"]
    ]
}
```

Commands can be:
- A string: `"echo hello"` - runs as a single command
- An array: `["script.sh", "arg1"]` - arguments joined with spaces

#### Standalone PHP Mode (APP_START_CMD)

For CLI/worker applications that don't need a web server or PHP-FPM, you can run a PHP script directly.

**Configuration (`.bp-config/options.json`):**

```json
{
    "WEB_SERVER": "none",
    "APP_START_CMD": "worker.php"
}
```

**Auto-detection:** If `WEB_SERVER` is set to `"none"` and `APP_START_CMD` is not specified, the buildpack searches for these entry point files:
- `app.php`
- `main.php`
- `run.php`
- `start.php`

If none are found, it defaults to running PHP-FPM only (for custom proxy setups).

**Example worker script:**

```php
<?php
// worker.php - Long-running background worker
echo "Worker started\n";

while (true) {
    // Process jobs from queue
    processNextJob();
    sleep(1);
}
```

**Note:** Standalone apps on Cloud Foundry may need special health check configuration since they don't have an HTTP endpoint.

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
