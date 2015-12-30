## Troubleshooting

The buildpack should work in most situations. If not, there are a couple easy ways to diagnose problems.

 1. Check the output from the buildpack.  It writes some basic information to stdout, like the files that are being downloaded.  Additionally, it will write more information should something fail, specifically you'll see a stack trace explaining why.

 2. Check the logs from the buildpack.  The buildpack writes logs to disk and you can retrieve them with the `cf files` command.

    ```bash
    cf files <app> app/.bp/logs/bp.log
    ```

 The output from this log is a little more detailed than what is written to stdout, but does skip some information which might be helpful to understand the state of the buildpack when it fails.

### Enable Debug Mode

To get the most information from the buildpack, you can put it into debug mode.  To do this, simply set the `BP_DEBUG` environment variable to `true` (or anything really, it just needs to be set).  This will instruct the buildpack to set it's log level to DEBUG and it'll write to stdout.  The combination of these two should provide quite a bit of detail about the state of the buildpack as it runs.

```bash
cf se <app> BP_DEBUG true
```

**NOTE:** if you enable debug logging it might include sensitive information like usernames, passwords, tokens, service info and file names from your application. Be careful where you post those logs and if necessary, redact any sensitive information first.
