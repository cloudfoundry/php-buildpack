==============================
Rule ``pow_to_exponentiation``
==============================

Converts ``pow`` to the ``**`` operator.

.. warning:: Using this rule is risky.

   Risky when the function ``pow`` is overridden.

Examples
--------

Example #1
~~~~~~~~~~

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,2 +1,2 @@
    <?php
   - pow($a, 1);
   + $a** 1;

Rule sets
---------

The rule is part of the following rule sets:

@PHP56Migration:risky
  Using the ``@PHP56Migration:risky`` rule set will enable the ``pow_to_exponentiation`` rule.

@PHP70Migration:risky
  Using the ``@PHP70Migration:risky`` rule set will enable the ``pow_to_exponentiation`` rule.

@PHP71Migration:risky
  Using the ``@PHP71Migration:risky`` rule set will enable the ``pow_to_exponentiation`` rule.

@PHP80Migration:risky
  Using the ``@PHP80Migration:risky`` rule set will enable the ``pow_to_exponentiation`` rule.
