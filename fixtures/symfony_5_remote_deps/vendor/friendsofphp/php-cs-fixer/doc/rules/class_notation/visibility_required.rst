============================
Rule ``visibility_required``
============================

Visibility MUST be declared on all properties and methods; ``abstract`` and
``final`` MUST be declared before the visibility; ``static`` MUST be declared
after the visibility.

Configuration
-------------

``elements``
~~~~~~~~~~~~

The structural elements to fix (PHP >= 7.1 required for ``const``).

Allowed values: a subset of ``['property', 'method', 'const']``

Default value: ``['property', 'method']``

Examples
--------

Example #1
~~~~~~~~~~

*Default* configuration.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,10 +1,10 @@
    <?php
    class Sample
    {
   -    var $a;
   -    static protected $var_foo2;
   +    public $a;
   +    protected static $var_foo2;

   -    function A()
   +    public function A()
        {
        }
    }

Example #2
~~~~~~~~~~

With configuration: ``['elements' => ['const']]``.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,5 +1,5 @@
    <?php
    class Sample
    {
   -    const SAMPLE = 1;
   +    public const SAMPLE = 1;
    }

Rule sets
---------

The rule is part of the following rule sets:

@PSR2
  Using the ``@PSR2`` rule set will enable the ``visibility_required`` rule with the default config.

@Symfony
  Using the ``@Symfony`` rule set will enable the ``visibility_required`` rule with the default config.

@PhpCsFixer
  Using the ``@PhpCsFixer`` rule set will enable the ``visibility_required`` rule with the default config.

@PHP71Migration
  Using the ``@PHP71Migration`` rule set will enable the ``visibility_required`` rule with the config below:

  ``['elements' => ['const', 'method', 'property']]``

@PHP73Migration
  Using the ``@PHP73Migration`` rule set will enable the ``visibility_required`` rule with the config below:

  ``['elements' => ['const', 'method', 'property']]``

@PHP80Migration
  Using the ``@PHP80Migration`` rule set will enable the ``visibility_required`` rule with the config below:

  ``['elements' => ['const', 'method', 'property']]``
