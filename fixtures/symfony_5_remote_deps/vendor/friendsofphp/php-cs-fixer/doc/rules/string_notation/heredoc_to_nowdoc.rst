==========================
Rule ``heredoc_to_nowdoc``
==========================

Convert ``heredoc`` to ``nowdoc`` where possible.

Examples
--------

Example #1
~~~~~~~~~~

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,3 +1,3 @@
   -<?php $a = <<<"TEST"
   +<?php $a = <<<'TEST'
    Foo
    TEST;

Rule sets
---------

The rule is part of the following rule set:

@PhpCsFixer
  Using the ``@PhpCsFixer`` rule set will enable the ``heredoc_to_nowdoc`` rule.
