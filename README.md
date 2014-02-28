## CloudFoundry PHP Buildpack

A build pack for CloudFoundry to deploy PHP based applications.

This is the next generation build pack for running PHP applications on CloudFoundry and it supersedes the [CF PHP & Apache Build Pack].  The rationale behind creating this build pack is to use the experiences and feedback gained while writing and using the old build pack with CloudFoundry to make a better build pack.  This includes improving the end user experience as well as the quality of the code, its stability, extensibility and readability.

## 30 Second Tutorial

Getting started with the build pack is easy.  With the cf command line utility installed, open a shell, change directories to the root of your PHP files and push your application using the argument `-b https://github.com/dmikusa-pivotal/cf-php-build-pack.git`.

Example:

```bash
mkdir my-php-app
cd my-php-app
cat << EOF > index.php
<?php
  phpinfo();
?>
EOF
cf push -m 128M -b https://github.com/dmikusa-pivotal/cf-php-build-pack.git my-php-app
```

Please note that you should change *my-php-app* to some unique name, otherwise you'll get an error and the push will fail.

The example above will create and push a test application, "my-php-app", to CloudFoundry.  The `-b` argument instructs CF to use this build pack.  The remainder of the options and arguments are not specific to the build pack, for questions on those consult the output of `cf push -h`.

Here's a breakdown of what happens when you run the example above.

  - On your PC...
    - It'll create a new directory and one PHP file, which calls `phpinfo()`
    - Run cf to push your application.  This will create a new application with a memory limit of 128M (more than enough here) and upload our test file.
  - On the Server...
    - The build pack is executed.
    - Application files are copied to the *htdocs* folder.
    - Apache HTTPD & PHP 5.4 are downloaded, configured with the build pack defaults and run.
    - Your application is accessible at the URL http://<app-name>.cfapps.io (assuming your targeted towards Pivotal Web Services).

## More Information

While the *30 Tecond Tutorial* shows how quick and easy it is to get started using the build pack, it skips over quite a bit of what you can do to adjust, configure and extend the build pack.  The following docs and links provide a more indepth look at the build pack.

  - [Goals](#goals)
  - [Features](#features)
  - [Example Applications](#examples)
  - [Usage]
  - [Configuration Options]
  - [Troubleshooting]
  - [Development]

### Goals

Here are the general goals of the build pack (in no particular order):

  - Maintain clean and easily understandable detect, compile and release scripts.
  - Execute quickly.  Run detect, compile and release scripts with minimal effort, downloading as little as possible.
  - Utilize a default configuration that "just works" for the majority of users.
  - Allow application developers to override default build pack behavior and settings through configuration.
  - Allow the build pack to be extended easily via extensions.
  - Allow application developers to include custom extensions.
  - Not be tied to one particular HTTP server.  Support multiple and allow application developers to pick which they use.
  - Provide better insight into the application environment.  Allow application and servers to be easily monitored.
  - Integrate all logs and output into loggregator.

## Features

Here's a list of the major features of the build pack.

  - supports the latest versions of Apache HTTPD 2.4 and Nginx 1.5
  - supports the latest versions of PHP 5.4 and 5.5
  - supports a large set of PHP extensions, including amqp, apc, bz2, curl, dba, gd, gettext, gmp, imap, ldap, mcrypt, mongodb, openssl, pdo_pgsql, pgsql, pspell, redis, xdebug and zlib
  - versions of HTTPD, Nginx and PHP are automatically upgraded to the latest release just by restaging an application
  - allows for application developers to control which PHP extensions are installed
  - allows for application developers to custom configure HTTPD, Nginx or PHP
  - download location is configurable, allowing users to host binaries on the same network (i.e. run without an internet connection)
  - supports an extension mechanism that allows the build pack to provided additional functionality
  - allows for application developers to provide custom extensions
  - support NewRelic through an extension
  - NewRelic support works for bound services or when manually specifying a license key
  - easy troubleshooting with the BP_DEBUG environment variable
  - all logging output is routed through stderr & stdout which is sent to loggregator

## Examples

Here are some example applications that can be used with this build pack.

  - [php-info]  This app has a basic index page and shows the output of phpinfo()


[CF PHP & Apache Build Pack]:https://github.com/dmikusa-pivotal/cf-php-apache-buildpack
[Configuration Options]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/config.md
[Development]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/development.md
[Troubleshooting]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/troubleshooting.md
[php-info]:https://github.com/dmikusa-pivotal/cf-ex-php-info
