===================================
Rule ``native_constant_invocation``
===================================

Add leading ``\`` before constant invocation of internal constant to speed up
resolving. Constant name match is case-sensitive, except for ``null``, ``false``
and ``true``.

.. warning:: Using this rule is risky.

   Risky when any of the constants are namespaced or overridden.

Configuration
-------------

``fix_built_in``
~~~~~~~~~~~~~~~~

Whether to fix constants returned by ``get_defined_constants``. User constants
are not accounted in this list and must be specified in the include one.

Allowed types: ``bool``

Default value: ``true``

``include``
~~~~~~~~~~~

List of additional constants to fix.

Allowed types: ``array``

Default value: ``[]``

``exclude``
~~~~~~~~~~~

List of constants to ignore.

Allowed types: ``array``

Default value: ``['null', 'false', 'true']``

``scope``
~~~~~~~~~

Only fix constant invocations that are made within a namespace or fix all.

Allowed values: ``'all'``, ``'namespaced'``

Default value: ``'all'``

Examples
--------

Example #1
~~~~~~~~~~

*Default* configuration.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1 +1 @@
   -<?php var_dump(PHP_VERSION, M_PI, MY_CUSTOM_PI);
   +<?php var_dump(\PHP_VERSION, \M_PI, MY_CUSTOM_PI);

Example #2
~~~~~~~~~~

With configuration: ``['scope' => 'namespaced']``.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1,7 +1,7 @@
    <?php
    namespace space1 {
   -    echo PHP_VERSION;
   +    echo \PHP_VERSION;
    }
    namespace {
        echo M_PI;
    }

Example #3
~~~~~~~~~~

With configuration: ``['include' => ['MY_CUSTOM_PI']]``.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1 +1 @@
   -<?php var_dump(PHP_VERSION, M_PI, MY_CUSTOM_PI);
   +<?php var_dump(\PHP_VERSION, \M_PI, \MY_CUSTOM_PI);

Example #4
~~~~~~~~~~

With configuration: ``['fix_built_in' => false, 'include' => ['MY_CUSTOM_PI']]``.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1 +1 @@
   -<?php var_dump(PHP_VERSION, M_PI, MY_CUSTOM_PI);
   +<?php var_dump(PHP_VERSION, M_PI, \MY_CUSTOM_PI);

Example #5
~~~~~~~~~~

With configuration: ``['exclude' => ['M_PI']]``.

.. code-block:: diff

   --- Original
   +++ New
   @@ -1 +1 @@
   -<?php var_dump(PHP_VERSION, M_PI, MY_CUSTOM_PI);
   +<?php var_dump(\PHP_VERSION, M_PI, MY_CUSTOM_PI);

Rule sets
---------

The rule is part of the following rule sets:

@Symfony:risky
  Using the ``@Symfony:risky`` rule set will enable the ``native_constant_invocation`` rule with the config below:

  ``['fix_built_in' => false, 'include' => ['DIRECTORY_SEPARATOR', 'PHP_SAPI', 'PHP_VERSION_ID'], 'scope' => 'namespaced']``

@PhpCsFixer:risky
  Using the ``@PhpCsFixer:risky`` rule set will enable the ``native_constant_invocation`` rule with the config below:

  ``['fix_built_in' => false, 'include' => ['DIRECTORY_SEPARATOR', 'PHP_SAPI', 'PHP_VERSION_ID'], 'scope' => 'namespaced']``
