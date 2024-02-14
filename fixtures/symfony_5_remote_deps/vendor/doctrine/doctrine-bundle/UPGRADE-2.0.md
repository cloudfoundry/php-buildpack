UPGRADE FROM 1.x to 2.0
=======================

PHP and Symfony version support
-------------------------------

 * Support for PHP 5.5, 5.6 and 7.0 was dropped
 * Support for unsupported Symfony versions was dropped. The bundle now supports
   Symfony 3.4 LTS and 4.1 or newer.
 * Support for Twig 1.34 and below as well as 2.4 and below (for 2.x) releases
   was dropped.
 * When no charset parameter is defined, it now defaults to `utf8mb4` on the
   MySQL platform and to `utf8` on all other platforms.

Commands
--------

 * `Doctrine\Bundle\DoctrineBundle\Command` requires a `ManagerRegistry`
   instance when instantiating.
 * Dropped `setContainer` and `getContainer` in
   `Doctrine\Bundle\DoctrineBundle\Command`.
 * `Doctrine\Bundle\DoctrineBundle\Command` no longer implements
   `ContainerAwareInterface`.
 * `Doctrine\Bundle\DoctrineBundle\Command\GenerateEntitiesDoctrineCommand` was
   dropped in favour of the MakerBundle.

Deprecation of DoctrineCacheBundle
----------------------------------

Configuring caches through DoctrineCacheBundle is no longer possible. Please use
symfony/cache through the `pool` type or configure your cache services manually
and use the `service` type.

Mapping
-------

 * Dropped `ContainerAwareEntityListenerResolver`, use
   `ContainerEntityListenerResolver` instead.

Registry
--------

 * `Registry` no longer implements `Symfony\Bridge\Doctrine\RegistryInterface`.
 * Removed all deprecated entity manager specific methods from the registry.

Service aliases
---------------

 * The `Symfony\Bridge\Doctrine\RegistryInterface` interface is no longer aliased
   to the `doctrine` service, use `Doctrine\Common\Persistence\ManagerRegistry`
   instead.
 * The `Doctrine\Common\Persistence\ObjectManager` interface is no longer
   aliased to the `doctrine.orm.entity_manager` service, use
   `Doctrine\ORM\EntityManagerInterface` instead.

Types
-----

 * Marking types as commented in the configuration is no longer supported.
   Instead, mark them commented using the `requiresSQLCommentHint()` method of
   the type.
 * The `commented` configuration option for types will be dropped in a future
   release. You should not use it.

UnitOfWork cleared between each request
---------------------------------------
If all of these are true:
* You call `Symfony\Bundle\FrameworkBundle\Client::disableReboot()` in your test case
* Trigger multiple HTTP requests (via `Symfony\Bundle\FrameworkBundle\Client::request()` etc.) within your test case
* Your test case relies on Doctrine ORM keeping references to old entities between requests (this is most obvious when calling `Doctrine\Persistence\ObjectManager::refresh`)

Your test case will fail since `DoctrineBundle` 2.0.3, as identity map is now cleared between each request 
to better simulate real requests and avoid memory leaks. You have two options to solve this:

1. Change your test cases with new behaviour in mind. In a lot of cases this just means to replace `ObjectManager::refresh($entity)` with `$entity = ObjectManager::find($entity->getId())`. This is the recommended solution.
2. Write a compiler pass which restores old behaviour, e.g. by adding the following to your `Kernel` class:
```php
protected function build(\Symfony\Component\DependencyInjection\ContainerBuilder $container)
{
    parent::build($container);

    if ($this->environment === 'test') {
        $container->addCompilerPass(new class implements \Symfony\Component\DependencyInjection\Compiler\CompilerPassInterface {
            public function process(\Symfony\Component\DependencyInjection\ContainerBuilder $container)
            {
                $container->getDefinition('doctrine')->clearTag('kernel.reset');
            }
        }, \Symfony\Component\DependencyInjection\Compiler\PassConfig::TYPE_BEFORE_OPTIMIZATION, 1);
    }
}
```
