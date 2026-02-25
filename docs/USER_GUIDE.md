# PHP Buildpack Features Guide

This guide shows you how to use all the features available in the Cloud Foundry PHP buildpack.

## Table of Contents
- [Getting Started](#getting-started)
- [Web Servers](#web-servers)
- [PHP Configuration](#php-configuration)
- [PHP Extensions](#php-extensions)
- [Composer and Dependencies](#composer-and-dependencies)
- [Application Monitoring](#application-monitoring)
- [Session Storage](#session-storage)
- [Popular Frameworks](#popular-frameworks)
- [Advanced Features](#advanced-features)

---

## Getting Started

### Deploying a Basic PHP Application

1. Create a basic PHP application:
```bash
mkdir my-php-app
cd my-php-app
echo "<?php phpinfo(); ?>" > index.php
```

2. Deploy to Cloud Foundry:
```bash
cf push my-app
```

That's it! The buildpack automatically:
- Detects your PHP application
- Installs PHP and Apache HTTPD
- Configures PHP-FPM
- Serves your application

### Directory Structure

```
my-app/
├── index.php                    # Your application code
├── .bp-config/                  # Buildpack configuration (optional)
│   ├── options.json            # General settings
│   ├── php/
│   │   ├── php.ini             # Custom PHP settings
│   │   ├── php.ini.d/          # Additional PHP config
│   │   └── fpm.d/              # PHP-FPM pool config
│   ├── httpd/                  # Apache configuration
│   └── nginx/                  # Nginx configuration
├── composer.json                # Dependencies
└── htdocs/                     # Custom web root (optional)
```

---

## Web Servers

### Apache HTTPD (Default)

Apache HTTPD is used by default. No configuration needed!

**Custom Configuration:**

Create `.bp-config/options.json`:
```json
{
  "WEB_SERVER": "httpd"
}
```

**Custom Apache Modules:**

Create `.bp-config/httpd/extra/httpd-modules.conf`:
```apache
# Load additional modules
LoadModule rewrite_module modules/mod_rewrite.so
LoadModule headers_module modules/mod_headers.so
```

**Custom Apache Configuration:**

Create `.bp-config/httpd/httpd.conf` to override the default configuration, or add files to `.bp-config/httpd/extra/` to extend it.

**Example - Enable mod_rewrite:**
```apache
# .bp-config/httpd/extra/rewrite.conf
<Directory "@{HOME}/@{WEBDIR}">
    RewriteEngine On
    RewriteBase /
    RewriteCond %{REQUEST_FILENAME} !-f
    RewriteRule ^ index.php [QSA,L]
</Directory>
```

---

### Nginx

Switch to Nginx by creating `.bp-config/options.json`:
```json
{
  "WEB_SERVER": "nginx"
}
```

**Custom Nginx Configuration:**

Create `.bp-config/nginx/server.conf`:
```nginx
# Custom location blocks
location / {
    try_files $uri $uri/ /index.php?$query_string;
}

location ~ \.php$ {
    fastcgi_pass unix:@{PHP_FPM_LISTEN};
    fastcgi_param SCRIPT_FILENAME @{HOME}/@{WEBDIR}$fastcgi_script_name;
    include fastcgi_params;
}
```

**Upload Size Configuration:**
```nginx
# .bp-config/nginx/server.conf
client_max_body_size 100M;
```

---

### No Web Server (PHP-FPM Only)

For multi-buildpack scenarios or when using an external web server:

```json
{
  "WEB_SERVER": "none"
}
```

PHP-FPM will listen on `127.0.0.1:9000` for FastCGI connections.

---

## PHP Configuration

### Selecting PHP Version

**Option 1: Via composer.json (Recommended)**
```json
{
  "require": {
    "php": "^8.2"
  }
}
```

**Option 2: Via .bp-config/options.json**
```json
{
  "PHP_VERSION": "8.2.x"
}
```

**Available Versions:**
- PHP 8.3.x
- PHP 8.2.x
- PHP 8.1.x

---

### Custom php.ini Settings

Create `.bp-config/php/php.ini`:
```ini
[PHP]
memory_limit = 256M
upload_max_filesize = 50M
post_max_size = 50M
max_execution_time = 60

date.timezone = "America/New_York"

display_errors = Off
error_reporting = E_ALL & ~E_DEPRECATED & ~E_STRICT
```

---

### Additional PHP Configuration

For modular configuration, use `.bp-config/php/php.ini.d/`:

**Example - Custom Include Path:**
```ini
; .bp-config/php/php.ini.d/custom-paths.ini
include_path = ".:/usr/share/php:@{HOME}/lib"
```

**Example - Error Logging:**
```ini
; .bp-config/php/php.ini.d/logging.ini
error_log = /home/vcap/logs/php_errors.log
log_errors = On
```

---

### PHP-FPM Configuration

**Custom FPM Pool Settings:**

Create `.bp-config/php/fpm.d/custom.conf`:
```ini
[www]
; Worker process settings
pm = dynamic
pm.max_children = 20
pm.start_servers = 5
pm.min_spare_servers = 5
pm.max_spare_servers = 10

; Environment variables for your application
env[DB_HOST] = ${DB_HOST}
env[DB_PORT] = ${DB_PORT}
env[REDIS_URL] = ${REDIS_URL}

; Application paths
env[APP_ENV] = production
env[APP_DEBUG] = false
```

**Expose Environment Variables to PHP:**
```ini
; .bp-config/php/fpm.d/env.conf
[www]
; Pass Cloud Foundry environment variables
env[VCAP_SERVICES] = ${VCAP_SERVICES}
env[VCAP_APPLICATION] = ${VCAP_APPLICATION}
env[CF_INSTANCE_INDEX] = ${CF_INSTANCE_INDEX}
```

---

## PHP Extensions

### Installing Extensions

**Method 1: Via composer.json (Recommended)**
```json
{
  "require": {
    "php": "^8.2",
    "ext-mbstring": "*",
    "ext-pdo": "*",
    "ext-pdo_mysql": "*",
    "ext-redis": "*",
    "ext-apcu": "*",
    "ext-intl": "*"
  }
}
```

**Method 2: Via .bp-config/options.json**
```json
{
  "PHP_EXTENSIONS": [
    "mbstring",
    "pdo",
    "pdo_mysql",
    "redis",
    "apcu"
  ]
}
```

---

### Popular Extensions

#### Redis (phpredis)

**Installation:**
```json
{
  "require": {
    "ext-redis": "*"
  }
}
```

**Usage:**
```php
<?php
$redis = new Redis();
$redis->connect('127.0.0.1', 6379);
$redis->set('key', 'value');
echo $redis->get('key');
?>
```

---

#### APCu (User Cache)

**Installation:**
```json
{
  "require": {
    "ext-apcu": "*"
  }
}
```

**Usage:**
```php
<?php
// Store data
apcu_store('my_key', 'my_value', 3600);

// Retrieve data
$value = apcu_fetch('my_key');
?>
```

---

#### AMQP (RabbitMQ)

**Installation:**
```json
{
  "require": {
    "ext-amqp": "*"
  }
}
```

**Usage:**
```php
<?php
$connection = new AMQPConnection([
    'host' => 'localhost',
    'port' => 5672,
    'vhost' => '/',
    'login' => 'guest',
    'password' => 'guest'
]);
$connection->connect();
?>
```

---

### All Available Extensions

Standard PHP extensions available:
- **Database:** mysqli, pdo, pdo_mysql, pdo_pgsql, pdo_sqlite, pgsql
- **Caching:** apcu, opcache
- **Compression:** bz2, zip, zlib
- **Crypto:** openssl, sodium
- **Encoding:** mbstring, iconv
- **Image:** gd, exif
- **International:** intl, gettext
- **Math:** bcmath, gmp
- **Network:** curl, ftp, sockets
- **Text:** xml, xmlreader, xmlwriter, simplexml, dom, xsl
- **Web:** soap, json
- And many more!

---

## Composer and Dependencies

### Basic Composer Usage

The buildpack automatically detects `composer.json` and runs `composer install`.

**Example composer.json:**
```json
{
  "require": {
    "php": "^8.2",
    "monolog/monolog": "^3.0",
    "guzzlehttp/guzzle": "^7.0"
  }
}
```

---

### Custom Vendor Directory

```json
{
  "config": {
    "vendor-dir": "lib/vendor"
  }
}
```

Or set via environment variable:
```bash
cf set-env myapp COMPOSER_VENDOR_DIR lib/vendor
```

---

### GitHub Rate Limiting

Avoid GitHub API rate limits by providing an OAuth token:

```bash
cf set-env myapp COMPOSER_GITHUB_OAUTH_TOKEN your-github-token
cf restage myapp
```

---

### Custom Composer Location

If your `composer.json` is not in the root:

```bash
cf set-env myapp COMPOSER_PATH src/
cf restage myapp
```

---

## Application Monitoring

### NewRelic

**Setup:**
1. Create a NewRelic service:
```bash
cf create-service newrelic standard my-newrelic
```

2. Bind to your application:
```bash
cf bind-service myapp my-newrelic
cf restage myapp
```

That's it! NewRelic is automatically configured.

**Custom Configuration:**
```bash
cf set-env myapp NEWRELIC_LICENSE your-license-key
cf restage myapp
```

---

### AppDynamics

**Setup:**
1. Create an AppDynamics service or use a user-provided service:
```bash
cf cups my-appdynamics -p '{"account-name":"your-account","account-access-key":"your-key","host-name":"controller.example.com","port":"443","ssl-enabled":true}'
```

2. Bind to your application:
```bash
cf bind-service myapp my-appdynamics
cf restage myapp
```

**Custom Configuration:**
```bash
cf set-env myapp APPD_TIER_NAME web
cf set-env myapp APPD_NODE_NAME web-1
```

---

### Dynatrace

Bind a Dynatrace service to enable monitoring:
```bash
cf bind-service myapp my-dynatrace
cf restage myapp
```

---

## Session Storage

### Redis Sessions

**Automatic Configuration:**
1. Bind a Redis service:
```bash
cf bind-service myapp my-redis
cf restage myapp
```

The buildpack automatically configures PHP sessions to use Redis!

**Manual Configuration:**
```ini
; .bp-config/php/php.ini
session.save_handler = redis
session.save_path = "tcp://localhost:6379"
```

---

### Memcached Sessions

**Automatic Configuration:**
1. Bind a Memcached service:
```bash
cf bind-service myapp my-memcached
cf restage myapp
```

Sessions automatically use Memcached!

---

## Popular Frameworks

### CakePHP

**composer.json:**
```json
{
  "require": {
    "php": "^8.2",
    "cakephp/cakephp": "^5.0"
  }
}
```

**Procfile (for migrations):**
```
web: php artisan migrate --force && $HOME/.bp/bin/start
```

---

### Laravel

**composer.json:**
```json
{
  "require": {
    "php": "^8.2",
    "laravel/framework": "^10.0"
  }
}
```

**Run migrations on startup:**

Create `.bp-config/options.json`:
```json
{
  "WEBDIR": "public",
  "ADDITIONAL_PREPROCESS_CMDS": [
    "php artisan migrate --force",
    "php artisan cache:clear",
    "php artisan config:cache"
  ]
}
```

---

### Symfony

**composer.json:**
```json
{
  "require": {
    "php": "^8.2",
    "symfony/framework-bundle": "^6.0"
  }
}
```

**Set web directory:**
```json
{
  "WEBDIR": "public"
}
```

---

### Laminas (Zend Framework)

**composer.json:**
```json
{
  "require": {
    "php": "^8.2",
    "laminas/laminas-mvc": "^3.0"
  }
}
```

Works out of the box!

---

## Advanced Features

### Custom Web Directory

If your application code is in a subdirectory:

```json
{
  "WEBDIR": "public"
}
```

Or:
```json
{
  "WEBDIR": "web"
}
```

The buildpack automatically moves your app into this directory.

---

### Preprocess Commands

Run commands before your application starts (migrations, cache warming, etc.):

```json
{
  "ADDITIONAL_PREPROCESS_CMDS": [
    "php artisan migrate --force",
    "php bin/console cache:warmup",
    "chmod -R 777 storage"
  ]
}
```

**Common Use Cases:**
- Database migrations
- Cache warming
- Asset compilation
- Directory permissions

---

### Standalone PHP Applications

Run PHP applications without a web server (workers, CLI apps):

```json
{
  "WEB_SERVER": "none",
  "APP_START_CMD": "php worker.php"
}
```

**Examples:**
- Queue workers
- Cron-like tasks
- Background processors
- Long-running scripts

---

### Environment Variables in Configuration

Use environment variables in your configuration files:

**PHP-FPM Configuration:**
```ini
; .bp-config/php/fpm.d/env.conf
[www]
env[DATABASE_URL] = ${DATABASE_URL}
env[REDIS_URL] = ${REDIS_URL}
env[APP_SECRET] = ${APP_SECRET}
```

**Nginx Configuration:**
```nginx
# PORT is replaced at runtime
server {
    listen ${PORT};
    # ...
}
```

---

### Service Bindings (VCAP_SERVICES)

Access bound service credentials in your PHP code:

```php
<?php
// Get VCAP_SERVICES
$vcap_services = json_decode(getenv('VCAP_SERVICES'), true);

// Access MySQL credentials
$mysql = $vcap_services['mysql'][0]['credentials'];
$host = $mysql['hostname'];
$port = $mysql['port'];
$user = $mysql['username'];
$pass = $mysql['password'];
$dbname = $mysql['name'];

// Connect to database
$pdo = new PDO(
    "mysql:host=$host;port=$port;dbname=$dbname",
    $user,
    $pass
);
?>
```

**For more complex parsing, create a helper class:**
```php
<?php
class VcapParser {
    private $services;
    
    public function __construct() {
        $this->services = json_decode(getenv('VCAP_SERVICES'), true) ?: [];
    }
    
    public function getCredentials($serviceType) {
        return $this->services[$serviceType][0]['credentials'] ?? null;
    }
}

// Usage
$vcap = new VcapParser();
$db = $vcap->getCredentials('mysql');
?>
```

---

### Multi-Buildpack Support

Use PHP with other buildpacks:

**manifest.yml:**
```yaml
applications:
- name: my-app
  buildpacks:
    - https://github.com/cloudfoundry/nodejs-buildpack
    - https://github.com/cloudfoundry/php-buildpack
  # Node.js for asset compilation, PHP for runtime
```

**Use Cases:**
- Node.js for frontend asset compilation
- .NET for legacy components
- Custom buildpacks for specialized tools

---

## Configuration Reference

### .bp-config/options.json

Complete reference of available options:

```json
{
  "PHP_VERSION": "8.2.x",
  "WEB_SERVER": "httpd",
  "WEBDIR": "htdocs",
  "LIBDIR": "lib",
  "COMPOSER_VENDOR_DIR": "vendor",
  "ADMIN_EMAIL": "admin@example.com",
  "ADDITIONAL_PREPROCESS_CMDS": [],
  "APP_START_CMD": null,
  "PHP_EXTENSIONS": []
}
```

**Options:**
- `PHP_VERSION` - PHP version to install (e.g., "8.2.x", "8.1.27")
- `WEB_SERVER` - Web server choice: "httpd", "nginx", or "none"
- `WEBDIR` - Document root directory (default: "htdocs")
- `LIBDIR` - Library directory (default: "lib")
- `COMPOSER_VENDOR_DIR` - Composer vendor directory
- `ADMIN_EMAIL` - Server admin email
- `ADDITIONAL_PREPROCESS_CMDS` - Commands to run before app starts
- `APP_START_CMD` - Custom start command (for standalone apps)
- `PHP_EXTENSIONS` - List of PHP extensions (prefer composer.json)

---

## Troubleshooting

### View Application Logs

```bash
cf logs myapp --recent
```

### Check PHP Version

```php
<?php phpinfo(); ?>
```

### Verify Loaded Extensions

```php
<?php
print_r(get_loaded_extensions());
?>
```

### Debug Composer Issues

```bash
cf set-env myapp COMPOSER_DEBUG 1
cf restage myapp
```

### Common Issues

**"Extension not found"**
- Ensure extension is listed in composer.json or options.json
- Check manifest.yml for available extensions

**"Session errors"**
- Verify Redis/Memcached service is bound
- Check session configuration in php.ini

**"Upload size limit"**
- Increase `upload_max_filesize` and `post_max_size` in php.ini
- For Nginx, also set `client_max_body_size`

**"Memory limit exceeded"**
- Increase `memory_limit` in php.ini
- Check application memory quota: `cf app myapp`

---

## Getting Help

- **Documentation:** https://docs.cloudfoundry.org/buildpacks/php/
- **GitHub Issues:** https://github.com/cloudfoundry/php-buildpack/issues
- **Slack:** #buildpacks on cloudfoundry.slack.com

---

## Next Steps

- [VCAP_SERVICES Usage Guide](VCAP_SERVICES_USAGE.md) - Working with service bindings
- [Migration Guide](REWRITE_MIGRATION.md) - Migrating from PHP buildpack v4.x
- [Architecture Overview](BUILDPACK_COMPARISON.md) - How the buildpack works

