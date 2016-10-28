<?php

  $bar = 'I\'m an apcu cached variable';
  apcu_add('foo', $bar);
  var_dump(apcu_fetch('foo'));
  echo "\n";
  $bar = 'NEVER GETS SET';
  apcu_add('foo', $bar);
  var_dump(apcu_fetch('foo'));
  echo "\n";

?>
