## Tips

While I hope the build pack is simple enough to use, here are some tips that can make your experience better.

1. Don't use the `-c` argument with `cf push`.  Setting the command this way overrides the build pack and prevents it from properly configuring the environment for you.  Instead you can use the `ADDITIONAL_PREPROCESS_CMDS` to specify commands that should run prior to your app, like migration scripts, and `APP_START_CMD` to specify an alternate PHP script to run, when running a stand-alone PHP app.

