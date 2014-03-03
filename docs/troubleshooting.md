## Troubleshooting

The build pack should work in most situations, although nothings perfect so you may need to debug it.  There are a couple easy ways to debug the build pack.

 1. Check the output from the build pack.  It writes some basic information to stdout, like the files that are being downloaded.  Additionally, it will write more information should something fail, specifically you'll see a stack trace explaining why.

 1. Check the logs from the build pack.  The build pack writes logs to disk and you can retrieve them with the `cf files` command.

    ```
    cf files <app> app/.bp/logs/bp.log
    ```

 The output from this log is a little more detailed than what is written to stdout, but does skip some information which might be helpful to understand the state of the build pack when it fails.
 
 1. To get the most information from the build pack, you can put it into debug mode.  To do this, simply set the `BP_DEBUG` environment variable to `true` (or anything really, it just needs to be set).  This will instruct the build pack to set it's log level to DEBUG and it'll write to stdout.  The combination of these two should provide quite a bit of detail about the state of the build pack as it runs.
