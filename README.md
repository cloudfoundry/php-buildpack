CloudFoundry PHP Buildpack
==========================

A build pack for CloudFoundry to deploy PHP based applications.


Instructions
------------

Coming soon...

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

