==========================================
Rule ``no_trailing_whitespace_in_comment``
==========================================

There MUST be no trailing spaces inside comment or PHPDoc.

Examples
--------

Example #1
~~~~~~~~~~

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,3 +1,3 @@
    <?php
   -// This is 
   -// a comment. 
   +// This is
   +// a comment.

Rule sets
---------

The rule is part of the following rule sets:

@PSR2
  Using the ``@PSR2`` rule set will enable the ``no_trailing_whitespace_in_comment`` rule.

@Symfony
  Using the ``@Symfony`` rule set will enable the ``no_trailing_whitespace_in_comment`` rule.

@PhpCsFixer
  Using the ``@PhpCsFixer`` rule set will enable the ``no_trailing_whitespace_in_comment`` rule.
