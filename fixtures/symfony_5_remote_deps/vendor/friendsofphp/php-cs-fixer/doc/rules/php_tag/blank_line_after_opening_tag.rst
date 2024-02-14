=====================================
Rule ``blank_line_after_opening_tag``
=====================================

Ensure there is no code on the same line as the PHP open tag and it is followed
by a blank line.

Examples
--------

Example #1
~~~~~~~~~~

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,2 +1,4 @@
   -<?php $a = 1;
   +<?php
   +
   +$a = 1;
    $b = 1;

Rule sets
---------

The rule is part of the following rule sets:

@Symfony
  Using the ``@Symfony`` rule set will enable the ``blank_line_after_opening_tag`` rule.

@PhpCsFixer
  Using the ``@PhpCsFixer`` rule set will enable the ``blank_line_after_opening_tag`` rule.
