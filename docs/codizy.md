## Codizy

The Codizy extension for this buildpack adds all of the needed prerequisites to have [Codizy] working!

### About Codizy

Codizy is an ALL-IN-ONE software designed to optimize PHP / MySQL applications, that includes 4 main features:
1 - Monitoring : checks application performance
2 - Analysis : finds and prioritize problems
3 - Profiling : detects PHP performance issues, regressions and buggy code
4 - Optimization : fixes MySQL tables with new index and rewrites MySQL queries

Codizy has been designed to fit in any type of environment:
- PHP development : including Frameworks (eg: Symfony, Zend Framwork, Yii, Codelgniter, Cake PHP...) and CMS (eg: Drupal, Joomla, Wordpress, Magento, OS Commerce, Prestashop ...)
- MySQL Server : MySQL, MariaDB, Percona...

For more information, please see the [Codizy] site.

### Configuration

No manual configuration is needed.  The Codizy build pack extension will take care of installing required extensions and adjusting `php.ini`.

### Usage

Codizy will be automatically enabled if you bind a service named `codizy` to your application.  Otherwise you can manually enable it by setting `CODIZY_INSTALL` to `True` in either `.bp-config/options.json` or in your application's `manifest.yml` file.

Once the Codizy service is enable, just add `?Codizy=on` to the query string of any URL served by PHP.

  - You'll be prompted to create a new Codizy Account or use an existing one
  - Once logged in, a trial version of Codizy will be downloaded
  - Then create a local Codizy account, and you'll access to full power of Codizy

For more information about how to use Codizy efficiently, see the [User Guide].

### Platform support

Codizy and it's required extensions currently PHP 5.4.x & 5.5.x on x86_64 Linux.  The current exception is with PHP 5.4.33 and 5.5.17.  These versions contain a [bug] which impacts features required by Codizy.  Please avoid using either of these versions of PHP with Codizy.


[Codizy]:http://www.codizy.com
[User Guide]:http://doc.codizy.com:8090/display/UG/User+guide
[bug]:https://bugs.php.net/bug.php?id=41631
