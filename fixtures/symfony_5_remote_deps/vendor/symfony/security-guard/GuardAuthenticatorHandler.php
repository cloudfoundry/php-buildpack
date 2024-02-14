<?php

/*
 * This file is part of the Symfony package.
 *
 * (c) Fabien Potencier <fabien@symfony.com>
 *
 * For the full copyright and license information, please view the LICENSE
 * file that was distributed with this source code.
 */

namespace Symfony\Component\Security\Guard;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Security\Core\Authentication\Token\Storage\TokenStorageInterface;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Exception\AuthenticationException;
use Symfony\Component\Security\Core\User\UserInterface;
use Symfony\Component\Security\Http\Event\InteractiveLoginEvent;
use Symfony\Component\Security\Http\SecurityEvents;
use Symfony\Component\Security\Http\Session\SessionAuthenticationStrategyInterface;
use Symfony\Contracts\EventDispatcher\EventDispatcherInterface;

/**
 * A utility class that does much of the *work* during the guard authentication process.
 *
 * By having the logic here instead of the listener, more of the process
 * can be called directly (e.g. for manual authentication) or overridden.
 *
 * @author Ryan Weaver <ryan@knpuniversity.com>
 *
 * @final
 */
class GuardAuthenticatorHandler
{
    private $tokenStorage;
    private $dispatcher;
    private $sessionStrategy;
    private $statelessProviderKeys;

    /**
     * @param array $statelessProviderKeys An array of provider/firewall keys that are "stateless" and so do not need the session migrated on success
     */
    public function __construct(TokenStorageInterface $tokenStorage, EventDispatcherInterface $eventDispatcher = null, array $statelessProviderKeys = [])
    {
        $this->tokenStorage = $tokenStorage;
        $this->dispatcher = $eventDispatcher;
        $this->statelessProviderKeys = $statelessProviderKeys;
    }

    /**
     * Authenticates the given token in the system.
     */
    public function authenticateWithToken(TokenInterface $token, Request $request, string $providerKey = null)
    {
        $this->migrateSession($request, $token, $providerKey);
        $this->tokenStorage->setToken($token);

        if (null !== $this->dispatcher) {
            $loginEvent = new InteractiveLoginEvent($request, $token);
            $this->dispatcher->dispatch($loginEvent, SecurityEvents::INTERACTIVE_LOGIN);
        }
    }

    /**
     * Returns the "on success" response for the given GuardAuthenticator.
     */
    public function handleAuthenticationSuccess(TokenInterface $token, Request $request, AuthenticatorInterface $guardAuthenticator, string $providerKey): ?Response
    {
        $response = $guardAuthenticator->onAuthenticationSuccess($request, $token, $providerKey);

        // check that it's a Response or null
        if ($response instanceof Response || null === $response) {
            return $response;
        }

        throw new \UnexpectedValueException(sprintf('The "%s::onAuthenticationSuccess()" method must return null or a Response object. You returned "%s".', \get_class($guardAuthenticator), get_debug_type($response)));
    }

    /**
     * Convenience method for authenticating the user and returning the
     * Response *if any* for success.
     */
    public function authenticateUserAndHandleSuccess(UserInterface $user, Request $request, AuthenticatorInterface $authenticator, string $providerKey): ?Response
    {
        // create an authenticated token for the User
        $token = $authenticator->createAuthenticatedToken($user, $providerKey);
        // authenticate this in the system
        $this->authenticateWithToken($token, $request, $providerKey);

        // return the success metric
        return $this->handleAuthenticationSuccess($token, $request, $authenticator, $providerKey);
    }

    /**
     * Handles an authentication failure and returns the Response for the
     * GuardAuthenticator.
     */
    public function handleAuthenticationFailure(AuthenticationException $authenticationException, Request $request, AuthenticatorInterface $guardAuthenticator, string $providerKey): ?Response
    {
        $response = $guardAuthenticator->onAuthenticationFailure($request, $authenticationException);
        if ($response instanceof Response || null === $response) {
            // returning null is ok, it means they want the request to continue
            return $response;
        }

        throw new \UnexpectedValueException(sprintf('The "%s::onAuthenticationFailure()" method must return null or a Response object. You returned "%s".', \get_class($guardAuthenticator), get_debug_type($response)));
    }

    /**
     * Call this method if your authentication token is stored to a session.
     *
     * @final
     */
    public function setSessionAuthenticationStrategy(SessionAuthenticationStrategyInterface $sessionStrategy)
    {
        $this->sessionStrategy = $sessionStrategy;
    }

    private function migrateSession(Request $request, TokenInterface $token, ?string $providerKey)
    {
        if (\in_array($providerKey, $this->statelessProviderKeys, true) || !$this->sessionStrategy || !$request->hasSession() || !$request->hasPreviousSession()) {
            return;
        }

        $this->sessionStrategy->onAuthentication($request, $token);
    }
}
