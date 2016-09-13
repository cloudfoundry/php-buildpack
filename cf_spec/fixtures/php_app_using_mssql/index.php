This file will show a PDOException in the logs when failing to connect to
an MS SQL Server.

<?php

$username = 'php_mssql_user';
$password = 'php_mssql_password';
$dbname   = 'database_name';
$dbh = new PDO('dblib:localhost;dbname=' . $dbname, $username, $password);

?>
