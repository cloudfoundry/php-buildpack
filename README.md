## CloudFoundry PHP Build pack

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

While the *30 Second Tutorial* shows how quick and easy it is to get started using the build pack, it skips over quite a bit of what you can do to adjust, configure and extend the build pack.  The following docs and links provide a more in-depth look at the build pack.

  - [Goals](#goals)
  - [Features](#features)
  - [Example Applications](#examples)
  - [Usage]
  - [Configuration Options]
  - [Composer]
  - [Binaries]
  - [Troubleshooting]
  - [Getting Help](#getting-help)
  - [Issues & Feature Requests](#issues--feature-requests)
  - [Development]
  - [Releases](#releases)
  - [License](#license)

## Goals

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

  - supports the latest versions of Apache HTTPD 2.4 and Nginx 1.5, 1.6 & 1.7
  - supports the latest versions of PHP 5.4, 5.5 and 5.6.
  - supports a large set of PHP extensions, including amqp, apc, apcu, bz2, curl, codizy, dba, exif, fileinfo, ftp, gd, gettext, gmp, igbinary, imagick, imap, intl, ioncube, ldap, mailparse, mbstring, mcrypt, memcache, memcached, mongo, msgpack, mysql, mysqli, opcache, openssl, pdo, pdo_mysql, pdo_pgsql, pdo_sqlite, pgsql, phalcon, phpiredis, pspell, redis, suhosin, snmp, soap, sockets, sundown, twig, xcache, xdebug, xhprof, zip and zlib
  - allows installing PHP runtime of choice: php cli, php cgi or php-fpm
  - versions of HTTPD, Nginx and PHP are automatically upgraded to the latest release just by re-staging an application
  - allows for application developers to control which PHP extensions are installed
  - allows for application developers to custom configure HTTPD, Nginx or PHP
  - supports running stand alone PHP scripts
  - supports running applications that use [Composer]
  - supports running commands or mirgration scripts prior to application startup
  - download location is configurable, allowing users to host binaries on the same network (i.e. run without an Internet connection)
  - supports running in ["offline" mode] where binaries are bundled with the build pack
  - supports an extension mechanism that allows the build pack to provided additional functionality
  - allows for application developers to provide custom extensions
  - support NewRelic & Codizy through an extension
  - Codizy & NewRelic support works for bound services or when manually enabling it
  - easy troubleshooting with the BP_DEBUG environment variable
  - all logging output is routed through stderr & stdout which is sent to loggregator

## Examples

Here are some example applications that can be used with this build pack.

  - [php-info]  This app has a basic index page and shows the output of phpinfo()
  - [PHPMyAdmin]  A deployment of PHPMyAdmin that uses bound MySQL services
  - [Wordpress]  A deployment of Wordpress that uses bound MySQL service
  - [CodeIgniter]  CodeIgniter tutorial application running on CF
  - [Stand Alone]  An example which runs a stand alone PHP script
  - [pgbouncer]  An example which runs the pgbouncer process in the container to pool db connections.
  - [phalcon]  An example which runs a Phalcon based application.
  - [composer] An example which uses Composer.

## Getting Help

If you have questions, comments or need further help with the build pack you can post to the [vcap-dev] mailing list. It's a good place for posting question on all of the open source CloudFoundry components, like this build pack. Alternatively, if you're using Pivotal Web Services with the build pack, you could post to the [support forums]. I keep an eye on both places.

## Releases

When using a custom build pack with CloudFoundry, you need to specify the Git URL for the build pack.  By default, this will pull down the master branch of the build pack.  With the CF PHP Build pack, the master branch is where work and new development occurs.  By using this branch it will get you all the latest and greatest developments from the build pack.

If you'd like something that is a little more stable, you can select one of the release tags of the build pack.  You can specify a release tag by appending `#<tag>` to the end of the build pack's URL.  

```yaml
---
applications:
- name: my-php-app
  memory: 128M
  instances: 1
  host: my-php-app
  path: .
  buildpack: https://github.com/dmikusa-pivotal/cf-php-build-pack#v2.0
```

The benefit of using a release tag is that it is stable, at least it should be.  No new features or changes will be made to a release tag.  This means if your app pushes OK now, it should push OK six months from now as long as you're using the same release tag.  The downfall of this is that, the tag is stuck at a point in time and won't receive updates to the binaries, like PHP, HTTPD and Nginx.

In the past, I was maintaining releases as branches on the build pack and back porting upgrades to binaries.  Because this build pack is a project that I maintain in my spare time and I do not have infinite resources, I've switched to tags which consume less time.  The older branches will continue to exist and can continue to be used, but will not receive any further updates.  The branches are numbers 1.x, while tags will start with 2.x.

## Issues & Feature Requests

This project is managed through Github.  If you encounter any issues, bug or problems with the build pack please open an issue.  Feature requests can also be submitted this way too.

## License

The CloudFoundry PHP Build Pack is released under version 2.0 of the [Apache License].

## Third Party Code & Services Disclaimer

This build pack facilitates the use of third party code and services with your application.  Please do not take this as an endorsement or guarantee of fitness for said third party code or services.  This build pack is simply striving to make your life as easy as possible if *you* decide to use third party code or a particular service.  The bottom line, it's *your* choice to use third party code or services and *you* should be diligently evaluating them to make sure the code or service fits your needs.


[CF PHP & Apache Build Pack]:https://github.com/dmikusa-pivotal/cf-php-apache-buildpack
[Configuration Options]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/config.md
[Development]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/development.md
[Troubleshooting]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/troubleshooting.md
[Usage]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/usage.md
[Binaries]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/binaries.md
[php-info]:https://github.com/dmikusa-pivotal/cf-ex-php-info
[PHPMyAdmin]:https://github.com/dmikusa-pivotal/cf-ex-phpmyadmin
[Wordpress]:https://github.com/dmikusa-pivotal/cf-ex-worpress
[CodeIgniter]:https://github.com/dmikusa-pivotal/cf-ex-code-igniter
[Stand Alone]:https://github.com/dmikusa-pivotal/cf-ex-stand-alone
[pgbouncer]:https://github.com/dmikusa-pivotal/cf-ex-pgbouncer
[Apache License]:http://www.apache.org/licenses/LICENSE-2.0
[vcap-dev]:https://groups.google.com/a/cloudfoundry.org/forum/#!forum/vcap-dev
[support forums]:http://support.run.pivotal.io/home
[Composer]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/composer.md
["offline" mode]:https://github.com/dmikusa-pivotal/cf-php-build-pack/blob/master/docs/binaries.md#bundling-binaries-with-the-build-pack
[phalcon]:https://github.com/dmikusa-pivotal/cf-ex-phalcon
[Phalcon]:http://phalconphp.com/en/
[composer]:https://github.com/dmikusa-pivotal/cf-ex-composer
