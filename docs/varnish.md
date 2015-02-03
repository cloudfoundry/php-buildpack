## Varnish

This buildpack supports varnish. Either as caching proxy in front of nginx/httpd directly in the buildpack or standalone with just varnish. You can also run just varnish and for example run a PHP "daemon" which listens to a rabbitmq for commands to be done (like clearing the cache)

|      Variable     |   Explanation                                        |
------------------- | -----------------------------------------------------|
| CACHE_SERVER      | If varnish should be used. The only possible option is "varnish"  |


### Configuration

All your varnish config files should go into .bp-config/varnish

### Varnish in front of nginx/http

Just set CACHE_SERVER in .bp-config/options.json and provide the correct varnish config and your done. The backend listens on port 8080 in this case

### Just Varnish and nothing else

If you have your backends on other apps, you can run just varnish, do this in .bp-config/options.json:

```
"PHP_VM": "none",
"WEB_SERVER": "none",
"CACHE_SERVER": "varnish"
```

### Varnish with a PHP daemon in the background

(concrete example will follow)

```
"PHP_VM": "php",
"WEB_SERVER": "none",
"CACHE_SERVER": "varnish",
"PHP_MODULES": ["cli"],
```

and add a file named _app.php_,  _main.php_, _run.php_ or _start.php_ into your root

or adjust _APP_START_CMD_
