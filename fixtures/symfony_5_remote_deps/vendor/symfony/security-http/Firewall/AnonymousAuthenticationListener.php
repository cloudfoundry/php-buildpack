<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Security\Http\Firewall;

use Psr\Log\LoggerInterface;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\Security\Core\Authentication\AuthenticationManagerInterface;
use Symfony\Component\Security\Core\Authentication\Token\AnonymousToken;
use Symfony\Component\Security\Core\Authentication\Token\Storage\TokenStorageInterface;
use Symfony\Component\Security\Core\Exception\AuthenticationException;

// Help opcache.preload discover always-needed symbols
class_exists(AnonymousToken::class);

/**
 * AnonymousAuthenticationListener automatically adds a Token if none is
 * already present.
 *
 * @author Fabien Potencier <fabien@symfony.com>
 *
 * @final
 */
class AnonymousAuthenticationListener extends AbstractListener
{
    private $tokenStorage;
    private $secret;
    private $authenticationManager;
    private $logger;

    public function __construct(TokenStorageInterface $tokenStorage, string $secret, LoggerInterface $logger = null, AuthenticationManagerInterface $authenticationManager = null)
    {
        $this->tokenStorage = $tokenStorage;
        $this->secret = $secret;
        $this->authenticationManager = $authenticationManager;
        $this->logger = $logger;
    }

    /**
     * {@inheritdoc}
     */
    public function supports(Request $request): ?bool
    {
        return null; // always run authenticate() lazily with lazy firewalls
    }

    /**
     * Handles anonymous authentication.
     */
    public function authenticate(RequestEvent $event)
    {
        if (null !== $this->tokenStorage->getToken()) {
            return;
        }

        try {
            $token = new AnonymousToken($this->secret, 'anon.', []);
            if (null !== $this->authenticationManager) {
                $token = $this->authenticationManager->authenticate($token);
            }

            $this->tokenStorage->setToken($token);

            if (null !== $this->logger) {
                $this->logger->info('Populated the TokenStorage with an anonymous Token.');
            }
        } catch (AuthenticationException $failed) {
            if (null !== $this->logger) {
                $this->logger->info('Anonymous authentication failed.', ['exception' => $failed]);
            }
        }
    }
}
