# Usage

Getting started with the buildpack is simple.  It's designed to be easy to use and minimally invasive.  For a quick start, see the [30 Second Tutorial].  This document will go into further detail and explain the more advanced options.

## Folder Structure

The easiest way to use the buildpack is to put your assets and PHP files into a directory and push it to Cloud Foundry.  When you do this, the buildpack will take your files and automatically move them into the `WEBDIR` (defaults to `htdocs`) folder, which is the directory where your chosen web server looks for the files.

### URL Rewriting

If you select Apache as your web server, you can include `.htaccess` files with your application.

Alternatively, you can [provide your own Apache or Nginx configurations].

### Preventing Access To PHP Files

The buildpack will put all of your files into a publicly accessible directory.  In some cases, you might want to have PHP files that are not publicly accessible but are on the [include_path].  To do that, you simply create a `lib` directory in your project folder and place your protected files there.

Example:

```bash
$ ls -lRh
total 0
-rw-r--r--  1 daniel  staff     0B Feb 27 21:40 images
-rw-r--r--  1 daniel  staff     0B Feb 27 21:39 index.php
drwxr-xr-x  3 daniel  staff   102B Feb 27 21:40 lib

./lib:
total 0
-rw-r--r--  1 daniel  staff     0B Feb 27 21:40 my.class.php  <-- not public, http://app.cfapps.io/lib/my.class.php == 404
```

This comes with a catch.  If your project legitimately has a `lib` directory, these files will not be publicly available because the buildpack does not copy a top-level `lib` directory into the `WEBDIR` folder.  If your project has a `lib` directory that needs to be publicly available then you have two options.

#### Option #1

In your project folder, create an `htdocs` folder (or whatever you've set for `WEBDIR`).  Then move any files that should be publicly accessible into this directory.  In the example below, the `lib/controller.php` file is publicly accessible.

Example:

```bash
$ ls -lRh
total 0
drwxr-xr-x  7 daniel  staff   238B Feb 27 21:48 htdocs

./htdocs:  <--  create the htdocs directory and put your files there
total 0
-rw-r--r--  1 daniel  staff     0B Feb 27 21:40 images
-rw-r--r--  1 daniel  staff     0B Feb 27 21:39 index.php
drwxr-xr-x  3 daniel  staff   102B Feb 27 21:48 lib

./htdocs/lib:   <--  anything under htdocs is public, including a lib directory
total 0
-rw-r--r--  1 daniel  staff     0B Feb 27 21:48 controller.php
```

Given this setup, it is possible to have both a public `lib` directory and a protected `lib` directory.  Here's an example of that setup.

Example:

```bash
$ ls -lRh
total 0
drwxr-xr-x  7 daniel  staff   238B Feb 27 21:48 htdocs
drwxr-xr-x  3 daniel  staff   102B Feb 27 21:51 lib

./htdocs:
total 0
-rw-r--r--  1 daniel  staff     0B Feb 27 21:40 images
-rw-r--r--  1 daniel  staff     0B Feb 27 21:39 index.php
drwxr-xr-x  3 daniel  staff   102B Feb 27 21:48 lib

./htdocs/lib:  <-- public lib directory
total 0
-rw-r--r--  1 daniel  staff     0B Feb 27 21:48 controller.php

./lib: <-- protected lib directory
total 0
-rw-r--r--  1 daniel  staff     0B Feb 27 21:51 my.class.php
```

#### Option #2

The second option is to pick a different name for the `LIBDIR`.  This is a configuration option that you can set (it defaults to `lib`).  Thus if you set it to something else, like `include` your application's `lib` directory would no longer be treated as a special directory and it would be placed into `WEBDIR` (i.e. become public).

#### Other Folders

Beyond the `WEBDIR` and `LIBDIR` directories, the buildpack also supports a `.bp-config` directory and a `.extensions` directory.  

The `.bp-config` directory should exist at the root of your project directory and it is the location of application specific configuration files.  Application specific configuration files override the default settings used by the buildpack.  This link explains [application configuration files] in depth.

The `.extensions` directory should also exist at the root of your project directory and it is the location of application specific custom extensions.  Application specific custom extensions allow you, the developer, to override or enhance the behavior of the buildpack.  This link explains [extensions] in more detail.

[30 Second Tutorial]:https://github.com/cloudfoundry/php-buildpack#30-second-tutorial
[application configuration files]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/config.md
[include_path]:http://us1.php.net/manual/en/ini.core.php#ini.include-path
[extensions]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/development.md#extensions
[provide your own Apache or Nginx configurations]:https://github.com/cloudfoundry/php-buildpack/blob/master/docs/config.md#httpd-nginx-and-php-configurations
