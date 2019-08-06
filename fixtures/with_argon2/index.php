hI<?php
    $options = [
        'memory_cost' => 1024,
        'time_cost' => 2
    ];
  print('password hash of "hello-world": ' . password_hash('hello-world!', PASSWORD_ARGON2I, $options));
?>

