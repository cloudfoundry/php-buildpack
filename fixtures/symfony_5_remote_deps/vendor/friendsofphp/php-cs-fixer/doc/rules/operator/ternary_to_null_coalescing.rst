===================================
Rule ``ternary_to_null_coalescing``
===================================

Use ``null`` coalescing operator ``??`` where possible. Requires PHP >= 7.0.

Examples
--------

Example #1
~~~~~~~~~~

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,2 +1,2 @@
    <?php
   -$sample = isset($a) ? $a : $b;
   +$sample = $a ?? $b;

Rule sets
---------

The rule is part of the following rule sets:

@PHP70Migration
  Using the ``@PHP70Migration`` rule set will enable the ``ternary_to_null_coalescing`` rule.

@PHP71Migration
  Using the ``@PHP71Migration`` rule set will enable the ``ternary_to_null_coalescing`` rule.

@PHP73Migration
  Using the ``@PHP73Migration`` rule set will enable the ``ternary_to_null_coalescing`` rule.

@PHP80Migration
  Using the ``@PHP80Migration`` rule set will enable the ``ternary_to_null_coalescing`` rule.
