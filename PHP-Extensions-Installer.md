## PHP Extension Installer

The PHP Buildpack provides an extension to locate and enable PHP Extensions provided with an application.

### Usage

Create a directory at the root of the application called ```.php-extensions```.  Put extensions (.so files) in this directory.  The buildpack extension will add a line to php.ini to load the extension.  If the extension has dependant libraries, create a ```lib``` directory under ```.php-extensions``` with the dependencies in it.  The buildpack extension will copy them to php/lib when the application is deployed.

Simple Application Structure with Extension
```
|-- index.php
|-- manifest.yml
`-- .php-extensions
    |-- lib
    |   `-- extension_depencency.so
    `-- a_php_extension.so
```

### Change the Default Directory

You can change the directory scaned by the Extension Installer by setting the environment variable which controls it in ```.bp_config\options.json```.

Sample setting:
```
    "APP_PHP_EXTENSIONS_DIR": "my-php-extensions"
```
