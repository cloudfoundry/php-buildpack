============================
Rule ``no_mixed_echo_print``
============================

Either language construct ``print`` or ``echo`` should be used.

Configuration
-------------

``use``
~~~~~~~

The desired language construct.

Allowed values: ``'echo'``, ``'print'``

Default value: ``'echo'``

Examples
--------

Example #1
~~~~~~~~~~

*Default* configuration.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1 +1 @@
   -<?php print 'example';
   +<?php echo 'example';

Example #2
~~~~~~~~~~

With configuration: ``['use' => 'print']``.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1 +1 @@
   -<?php echo('example');
   +<?php print('example');

Rule sets
---------

The rule is part of the following rule sets:

@Symfony
  Using the ``@Symfony`` rule set will enable the ``no_mixed_echo_print`` rule with the default config.

@PhpCsFixer
  Using the ``@PhpCsFixer`` rule set will enable the ``no_mixed_echo_print`` rule with the default config.
