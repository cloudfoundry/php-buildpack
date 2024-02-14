===============================
Rule ``no_trailing_whitespace``
===============================

Remove trailing whitespace at the end of non-blank lines.

Examples
--------

Example #1
~~~~~~~~~~

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,2 +1,2 @@
    <?php
   -$a = 1;     
   +$a = 1;

Rule sets
---------

The rule is part of the following rule sets:

@PSR2
  Using the ``@PSR2`` rule set will enable the ``no_trailing_whitespace`` rule.

@Symfony
  Using the ``@Symfony`` rule set will enable the ``no_trailing_whitespace`` rule.

@PhpCsFixer
  Using the ``@PhpCsFixer`` rule set will enable the ``no_trailing_whitespace`` rule.
