<?php
// The sessions extension rewrites these directives in the dependency php.ini
// during the supply phase. No session is started here, so no Redis server is
// required for this app to serve.
echo "handler=" . ini_get("session.save_handler") . "|name=" . ini_get("session.name");
