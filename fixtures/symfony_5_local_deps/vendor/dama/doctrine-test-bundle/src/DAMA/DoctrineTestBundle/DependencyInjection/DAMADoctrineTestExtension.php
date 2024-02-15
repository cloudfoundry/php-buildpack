<?php

namespace DAMA\DoctrineTestBundle\DependencyInjection;

use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\HttpKernel\DependencyInjection\Extension;

class DAMADoctrineTestExtension extends Extension
{
    public function load(array $configs, ContainerBuilder $container): void
    {
        $configuration = new Configuration();
        $config = $this->processConfiguration($configuration, $configs);

        $container->setParameter(
            'dama.'.Configuration::STATIC_META_CACHE,
            (bool) $config[Configuration::STATIC_META_CACHE]
        );
        $container->setParameter(
            'dama.'.Configuration::STATIC_QUERY_CACHE,
            (bool) $config[Configuration::STATIC_QUERY_CACHE]
        );
        $container->setParameter(
            'dama.'.Configuration::ENABLE_STATIC_CONNECTION,
            $config[Configuration::ENABLE_STATIC_CONNECTION]
        );
    }
}
