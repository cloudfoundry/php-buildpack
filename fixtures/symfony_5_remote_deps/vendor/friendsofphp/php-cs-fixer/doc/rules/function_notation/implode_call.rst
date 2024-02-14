=====================
Rule ``implode_call``
=====================

Function ``implode`` must be called with 2 arguments in the documented order.

.. warning:: Using this rule is risky.

   Risky when the function ``implode`` is overridden.

Examples
--------

Example #1
~~~~~~~~~~

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,2 +1,2 @@
    <?php
   -implode($pieces, '');
   +implode('', $pieces);

Example #2
~~~~~~~~~~

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,2 +1,2 @@
    <?php
   -implode($pieces);
   +implode('', $pieces);

Rule sets
---------

The rule is part of the following rule sets:

@Symfony:risky
  Using the ``@Symfony:risky`` rule set will enable the ``implode_call`` rule.

@PhpCsFixer:risky
  Using the ``@PhpCsFixer:risky`` rule set will enable the ``implode_call`` rule.

@PHP80Migration:risky
  Using the ``@PHP80Migration:risky`` rule set will enable the ``implode_call`` rule.
