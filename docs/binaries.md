## Binaries

To reduce the time it takes for the build pack to run and setup a usable environment, the build pack makes use of precompiled binaries.  For general use, these binaries are hosted on DropBox.  If you're running on a public cloud like Pivotal Web Services, you should be able to use these binaries without any problems and you probably do not need to read any further.  If you are running in a private environment or if for security reasons, you'd like to compile your own binaries, this document will explain what you need to do.

### Binary Repo Structure

The binary repository used by the build pack is simple and uses the following folder structure:  `<package>/<version>/<binary-file>`.  In this example, package would be the name of the binary like `php` or `httpd`, the version would be the full version number of the package to be installed and the binary file would be the name of the file to download.

Ex:

```
$REPO_ROOT/php/5.5.10/php-5.5.10.tar.gz
```

The repository is accessed by the build pack over HTTP or HTTPS and can be hosted on any web server, so long as the build pack can access it.  For convenience, you can also place the repository in a sub folder on the web server.  You just need to adjust the `DOWNLOAD_URL` link accordingly.

Ex:

```
http:/server/cf/php-repo/php/5.5.10/php-5.5.10.tar.gz
```

The `DOWNLOAD_URL` would be `http://server/cf/php-repo`.

### Building Your Own Repository

The easiest way to build your own repository is to run the `bin/binaries download` command.  This is a script that is included with the build pack and when run it will read the file `binaries/index-latest.json` and download the latest set of binaries from DropBox.  When it completes, you'll have a working set of binaries on your local machine.  

To use the downloaded files with the build pack, you just need to copy them to your web server and set the `DOWNLOAD_URL` to point to your web server.  Setting `DOWNLOAD_URL` can be done per application, in `.bp-config/options.json`, or by forking the build pack and modifying `defaults/options.json`.

#### Usage:  binaries

The `binaries download` command expects one argument, the path where it should place the downloaded binaries.

Ex:

```
./binaries download binaries
```

This will look for the `index-latest.json` file at the path `binaries/index.json`.  If the index file is in a different location, you can specify that with the `--index` option.

Ex:

```
./binaries download --index=binaries/index-latest.json binaries
```

By default, the `binaries download` command will only download the most recent version of each package.  In other words, it'll pull in the most recent version of PHP, HTTPD, Nginx and other packages used by the build pack.  If you want it to download the full list of available binaries, just use the `--index` argument and point to the `binaries/index-all.json` file.  This file contains a full index of the available downloads.

Ex:

```
./binaries download --index=binaries/index-all.json binaries
```

It is *not* necessary to download all of the binaries, unless you specifically need support for an older version of software, so using the `index-all.json` file will generally just make the command take longer to run.

If you'd like to select a custom set of packages and versions to download, you can do that by starting with the `index-all.json` file and removing the packages, versions and files that you do not want to include.

#### Python Versions

If you have [PyEnv] installed on your system, you'll notice that the build pack includes a `.python-version` file.  This instructs PyEnv to use Python 2.6.6, which is the same version used by CloudFoundry (at least at the moment).  This presents a minor issue in that Python 2.6.x does not contain the `argparse` library and that library is used by the `binaries` script.  There are three ways to handle this.

1. If you do not have PyEnv installed, nothing will happen and you'll use whatever version of Python you have installed on your system.  In most cases, this will be Python 2.7.x, the script should run fine and you should not need to do anything else.  If your system version is not Python 2.7.x, you'll need to install Python 2.7.x (not this script may work with Python 3, but I haven't tested it).

2. If you have PyEnv installed, you'll need to run `pyenv local system` to switch to your system version of Python (again, probably Python 2.7.x) or install Python 2.7.6 with PyEnv and switch to that.

3. If you have PyEnv installed, create a virtual environment by running ```virtualenv `pwd`/env```.  Then activate the virtual environment by running `. ./env/bin/activate` and run `pip install --allow-external argparse -r requirements.txt`, which will install argparse into the virtual environment.  With that you can run the `binaries` script, but only when the virtual environment is active.

### Bundling Binaries With the Build Pack

It is possible to bundle the required binaries with the build pack.  When doing this, the build pack is self-contained and should have everything it needs to run.  This is not possible if you're using a public CF instance that is run by someone else (i.e. Pivotal Web Services), however if you're running a private cloud then you can install the build pack (see `cf create-buildpack`), which is a nice option as the installed build pack is local and will not need to download anything from the internet.

Here are the steps you would need to do this.

1. Clone the repository.  Check out a release branch, a specific commit or head.
1. Run `bin/binaries zip --index binaries/index-latest.json`.  This will download the latest set of binaries and packagae it with the build pack that you have checked out.
1. Run `cf create-buildpack` pointing to the file that was generated in the previous step.  This will install the build pack on your private cloud (as long as you have permissions).
1. Now you can `cf push` a PHP application and you no longer need to set the `-b` argument or specify the build pack in your manifest file.

[PyEnv]:https://github.com/yyuu/pyenv
