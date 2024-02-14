===================================
Rule ``blank_line_after_namespace``
===================================

There MUST be one blank line after the namespace declaration.

Examples
--------

Example #1
~~~~~~~~~~

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,5 +1,4 @@
    <?php
    namespace Sample\Sample;

   -
    $a;

Example #2
~~~~~~~~~~

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,3 +1,4 @@
    <?php
    namespace Sample\Sample;
   +
    Class Test{}

Rule sets
---------

The rule is part of the following rule sets:

@PSR2
  Using the ``@PSR2`` rule set will enable the ``blank_line_after_namespace`` rule.

@Symfony
  Using the ``@Symfony`` rule set will enable the ``blank_line_after_namespace`` rule.

@PhpCsFixer
  Using the ``@PhpCsFixer`` rule set will enable the ``blank_line_after_namespace`` rule.
