===========================
Rule ``no_alias_functions``
===========================

Master functions shall be used instead of aliases.

.. warning:: Using this rule is risky.

   Risky when any of the alias functions are overridden.

Configuration
-------------

``sets``
~~~~~~~~

List of sets to fix. Defined sets are ``@internal`` (native functions),
``@IMAP`` (IMAP functions), ``@mbreg`` (from ``ext-mbstring``) ``@all`` (all
listed sets).

Allowed values: a subset of ``['@internal', '@IMAP', '@mbreg', '@all', '@time', '@exif']``

Default value: ``['@internal', '@IMAP']``

Examples
--------

Example #1
~~~~~~~~~~

*Default* configuration.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,22 +1,22 @@
    <?php
   -$a = chop($b);
   -close($b);
   -$a = doubleval($b);
   -$a = fputs($b, $c);
   -$a = get_required_files();
   -ini_alter($b, $c);
   -$a = is_double($b);
   -$a = is_integer($b);
   -$a = is_long($b);
   -$a = is_real($b);
   -$a = is_writeable($b);
   -$a = join($glue, $pieces);
   -$a = key_exists($key, $array);
   -magic_quotes_runtime($new_setting);
   -$a = pos($array);
   -$a = show_source($filename, true);
   -$a = sizeof($b);
   -$a = strchr($haystack, $needle);
   -$a = imap_header($imap_stream, 1);
   -user_error($message);
   +$a = rtrim($b);
   +closedir($b);
   +$a = floatval($b);
   +$a = fwrite($b, $c);
   +$a = get_included_files();
   +ini_set($b, $c);
   +$a = is_float($b);
   +$a = is_int($b);
   +$a = is_int($b);
   +$a = is_float($b);
   +$a = is_writable($b);
   +$a = implode($glue, $pieces);
   +$a = array_key_exists($key, $array);
   +set_magic_quotes_runtime($new_setting);
   +$a = current($array);
   +$a = highlight_file($filename, true);
   +$a = count($b);
   +$a = strstr($haystack, $needle);
   +$a = imap_headerinfo($imap_stream, 1);
   +trigger_error($message);
    mbereg_search_getregs();

Example #2
~~~~~~~~~~

With configuration: ``['sets' => ['@mbreg']]``.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,3 +1,3 @@
    <?php
    $a = is_double($b);
   -mbereg_search_getregs();
   +mb_ereg_search_getregs();

Rule sets
---------

The rule is part of the following rule sets:

@Symfony:risky
  Using the ``@Symfony:risky`` rule set will enable the ``no_alias_functions`` rule with the default config.

@PhpCsFixer:risky
  Using the ``@PhpCsFixer:risky`` rule set will enable the ``no_alias_functions`` rule with the config below:

  ``['sets' => ['@all']]``

@PHP80Migration:risky
  Using the ``@PHP80Migration:risky`` rule set will enable the ``no_alias_functions`` rule with the config below:

  ``['sets' => ['@all']]``
