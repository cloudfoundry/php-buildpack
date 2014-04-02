## Binaries

To reduce the time it takes for the build pack to run and setup a usable environment, the build pack makes use of precompiled binaries.  For general use, these binaries are hosted on DropBox.  If you're running on a public cloud like Pivotal Web Services, you should be able to use these binaries without any problems and you probably do not need to read any further.  If you are running in a private environment or if for security reasons, you'd like to compile your own binaries, this document will explain what you need to do.

### Binary Repo Structure

The binary repository used by the build pack is simple and uses the following folder structure:  ```<package>/<version>/<binary-file>`.  In this example, package would be the name of the binary like `php` or `httpd`, the version would be the full version number of the package to be installed and the binary file would be the name of the file to download.

The repository is accessed by the build pack over HTTP and thus can be hosted on any web server, so long as the build pack can access it.

### Building Your Own Repository

The easiest way to build your own repository is to run the `bin/binaries download` command.  This is a script that is included with the build pack and when run it will read the file `binaries/index.json` and download the binaries it needs from DropBox.  When it completes, you'll have a working set of binaries on your local machine.  

To use these with the build pack, you just need to copy them to your web server and set the `DOWNLOAD_URL` to point to your web server.  Setting `DOWNLOAD_URL` can be done per application, in `.bp-config/options.json`, or by forking the build pack and modifying `defaults/options.json`.

#### Usage:  binaries

The `binaries download` command expects one argument, the path where it should place the downloaded binaries.

Ex:

```
./binaries download my-binaries
```

This will look for the index.json file at the path `my-binaries/index.json`.  If the index file is in a different location, you can specify that with the `--index` option.

Ex:

```
./binaries download --index=binaries/index.json my-binaries
```

By default, the `binaries download` command will only download the most recent version of each package.  In other words, it'll pull in the most recent version of PHP, HTTPD and Nginx.  If you want the full list of available binaries, you can specify the `--latest` argument and set it to `False`.

Ex:

```
./binaries download --index=binaries/index.json --latest=False my-binaries
```

It is not necessary to download all of the binaries, unless you specifically need support for an older version of software, so specifying `--latest=False` will generally just make the command take longer to run.

### Bundling Binaries With the Build Pack

While I don't generally recommend this option, it is possible to bundle the binaries with the build pack.  When doing this, the build pack is self contained and should have everything it needs to run.  The downside of this is that the build pack will be much, much larger and it'll take longer to download.  However, if you're running a private cloud and you want to install the build pack (see `cf create-buildpack`), this is not a bad option as the installed build pack would only be downloaded once and so the overhead of the larger build pack would not be an issue.

Here are the steps you would need to do this.

1. Clone the project:  `git clone https://github.com/dmikusa-pivotal/cf-php-build-pack`
1. Run `bin/binaries download binaries`.  This will download the binaries into the `binaries` directory.
1. Edit the `defaults/options.json` file.  Change DOWNLOAD_URL to `file://{BP_DIR}/binaries`.  This instructs the build pack to find the binaries locally and in the directory that we populated in the previous steps.
1. Add, `git add binaries defaults/options.json` and commit the binaries to your repo, `git ci -m "Added binaries, changed DOWNLOAD_URL to use local binaries."`.
1. Publish your git repo or a zip archive of the repository.
1. Run `cf create-buildpack` pointing to either the git repo or the zip archive of the repositor.  The build pack will be installed with it's binaries.

