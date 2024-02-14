<?php


namespace Doctrine\Bundle\MigrationsBundle;

use Doctrine\Bundle\MigrationsBundle\DependencyInjection\CompilerPass\ConfigureDependencyFactoryPass;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\HttpKernel\Bundle\Bundle;

/**
 * Bundle.
 *
 * @author Fabien Potencier <fabien@symfony.com>
 * @author Jonathan H. Wage <jonwage@gmail.com>
 */
class DoctrineMigrationsBundle extends Bundle
{
    public function build(ContainerBuilder $builder)
    {
      $builder->addCompilerPass(new ConfigureDependencyFactoryPass());
    }
}
