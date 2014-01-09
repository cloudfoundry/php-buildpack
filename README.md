CloudFoundry PHP Buildpack
==========================

A build pack for CloudFoundry to deploy PHP based applications.

This is an experimental build pack to run PHP applications on CloudFoundry.  It builds on my experiences developing the [CF PHP & Apache Build Pack](https://github.com/dmikusa-pivotal/cf-php-apache-buildpack).

Goals
-----

Here are some of the general goals for this build pack.  At the moment, these are just goals, but hopefully they'll become features soon.

 1. Use clean and easily understandable detect, compile and release scripts.
 1. Execute quickly.  Run detect, compile and release scripts as quickly as possible, downloading as little as possible.
 1. Allow application developers to easily customize build pack behavior through configuration.
 1. Allow the build pack to be extended via extensions and allow application developers to include custom extensions.
 1. Not be tied to one particular HTTP server.  Support many and allow application developers to pick which they use.
 1. Provide better insight into the application environment.  Allow application and servers to be easily monitored.
 1. Handle x-forwarded-for and x-forwarded-proto headers passed by the CF router.
 1. Integrate logging into loggregator

Instructions
------------

Coming soon...  In the meantime, don't use this build pack.  Use [CF PHP & Apache Build Pack](https://github.com/dmikusa-pivotal/cf-php-apache-buildpack).

Examples
--------

Coming soon...

Behind the Scenes
-----------------

Coming soon...

Configuration
-------------

Coming soon...

Development
-----------

The build pack is broken down into the following parts:

 1. The [bash scripts](https://github.com/dmikusa-pivotal/cf-php-buildpack/tree/master/bin) that implement the build pack interface.  These bootstrap and delegate to the [Python scripts](https://github.com/dmikusa-pivotal/cf-php-buildpack/tree/master/scripts) of the same name.
 1. The [Python scripts](https://github.com/dmikusa-pivotal/cf-php-buildpack/tree/master/scripts) that define the steps the build pack takes prepare the application.  These use the [build_pack_utils library](https://github.com/dmikusa-pivotal/py-cf-buildpack-utils) which performs the heavy lifting.
 1. The [configuration](https://github.com/dmikusa-pivotal/cf-php-buildpack/blob/master/defaults/options.json) which defines the details about what is installed.  Configuration options can be overridden by the end user.

