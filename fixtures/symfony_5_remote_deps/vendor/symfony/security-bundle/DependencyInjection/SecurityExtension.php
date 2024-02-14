<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Bundle\SecurityBundle\DependencyInjection;

use Symfony\Bundle\SecurityBundle\DependencyInjection\Security\Factory\AuthenticatorFactoryInterface;
use Symfony\Bundle\SecurityBundle\DependencyInjection\Security\Factory\EntryPointFactoryInterface;
use Symfony\Bundle\SecurityBundle\DependencyInjection\Security\Factory\RememberMeFactory;
use Symfony\Bundle\SecurityBundle\DependencyInjection\Security\Factory\SecurityFactoryInterface;
use Symfony\Bundle\SecurityBundle\DependencyInjection\Security\UserProvider\UserProviderFactoryInterface;
use Symfony\Bundle\SecurityBundle\Security\LegacyLogoutHandlerListener;
use Symfony\Bundle\SecurityBundle\SecurityUserValueResolver;
use Symfony\Component\Config\Definition\Exception\InvalidConfigurationException;
use Symfony\Component\Config\FileLocator;
use Symfony\Component\Console\Application;
use Symfony\Component\DependencyInjection\Alias;
use Symfony\Component\DependencyInjection\Argument\IteratorArgument;
use Symfony\Component\DependencyInjection\Argument\ServiceClosureArgument;
use Symfony\Component\DependencyInjection\ChildDefinition;
use Symfony\Component\DependencyInjection\Compiler\ServiceLocatorTagPass;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Definition;
use Symfony\Component\DependencyInjection\Extension\PrependExtensionInterface;
use Symfony\Component\DependencyInjection\Loader\XmlFileLoader;
use Symfony\Component\DependencyInjection\Reference;
use Symfony\Component\EventDispatcher\EventDispatcher;
use Symfony\Component\HttpKernel\DependencyInjection\Extension;
use Symfony\Component\Ldap\Entry;
use Symfony\Component\Security\Core\Authorization\Voter\VoterInterface;
use Symfony\Component\Security\Core\Encoder\NativePasswordEncoder;
use Symfony\Component\Security\Core\Encoder\SodiumPasswordEncoder;
use Symfony\Component\Security\Core\User\ChainUserProvider;
use Symfony\Component\Security\Core\User\UserProviderInterface;
use Symfony\Component\Security\Http\Controller\UserValueResolver;
use Symfony\Component\Security\Http\EntryPoint\AuthenticationEntryPointInterface;
use Twig\Extension\AbstractExtension;

/**
 * SecurityExtension.
 *
 * @author Fabien Potencier <fabien@symfony.com>
 * @author Johannes M. Schmitt <schmittjoh@gmail.com>
 */
class SecurityExtension extends Extension implements PrependExtensionInterface
{
    private $requestMatchers = [];
    private $expressions = [];
    private $contextListeners = [];
    private $listenerPositions = ['pre_auth', 'form', 'http', 'remember_me', 'anonymous'];
    private $factories = [];
    private $userProviderFactories = [];
    private $statelessFirewallKeys = [];

    private $authenticatorManagerEnabled = false;

    public function __construct()
    {
        foreach ($this->listenerPositions as $position) {
            $this->factories[$position] = [];
        }
    }

    public function prepend(ContainerBuilder $container)
    {
        $rememberMeSecureDefault = false;
        $rememberMeSameSiteDefault = null;

        if (!isset($container->getExtensions()['framework'])) {
            return;
        }
        foreach ($container->getExtensionConfig('framework') as $config) {
            if (isset($config['session']) && \is_array($config['session'])) {
                $rememberMeSecureDefault = $config['session']['cookie_secure'] ?? $rememberMeSecureDefault;
                $rememberMeSameSiteDefault = \array_key_exists('cookie_samesite', $config['session']) ? $config['session']['cookie_samesite'] : $rememberMeSameSiteDefault;
            }
        }
        foreach ($this->listenerPositions as $position) {
            foreach ($this->factories[$position] as $factory) {
                if ($factory instanceof RememberMeFactory) {
                    \Closure::bind(function () use ($rememberMeSecureDefault, $rememberMeSameSiteDefault) {
                        $this->options['secure'] = $rememberMeSecureDefault;
                        $this->options['samesite'] = $rememberMeSameSiteDefault;
                    }, $factory, $factory)();
                }
            }
        }
    }

    public function load(array $configs, ContainerBuilder $container)
    {
        if (!array_filter($configs)) {
            return;
        }

        $mainConfig = $this->getConfiguration($configs, $container);

        $config = $this->processConfiguration($mainConfig, $configs);

        // load services
        $loader = new XmlFileLoader($container, new FileLocator(__DIR__.'/../Resources/config'));
        $loader->load('security.xml');
        $loader->load('security_listeners.xml');
        $loader->load('security_rememberme.xml');

        if ($this->authenticatorManagerEnabled = $config['enable_authenticator_manager']) {
            if ($config['always_authenticate_before_granting']) {
                throw new InvalidConfigurationException('The security option "always_authenticate_before_granting" cannot be used when "enable_authenticator_manager" is set to true. If you rely on this behavior, set it to false.');
            }

            $loader->load('security_authenticator.xml');

            // The authenticator system no longer has anonymous tokens. This makes sure AccessListener
            // and AuthorizationChecker do not throw AuthenticationCredentialsNotFoundException when no
            // token is available in the token storage.
            $container->getDefinition('security.access_listener')->setArgument(4, false);
            $container->getDefinition('security.authorization_checker')->setArgument(4, false);
            $container->getDefinition('security.authorization_checker')->setArgument(5, false);
        } else {
            $loader->load('security_legacy.xml');
        }

        if (class_exists(AbstractExtension::class)) {
            $loader->load('templating_twig.xml');
        }

        $loader->load('collectors.xml');
        $loader->load('guard.xml');

        if ($container->hasParameter('kernel.debug') && $container->getParameter('kernel.debug')) {
            $loader->load('security_debug.xml');
        }

        if (!class_exists(\Symfony\Component\ExpressionLanguage\ExpressionLanguage::class)) {
            $container->removeDefinition('security.expression_language');
            $container->removeDefinition('security.access.expression_voter');
        }

        // set some global scalars
        $container->setParameter('security.access.denied_url', $config['access_denied_url']);
        $container->setParameter('security.authentication.manager.erase_credentials', $config['erase_credentials']);
        $container->setParameter('security.authentication.session_strategy.strategy', $config['session_fixation_strategy']);

        if (isset($config['access_decision_manager']['service'])) {
            $container->setAlias('security.access.decision_manager', $config['access_decision_manager']['service'])->setPrivate(true);
        } else {
            $container
                ->getDefinition('security.access.decision_manager')
                ->addArgument($config['access_decision_manager']['strategy'])
                ->addArgument($config['access_decision_manager']['allow_if_all_abstain'])
                ->addArgument($config['access_decision_manager']['allow_if_equal_granted_denied']);
        }

        $container->setParameter('security.access.always_authenticate_before_granting', $config['always_authenticate_before_granting']);
        $container->setParameter('security.authentication.hide_user_not_found', $config['hide_user_not_found']);

        $this->createFirewalls($config, $container);
        $this->createAuthorization($config, $container);
        $this->createRoleHierarchy($config, $container);

        $container->getDefinition('security.authentication.guard_handler')
            ->replaceArgument(2, $this->statelessFirewallKeys);

        if ($config['encoders']) {
            $this->createEncoders($config['encoders'], $container);
        }

        if (class_exists(Application::class)) {
            $loader->load('console.xml');
            $container->getDefinition('security.command.user_password_encoder')->replaceArgument(1, array_keys($config['encoders']));
        }

        if (!class_exists(UserValueResolver::class)) {
            $container->getDefinition('security.user_value_resolver')->setClass(SecurityUserValueResolver::class);
        }

        $container->registerForAutoconfiguration(VoterInterface::class)
            ->addTag('security.voter');
    }

    private function createRoleHierarchy(array $config, ContainerBuilder $container)
    {
        if (!isset($config['role_hierarchy']) || 0 === \count($config['role_hierarchy'])) {
            $container->removeDefinition('security.access.role_hierarchy_voter');

            return;
        }

        $container->setParameter('security.role_hierarchy.roles', $config['role_hierarchy']);
        $container->removeDefinition('security.access.simple_role_voter');
    }

    private function createAuthorization(array $config, ContainerBuilder $container)
    {
        foreach ($config['access_control'] as $access) {
            $matcher = $this->createRequestMatcher(
                $container,
                $access['path'],
                $access['host'],
                $access['port'],
                $access['methods'],
                $access['ips']
            );

            $attributes = $access['roles'];
            if ($access['allow_if']) {
                $attributes[] = $this->createExpression($container, $access['allow_if']);
            }

            $container->getDefinition('security.access_map')
                      ->addMethodCall('add', [$matcher, $attributes, $access['requires_channel']]);
        }

        // allow cache warm-up for expressions
        if (\count($this->expressions)) {
            $container->getDefinition('security.cache_warmer.expression')
                ->replaceArgument(0, new IteratorArgument(array_values($this->expressions)));
        } else {
            $container->removeDefinition('security.cache_warmer.expression');
        }
    }

    private function createFirewalls(array $config, ContainerBuilder $container)
    {
        if (!isset($config['firewalls'])) {
            return;
        }

        $firewalls = $config['firewalls'];
        $providerIds = $this->createUserProviders($config, $container);

        $container->setParameter('security.firewalls', array_keys($firewalls));

        // make the ContextListener aware of the configured user providers
        $contextListenerDefinition = $container->getDefinition('security.context_listener');
        $arguments = $contextListenerDefinition->getArguments();
        $userProviders = [];
        foreach ($providerIds as $userProviderId) {
            $userProviders[] = new Reference($userProviderId);
        }
        $arguments[1] = $userProviderIteratorsArgument = new IteratorArgument($userProviders);
        $contextListenerDefinition->setArguments($arguments);

        if (\count($userProviders) > 1) {
            $container->setDefinition('security.user_providers', new Definition(ChainUserProvider::class, [$userProviderIteratorsArgument]))
                ->setPublic(false);
        } else {
            $container->setAlias('security.user_providers', new Alias(current($providerIds)))->setPublic(false);
        }

        if (1 === \count($providerIds)) {
            $container->setAlias(UserProviderInterface::class, current($providerIds));
        }

        $customUserChecker = false;

        // load firewall map
        $mapDef = $container->getDefinition('security.firewall.map');
        $map = $authenticationProviders = $contextRefs = [];
        foreach ($firewalls as $name => $firewall) {
            if (isset($firewall['user_checker']) && 'security.user_checker' !== $firewall['user_checker']) {
                $customUserChecker = true;
            }

            $configId = 'security.firewall.map.config.'.$name;

            [$matcher, $listeners, $exceptionListener, $logoutListener] = $this->createFirewall($container, $name, $firewall, $authenticationProviders, $providerIds, $configId);

            $contextId = 'security.firewall.map.context.'.$name;
            $isLazy = !$firewall['stateless'] && (!empty($firewall['anonymous']['lazy']) || $firewall['lazy']);
            $context = new ChildDefinition($isLazy ? 'security.firewall.lazy_context' : 'security.firewall.context');
            $context = $container->setDefinition($contextId, $context);
            $context
                ->replaceArgument(0, new IteratorArgument($listeners))
                ->replaceArgument(1, $exceptionListener)
                ->replaceArgument(2, $logoutListener)
                ->replaceArgument(3, new Reference($configId))
            ;

            $contextRefs[$contextId] = new Reference($contextId);
            $map[$contextId] = $matcher;
        }
        $mapDef->replaceArgument(0, ServiceLocatorTagPass::register($container, $contextRefs));
        $mapDef->replaceArgument(1, new IteratorArgument($map));

        if (!$this->authenticatorManagerEnabled) {
            // add authentication providers to authentication manager
            $authenticationProviders = array_map(function ($id) {
                return new Reference($id);
            }, array_values(array_unique($authenticationProviders)));

            $container
                ->getDefinition('security.authentication.manager')
                ->replaceArgument(0, new IteratorArgument($authenticationProviders));
        }

        // register an autowire alias for the UserCheckerInterface if no custom user checker service is configured
        if (!$customUserChecker) {
            $container->setAlias('Symfony\Component\Security\Core\User\UserCheckerInterface', new Alias('security.user_checker', false));
        }
    }

    private function createFirewall(ContainerBuilder $container, string $id, array $firewall, array &$authenticationProviders, array $providerIds, string $configId)
    {
        $config = $container->setDefinition($configId, new ChildDefinition('security.firewall.config'));
        $config->replaceArgument(0, $id);
        $config->replaceArgument(1, $firewall['user_checker']);

        // Matcher
        $matcher = null;
        if (isset($firewall['request_matcher'])) {
            $matcher = new Reference($firewall['request_matcher']);
        } elseif (isset($firewall['pattern']) || isset($firewall['host'])) {
            $pattern = $firewall['pattern'] ?? null;
            $host = $firewall['host'] ?? null;
            $methods = $firewall['methods'] ?? [];
            $matcher = $this->createRequestMatcher($container, $pattern, $host, null, $methods);
        }

        $config->replaceArgument(2, $matcher ? (string) $matcher : null);
        $config->replaceArgument(3, $firewall['security']);

        // Security disabled?
        if (false === $firewall['security']) {
            return [$matcher, [], null, null];
        }

        $config->replaceArgument(4, $firewall['stateless']);

        // Provider id (must be configured explicitly per firewall/authenticator if more than one provider is set)
        $defaultProvider = null;
        if (isset($firewall['provider'])) {
            if (!isset($providerIds[$normalizedName = str_replace('-', '_', $firewall['provider'])])) {
                throw new InvalidConfigurationException(sprintf('Invalid firewall "%s": user provider "%s" not found.', $id, $firewall['provider']));
            }
            $defaultProvider = $providerIds[$normalizedName];
        } elseif (1 === \count($providerIds)) {
            $defaultProvider = reset($providerIds);
        }

        $config->replaceArgument(5, $defaultProvider);

        // Register Firewall-specific event dispatcher
        $firewallEventDispatcherId = 'security.event_dispatcher.'.$id;
        $container->register($firewallEventDispatcherId, EventDispatcher::class);

        // Register listeners
        $listeners = [];
        $listenerKeys = [];

        // Channel listener
        $listeners[] = new Reference('security.channel_listener');

        $contextKey = null;
        $contextListenerId = null;
        // Context serializer listener
        if (false === $firewall['stateless']) {
            $contextKey = $firewall['context'] ?? $id;
            $listeners[] = new Reference($contextListenerId = $this->createContextListener($container, $contextKey));
            $sessionStrategyId = 'security.authentication.session_strategy';

            if ($this->authenticatorManagerEnabled) {
                $container
                    ->setDefinition('security.listener.session.'.$id, new ChildDefinition('security.listener.session'))
                    ->addTag('kernel.event_subscriber', ['dispatcher' => $firewallEventDispatcherId]);
            }
        } else {
            $this->statelessFirewallKeys[] = $id;
            $sessionStrategyId = 'security.authentication.session_strategy_noop';
        }
        $container->setAlias(new Alias('security.authentication.session_strategy.'.$id, false), $sessionStrategyId);

        $config->replaceArgument(6, $contextKey);

        // Logout listener
        $logoutListenerId = null;
        if (isset($firewall['logout'])) {
            $logoutListenerId = 'security.logout_listener.'.$id;
            $logoutListener = $container->setDefinition($logoutListenerId, new ChildDefinition('security.logout_listener'));
            $logoutListener->replaceArgument(2, new Reference($firewallEventDispatcherId));
            $logoutListener->replaceArgument(3, [
                'csrf_parameter' => $firewall['logout']['csrf_parameter'],
                'csrf_token_id' => $firewall['logout']['csrf_token_id'],
                'logout_path' => $firewall['logout']['path'],
            ]);

            // add default logout listener
            if (isset($firewall['logout']['success_handler'])) {
                // deprecated, to be removed in Symfony 6.0
                $logoutSuccessHandlerId = $firewall['logout']['success_handler'];
                $container->register('security.logout.listener.legacy_success_listener.'.$id, LegacyLogoutHandlerListener::class)
                    ->setArguments([new Reference($logoutSuccessHandlerId)])
                    ->addTag('kernel.event_subscriber', ['dispatcher' => $firewallEventDispatcherId]);
            } else {
                $logoutSuccessListenerId = 'security.logout.listener.default.'.$id;
                $container->setDefinition($logoutSuccessListenerId, new ChildDefinition('security.logout.listener.default'))
                    ->replaceArgument(1, $firewall['logout']['target'])
                    ->addTag('kernel.event_subscriber', ['dispatcher' => $firewallEventDispatcherId]);
            }

            // add CSRF provider
            if (isset($firewall['logout']['csrf_token_generator'])) {
                $logoutListener->addArgument(new Reference($firewall['logout']['csrf_token_generator']));
            }

            // add session logout listener
            if (true === $firewall['logout']['invalidate_session'] && false === $firewall['stateless']) {
                $container->setDefinition('security.logout.listener.session.'.$id, new ChildDefinition('security.logout.listener.session'))
                    ->addTag('kernel.event_subscriber', ['dispatcher' => $firewallEventDispatcherId]);
            }

            // add cookie logout listener
            if (\count($firewall['logout']['delete_cookies']) > 0) {
                $container->setDefinition('security.logout.listener.cookie_clearing.'.$id, new ChildDefinition('security.logout.listener.cookie_clearing'))
                    ->addArgument($firewall['logout']['delete_cookies'])
                    ->addTag('kernel.event_subscriber', ['dispatcher' => $firewallEventDispatcherId]);
            }

            // add custom listeners (deprecated)
            foreach ($firewall['logout']['handlers'] as $i => $handlerId) {
                $container->register('security.logout.listener.legacy_handler.'.$i, LegacyLogoutHandlerListener::class)
                    ->addArgument(new Reference($handlerId))
                    ->addTag('kernel.event_subscriber', ['dispatcher' => $firewallEventDispatcherId]);
            }

            // register with LogoutUrlGenerator
            $container
                ->getDefinition('security.logout_url_generator')
                ->addMethodCall('registerListener', [
                    $id,
                    $firewall['logout']['path'],
                    $firewall['logout']['csrf_token_id'],
                    $firewall['logout']['csrf_parameter'],
                    isset($firewall['logout']['csrf_token_generator']) ? new Reference($firewall['logout']['csrf_token_generator']) : null,
                    false === $firewall['stateless'] && isset($firewall['context']) ? $firewall['context'] : null,
                ])
            ;
        }

        // Determine default entry point
        $configuredEntryPoint = $firewall['entry_point'] ?? null;

        // Authentication listeners
        $firewallAuthenticationProviders = [];
        [$authListeners, $defaultEntryPoint] = $this->createAuthenticationListeners($container, $id, $firewall, $firewallAuthenticationProviders, $defaultProvider, $providerIds, $configuredEntryPoint, $contextListenerId);

        if (!$this->authenticatorManagerEnabled) {
            $authenticationProviders = array_merge($authenticationProviders, $firewallAuthenticationProviders);
        } else {
            // $configuredEntryPoint is resolved into a service ID and stored in $defaultEntryPoint
            $configuredEntryPoint = $defaultEntryPoint;

            // authenticator manager
            $authenticators = array_map(function ($id) {
                return new Reference($id);
            }, $firewallAuthenticationProviders);
            $container
                ->setDefinition($managerId = 'security.authenticator.manager.'.$id, new ChildDefinition('security.authenticator.manager'))
                ->replaceArgument(0, $authenticators)
                ->replaceArgument(2, new Reference($firewallEventDispatcherId))
                ->replaceArgument(3, $id)
                ->addTag('monolog.logger', ['channel' => 'security'])
            ;

            $managerLocator = $container->getDefinition('security.authenticator.managers_locator');
            $managerLocator->replaceArgument(0, array_merge($managerLocator->getArgument(0), [$id => new ServiceClosureArgument(new Reference($managerId))]));

            // authenticator manager listener
            $container
                ->setDefinition('security.firewall.authenticator.'.$id, new ChildDefinition('security.firewall.authenticator'))
                ->replaceArgument(0, new Reference($managerId))
            ;

            // user checker listener
            $container
                ->setDefinition('security.listener.user_checker.'.$id, new ChildDefinition('security.listener.user_checker'))
                ->replaceArgument(0, new Reference('security.user_checker.'.$id))
                ->addTag('kernel.event_subscriber', ['dispatcher' => $firewallEventDispatcherId]);

            $listeners[] = new Reference('security.firewall.authenticator.'.$id);
        }

        $config->replaceArgument(7, $configuredEntryPoint ?: $defaultEntryPoint);

        $listeners = array_merge($listeners, $authListeners);

        // Switch user listener
        if (isset($firewall['switch_user'])) {
            $listenerKeys[] = 'switch_user';
            $listeners[] = new Reference($this->createSwitchUserListener($container, $id, $firewall['switch_user'], $defaultProvider, $firewall['stateless']));
        }

        // Access listener
        $listeners[] = new Reference('security.access_listener');

        // Exception listener
        $exceptionListener = new Reference($this->createExceptionListener($container, $firewall, $id, $configuredEntryPoint ?: $defaultEntryPoint, $firewall['stateless']));

        $config->replaceArgument(8, $firewall['access_denied_handler'] ?? null);
        $config->replaceArgument(9, $firewall['access_denied_url'] ?? null);

        $container->setAlias('security.user_checker.'.$id, new Alias($firewall['user_checker'], false));

        foreach ($this->factories as $position) {
            foreach ($position as $factory) {
                $key = str_replace('-', '_', $factory->getKey());
                if (\array_key_exists($key, $firewall)) {
                    $listenerKeys[] = $key;
                }
            }
        }

        $config->replaceArgument(10, $listenerKeys);
        $config->replaceArgument(11, $firewall['switch_user'] ?? null);

        return [$matcher, $listeners, $exceptionListener, null !== $logoutListenerId ? new Reference($logoutListenerId) : null];
    }

    private function createContextListener(ContainerBuilder $container, string $contextKey)
    {
        if (isset($this->contextListeners[$contextKey])) {
            return $this->contextListeners[$contextKey];
        }

        $listenerId = 'security.context_listener.'.\count($this->contextListeners);
        $listener = $container->setDefinition($listenerId, new ChildDefinition('security.context_listener'));
        $listener->replaceArgument(2, $contextKey);

        return $this->contextListeners[$contextKey] = $listenerId;
    }

    private function createAuthenticationListeners(ContainerBuilder $container, string $id, array $firewall, array &$authenticationProviders, ?string $defaultProvider, array $providerIds, ?string $defaultEntryPoint, string $contextListenerId = null)
    {
        $listeners = [];
        $hasListeners = false;
        $entryPoints = [];

        foreach ($this->listenerPositions as $position) {
            foreach ($this->factories[$position] as $factory) {
                $key = str_replace('-', '_', $factory->getKey());

                if (isset($firewall[$key])) {
                    $userProvider = $this->getUserProvider($container, $id, $firewall, $key, $defaultProvider, $providerIds, $contextListenerId);

                    if ($this->authenticatorManagerEnabled) {
                        if (!$factory instanceof AuthenticatorFactoryInterface) {
                            throw new InvalidConfigurationException(sprintf('Cannot configure AuthenticatorManager as "%s" authentication does not support it, set "security.enable_authenticator_manager" to `false`.', $key));
                        }

                        $authenticators = $factory->createAuthenticator($container, $id, $firewall[$key], $userProvider);
                        if (\is_array($authenticators)) {
                            foreach ($authenticators as $i => $authenticator) {
                                $authenticationProviders[] = $authenticator;
                            }
                        } else {
                            $authenticationProviders[] = $authenticators;
                        }

                        if ($factory instanceof EntryPointFactoryInterface && ($entryPoint = $factory->registerEntryPoint($container, $id, $firewall[$key]))) {
                            $entryPoints[$key] = $entryPoint;
                        }
                    } else {
                        [$provider, $listenerId, $defaultEntryPoint] = $factory->create($container, $id, $firewall[$key], $userProvider, $defaultEntryPoint);

                        $listeners[] = new Reference($listenerId);
                        $authenticationProviders[] = $provider;
                    }
                    $hasListeners = true;
                }
            }
        }

        if ($entryPoints) {
            // we can be sure the authenticator system is enabled
            if (null !== $defaultEntryPoint) {
                $defaultEntryPoint = $entryPoints[$defaultEntryPoint] ?? $defaultEntryPoint;
            } elseif (1 === \count($entryPoints)) {
                $defaultEntryPoint = current($entryPoints);
            } else {
                throw new InvalidConfigurationException(sprintf('Because you have multiple authenticators in firewall "%s", you need to set the "entry_point" key to one of your authenticators (%s) or a service ID implementing "%s". The "entry_point" determines what should happen (e.g. redirect to "/login") when an anonymous user tries to access a protected page.', $id, implode(', ', $entryPoints), AuthenticationEntryPointInterface::class));
            }
        }

        if (false === $hasListeners && !$this->authenticatorManagerEnabled) {
            throw new InvalidConfigurationException(sprintf('No authentication listener registered for firewall "%s".', $id));
        }

        return [$listeners, $defaultEntryPoint];
    }

    private function getUserProvider(ContainerBuilder $container, string $id, array $firewall, string $factoryKey, ?string $defaultProvider, array $providerIds, ?string $contextListenerId): string
    {
        if (isset($firewall[$factoryKey]['provider'])) {
            if (!isset($providerIds[$normalizedName = str_replace('-', '_', $firewall[$factoryKey]['provider'])])) {
                throw new InvalidConfigurationException(sprintf('Invalid firewall "%s": user provider "%s" not found.', $id, $firewall[$factoryKey]['provider']));
            }

            return $providerIds[$normalizedName];
        }

        if ('remember_me' === $factoryKey && $contextListenerId) {
            $container->getDefinition($contextListenerId)->addTag('security.remember_me_aware', ['id' => $id, 'provider' => 'none']);
        }

        if ($defaultProvider) {
            return $defaultProvider;
        }

        if (!$providerIds) {
            $userProvider = sprintf('security.user.provider.missing.%s', $factoryKey);
            $container->setDefinition(
                $userProvider,
                (new ChildDefinition('security.user.provider.missing'))->replaceArgument(0, $id)
            );

            return $userProvider;
        }

        if ('remember_me' === $factoryKey || 'anonymous' === $factoryKey) {
            return 'security.user_providers';
        }

        throw new InvalidConfigurationException(sprintf('Not configuring explicitly the provider for the "%s" listener on "%s" firewall is ambiguous as there is more than one registered provider.', $factoryKey, $id));
    }

    private function createEncoders(array $encoders, ContainerBuilder $container)
    {
        $encoderMap = [];
        foreach ($encoders as $class => $encoder) {
            $encoderMap[$class] = $this->createEncoder($encoder);
        }

        $container
            ->getDefinition('security.encoder_factory.generic')
            ->setArguments([$encoderMap])
        ;
    }

    private function createEncoder(array $config)
    {
        // a custom encoder service
        if (isset($config['id'])) {
            return new Reference($config['id']);
        }

        if ($config['migrate_from'] ?? false) {
            return $config;
        }

        // plaintext encoder
        if ('plaintext' === $config['algorithm']) {
            $arguments = [$config['ignore_case']];

            return [
                'class' => 'Symfony\Component\Security\Core\Encoder\PlaintextPasswordEncoder',
                'arguments' => $arguments,
            ];
        }

        // pbkdf2 encoder
        if ('pbkdf2' === $config['algorithm']) {
            return [
                'class' => 'Symfony\Component\Security\Core\Encoder\Pbkdf2PasswordEncoder',
                'arguments' => [
                    $config['hash_algorithm'],
                    $config['encode_as_base64'],
                    $config['iterations'],
                    $config['key_length'],
                ],
            ];
        }

        // bcrypt encoder
        if ('bcrypt' === $config['algorithm']) {
            $config['algorithm'] = 'native';
            $config['native_algorithm'] = \PASSWORD_BCRYPT;

            return $this->createEncoder($config);
        }

        // Argon2i encoder
        if ('argon2i' === $config['algorithm']) {
            if (SodiumPasswordEncoder::isSupported() && !\defined('SODIUM_CRYPTO_PWHASH_ALG_ARGON2ID13')) {
                $config['algorithm'] = 'sodium';
            } elseif (\defined('PASSWORD_ARGON2I')) {
                $config['algorithm'] = 'native';
                $config['native_algorithm'] = \PASSWORD_ARGON2I;
            } else {
                throw new InvalidConfigurationException(sprintf('Algorithm "argon2i" is not available. Either use "%s" or upgrade to PHP 7.2+ instead.', \defined('SODIUM_CRYPTO_PWHASH_ALG_ARGON2ID13') ? 'argon2id", "auto' : 'auto'));
            }

            return $this->createEncoder($config);
        }

        if ('argon2id' === $config['algorithm']) {
            if (($hasSodium = SodiumPasswordEncoder::isSupported()) && \defined('SODIUM_CRYPTO_PWHASH_ALG_ARGON2ID13')) {
                $config['algorithm'] = 'sodium';
            } elseif (\defined('PASSWORD_ARGON2ID')) {
                $config['algorithm'] = 'native';
                $config['native_algorithm'] = \PASSWORD_ARGON2ID;
            } else {
                throw new InvalidConfigurationException(sprintf('Algorithm "argon2id" is not available. Either use "%s", upgrade to PHP 7.3+ or use libsodium 1.0.15+ instead.', \defined('PASSWORD_ARGON2I') || $hasSodium ? 'argon2i", "auto' : 'auto'));
            }

            return $this->createEncoder($config);
        }

        if ('native' === $config['algorithm']) {
            return [
                'class' => NativePasswordEncoder::class,
                'arguments' => [
                    $config['time_cost'],
                    (($config['memory_cost'] ?? 0) << 10) ?: null,
                    $config['cost'],
                ] + (isset($config['native_algorithm']) ? [3 => $config['native_algorithm']] : []),
            ];
        }

        if ('sodium' === $config['algorithm']) {
            if (!SodiumPasswordEncoder::isSupported()) {
                throw new InvalidConfigurationException('Libsodium is not available. Install the sodium extension or use "auto" instead.');
            }

            return [
                'class' => SodiumPasswordEncoder::class,
                'arguments' => [
                    $config['time_cost'],
                    (($config['memory_cost'] ?? 0) << 10) ?: null,
                ],
            ];
        }

        // run-time configured encoder
        return $config;
    }

    // Parses user providers and returns an array of their ids
    private function createUserProviders(array $config, ContainerBuilder $container): array
    {
        $providerIds = [];
        foreach ($config['providers'] as $name => $provider) {
            $id = $this->createUserDaoProvider($name, $provider, $container);
            $providerIds[str_replace('-', '_', $name)] = $id;
        }

        return $providerIds;
    }

    // Parses a <provider> tag and returns the id for the related user provider service
    private function createUserDaoProvider(string $name, array $provider, ContainerBuilder $container): string
    {
        $name = $this->getUserProviderId($name);

        // Doctrine Entity and In-memory DAO provider are managed by factories
        foreach ($this->userProviderFactories as $factory) {
            $key = str_replace('-', '_', $factory->getKey());

            if (!empty($provider[$key])) {
                $factory->create($container, $name, $provider[$key]);

                return $name;
            }
        }

        // Existing DAO service provider
        if (isset($provider['id'])) {
            $container->setAlias($name, new Alias($provider['id'], false));

            return $provider['id'];
        }

        // Chain provider
        if (isset($provider['chain'])) {
            $providers = [];
            foreach ($provider['chain']['providers'] as $providerName) {
                $providers[] = new Reference($this->getUserProviderId($providerName));
            }

            $container
                ->setDefinition($name, new ChildDefinition('security.user.provider.chain'))
                ->addArgument(new IteratorArgument($providers));

            return $name;
        }

        throw new InvalidConfigurationException(sprintf('Unable to create definition for "%s" user provider.', $name));
    }

    private function getUserProviderId(string $name): string
    {
        return 'security.user.provider.concrete.'.strtolower($name);
    }

    private function createExceptionListener(ContainerBuilder $container, array $config, string $id, ?string $defaultEntryPoint, bool $stateless): string
    {
        $exceptionListenerId = 'security.exception_listener.'.$id;
        $listener = $container->setDefinition($exceptionListenerId, new ChildDefinition('security.exception_listener'));
        $listener->replaceArgument(3, $id);
        $listener->replaceArgument(4, null === $defaultEntryPoint ? null : new Reference($defaultEntryPoint));
        $listener->replaceArgument(8, $stateless);

        // access denied handler setup
        if (isset($config['access_denied_handler'])) {
            $listener->replaceArgument(6, new Reference($config['access_denied_handler']));
        } elseif (isset($config['access_denied_url'])) {
            $listener->replaceArgument(5, $config['access_denied_url']);
        }

        return $exceptionListenerId;
    }

    private function createSwitchUserListener(ContainerBuilder $container, string $id, array $config, ?string $defaultProvider, bool $stateless): string
    {
        $userProvider = isset($config['provider']) ? $this->getUserProviderId($config['provider']) : $defaultProvider;

        if (!$userProvider) {
            throw new InvalidConfigurationException(sprintf('Not configuring explicitly the provider for the "switch_user" listener on "%s" firewall is ambiguous as there is more than one registered provider.', $id));
        }

        $switchUserListenerId = 'security.authentication.switchuser_listener.'.$id;
        $listener = $container->setDefinition($switchUserListenerId, new ChildDefinition('security.authentication.switchuser_listener'));
        $listener->replaceArgument(1, new Reference($userProvider));
        $listener->replaceArgument(2, new Reference('security.user_checker.'.$id));
        $listener->replaceArgument(3, $id);
        $listener->replaceArgument(6, $config['parameter']);
        $listener->replaceArgument(7, $config['role']);
        $listener->replaceArgument(9, $stateless);

        return $switchUserListenerId;
    }

    private function createExpression(ContainerBuilder $container, string $expression): Reference
    {
        if (isset($this->expressions[$id = '.security.expression.'.ContainerBuilder::hash($expression)])) {
            return $this->expressions[$id];
        }

        if (!class_exists(\Symfony\Component\ExpressionLanguage\ExpressionLanguage::class)) {
            throw new \RuntimeException('Unable to use expressions as the Symfony ExpressionLanguage component is not installed.');
        }

        $container
            ->register($id, 'Symfony\Component\ExpressionLanguage\Expression')
            ->setPublic(false)
            ->addArgument($expression)
        ;

        return $this->expressions[$id] = new Reference($id);
    }

    private function createRequestMatcher(ContainerBuilder $container, string $path = null, string $host = null, int $port = null, array $methods = [], array $ips = null, array $attributes = []): Reference
    {
        if ($methods) {
            $methods = array_map('strtoupper', (array) $methods);
        }

        if (null !== $ips) {
            foreach ($ips as $ip) {
                $container->resolveEnvPlaceholders($ip, null, $usedEnvs);

                if (!$usedEnvs && !$this->isValidIp($ip)) {
                    throw new \LogicException(sprintf('The given value "%s" in the "security.access_control" config option is not a valid IP address.', $ip));
                }

                $usedEnvs = null;
            }
        }

        $id = '.security.request_matcher.'.ContainerBuilder::hash([$path, $host, $port, $methods, $ips, $attributes]);

        if (isset($this->requestMatchers[$id])) {
            return $this->requestMatchers[$id];
        }

        // only add arguments that are necessary
        $arguments = [$path, $host, $methods, $ips, $attributes, null, $port];
        while (\count($arguments) > 0 && !end($arguments)) {
            array_pop($arguments);
        }

        $container
            ->register($id, 'Symfony\Component\HttpFoundation\RequestMatcher')
            ->setPublic(false)
            ->setArguments($arguments)
        ;

        return $this->requestMatchers[$id] = new Reference($id);
    }

    public function addSecurityListenerFactory(SecurityFactoryInterface $factory)
    {
        $this->factories[$factory->getPosition()][] = $factory;
    }

    public function addUserProviderFactory(UserProviderFactoryInterface $factory)
    {
        $this->userProviderFactories[] = $factory;
    }

    /**
     * {@inheritdoc}
     */
    public function getXsdValidationBasePath()
    {
        return __DIR__.'/../Resources/config/schema';
    }

    public function getNamespace()
    {
        return 'http://symfony.com/schema/dic/security';
    }

    public function getConfiguration(array $config, ContainerBuilder $container)
    {
        // first assemble the factories
        return new MainConfiguration($this->factories, $this->userProviderFactories);
    }

    private function isValidIp(string $cidr): bool
    {
        $cidrParts = explode('/', $cidr);

        if (1 === \count($cidrParts)) {
            return false !== filter_var($cidrParts[0], \FILTER_VALIDATE_IP);
        }

        $ip = $cidrParts[0];
        $netmask = $cidrParts[1];

        if (!ctype_digit($netmask)) {
            return false;
        }

        if (filter_var($ip, \FILTER_VALIDATE_IP, \FILTER_FLAG_IPV4)) {
            return $netmask <= 32;
        }

        if (filter_var($ip, \FILTER_VALIDATE_IP, \FILTER_FLAG_IPV6)) {
            return $netmask <= 128;
        }

        return false;
    }
}
