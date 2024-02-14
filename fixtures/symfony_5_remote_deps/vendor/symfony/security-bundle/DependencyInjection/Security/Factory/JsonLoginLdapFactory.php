<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Bundle\SecurityBundle\DependencyInjection\Security\Factory;

use Symfony\Component\Config\Definition\Builder\NodeDefinition;
use Symfony\Component\DependencyInjection\ChildDefinition;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Reference;
use Symfony\Component\Security\Core\Exception\LogicException;

/**
 * JsonLoginLdapFactory creates services for json login ldap authentication.
 *
 * @internal
 */
class JsonLoginLdapFactory extends JsonLoginFactory
{
    use LdapFactoryTrait;

    public function getKey()
    {
        return 'json-login-ldap';
    }

    protected function createAuthProvider(ContainerBuilder $container, string $id, array $config, string $userProviderId)
    {
        $provider = 'security.authentication.provider.ldap_bind.'.$id;
        $definition = $container
            ->setDefinition($provider, new ChildDefinition('security.authentication.provider.ldap_bind'))
            ->replaceArgument(0, new Reference($userProviderId))
            ->replaceArgument(1, new Reference('security.user_checker.'.$id))
            ->replaceArgument(2, $id)
            ->replaceArgument(3, new Reference($config['service']))
            ->replaceArgument(4, $config['dn_string'])
            ->replaceArgument(6, $config['search_dn'])
            ->replaceArgument(7, $config['search_password'])
        ;

        if (!empty($config['query_string'])) {
            if ('' === $config['search_dn'] || '' === $config['search_password']) {
                throw new LogicException('Using the "query_string" config without using a "search_dn" and a "search_password" is not supported.');
            }
            $definition->addMethodCall('setQueryString', [$config['query_string']]);
        }

        return $provider;
    }

    public function addConfiguration(NodeDefinition $node)
    {
        parent::addConfiguration($node);

        $node
            ->children()
                ->scalarNode('service')->defaultValue('ldap')->end()
                ->scalarNode('dn_string')->defaultValue('{username}')->end()
                ->scalarNode('query_string')->end()
                ->scalarNode('search_dn')->defaultValue('')->end()
                ->scalarNode('search_password')->defaultValue('')->end()
            ->end()
        ;
    }
}
