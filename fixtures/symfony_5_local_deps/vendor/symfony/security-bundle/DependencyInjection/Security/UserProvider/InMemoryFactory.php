<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Bundle\SecurityBundle\DependencyInjection\Security\UserProvider;

use Symfony\Component\Config\Definition\Builder\NodeDefinition;
use Symfony\Component\DependencyInjection\ChildDefinition;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Parameter;

/**
 * InMemoryFactory creates services for the memory provider.
 *
 * @author Fabien Potencier <fabien@symfony.com>
 * @author Christophe Coevoet <stof@notk.org>
 */
class InMemoryFactory implements UserProviderFactoryInterface
{
    /**
     * @return void
     */
    public function create(ContainerBuilder $container, string $id, array $config)
    {
        $definition = $container->setDefinition($id, new ChildDefinition('security.user.provider.in_memory'));
        $defaultPassword = new Parameter('container.build_id');
        $users = [];

        foreach ($config['users'] as $username => $user) {
            $users[$username] = ['password' => null !== $user['password'] ? (string) $user['password'] : $defaultPassword, 'roles' => $user['roles']];
        }

        $definition->addArgument($users);
    }

    /**
     * @return string
     */
    public function getKey()
    {
        return 'memory';
    }

    /**
     * @return void
     */
    public function addConfiguration(NodeDefinition $node)
    {
        $node
            ->fixXmlConfig('user')
            ->children()
                ->arrayNode('users')
                    ->useAttributeAsKey('identifier')
                    ->normalizeKeys(false)
                    ->prototype('array')
                        ->children()
                            ->scalarNode('password')->defaultNull()->end()
                            ->arrayNode('roles')
                                ->beforeNormalization()->ifString()->then(fn ($v) => preg_split('/\s*,\s*/', $v))->end()
                                ->prototype('scalar')->end()
                            ->end()
                        ->end()
                    ->end()
                ->end()
            ->end()
        ;
    }
}
