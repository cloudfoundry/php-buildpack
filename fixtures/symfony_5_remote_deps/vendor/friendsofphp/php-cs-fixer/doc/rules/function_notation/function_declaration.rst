=============================
Rule ``function_declaration``
=============================

Spaces should be properly placed in a function declaration.

Configuration
-------------

``closure_function_spacing``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Spacing to use before open parenthesis for closures.

Allowed values: ``'none'``, ``'one'``

Default value: ``'one'``

Examples
--------

Example #1
~~~~~~~~~~

*Default* configuration.

.. code-block:: diff

   --- Original
   +++ New
   @@ -2,13 +2,13 @@

    class Foo
    {
   -    public static function  bar   ( $baz , $foo )
   +    public static function bar($baz , $foo)
        {
            return false;
        }
    }

   -function  foo  ($bar, $baz)
   +function foo($bar, $baz)
    {
        return false;
    }

Example #2
~~~~~~~~~~

With configuration: ``['closure_function_spacing' => 'none']``.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,2 +1,2 @@
    <?php
   -$f = function () {};
   +$f = function() {};

Example #3
~~~~~~~~~~

With configuration: ``['closure_function_spacing' => 'none']``.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,2 +1,2 @@
    <?php
   -$f = fn () => null;
   +$f = fn() => null;

Rule sets
---------

The rule is part of the following rule sets:

@PSR2
  Using the ``@PSR2`` rule set will enable the ``function_declaration`` rule with the default config.

@Symfony
  Using the ``@Symfony`` rule set will enable the ``function_declaration`` rule with the default config.

@PhpCsFixer
  Using the ``@PhpCsFixer`` rule set will enable the ``function_declaration`` rule with the default config.
