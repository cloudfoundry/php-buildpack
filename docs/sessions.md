## Sessions

When your application has one instance, it's mostly safe to use the default session storage, which is the local file system.  You would only see problems if your single instance crashes as the local file system would go away and you'd lose your sessions.  For many applications, this will work just fine but please consider how this will impact your application.

If you have multiple application instances or you need a more robust solution for your application, then you'll want to use Redis or Memcached as a backing store for your session data.  The build pack supports both and when one is bound to your application it will detected it and automatically configure PHP to use it for session storage.

### Usage

By default, there's no configuration necessary.  Simple create a Redis service, make sure the service name contains `redis-sessions` and then bind the service to the application.

Ex:

```
cf create-service redis some-plan app-redis-sessions
cf bind-service app app-redis-sessions
cf restage app
```

If you want to use a specific service instance or change the search key, you can do that by setting `REDIS_SESSION_STORE_SERVICE_NAME` in `.bp-config/options.json` to the new search key.  The session configuration extension will then search the bound services by name for the new session key.

### Configuration Changes

When detected, the following changes will be made.

#### Redis

  - the `redis` PHP extension will be installed, which provides the session save handler
  - `session.name` will be set to `PHPSESSIONID` this disables sticky sessions
  - `session.save_handler` is configured to `redis`
  - `session.save_path` is configured based on the bound credentials (i.e. `tcp://host:port?auth=pass`)
